from agent.main import monitor_once
from agent.recovery.manager import RecoveryManager


def test_monitor_once_memory_recovery(monkeypatch):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 20)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 95)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_process_info", lambda name: None)
    monkeypatch.setattr("agent.main.get_network_info", lambda interface: None)

    class FakeRecoveryManager:
        def __init__(self):
            self.calls = []

        def recover_and_verify(self, component, context=None, **kwargs):
            self.calls.append((component, kwargs))
            return {
                "component": component,
                "status": "recovered",
            }

    recovery_manager = FakeRecoveryManager()

    monitor_once(recovery_manager)

    assert recovery_manager.calls == [
        ("memory", {})
    ]


def test_monitor_once_continues_after_a_collector_failure(monkeypatch):
    def failed_cpu_collection():
        raise OSError("cpu collector unavailable")

    monkeypatch.setattr("agent.main.get_cpu_usage", failed_cpu_collection)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 95)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_process_info", lambda name: None)
    monkeypatch.setattr("agent.main.get_network_info", lambda interface: None)

    class FakeRecoveryManager:
        def __init__(self):
            self.calls = []

        def recover_and_verify(self, component, context=None, **kwargs):
            self.calls.append((component, kwargs))
            return {"component": component, "status": "recovered"}

    recovery_manager = FakeRecoveryManager()

    monitor_once(recovery_manager)

    assert recovery_manager.calls == [("memory", {})]


def test_monitor_once_cpu_recovery(monkeypatch):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 95)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_process_info", lambda name: None)
    monkeypatch.setattr("agent.main.get_network_info", lambda interface: None)

    class FakeRecoveryManager:
        def __init__(self):
            self.calls = []

        def recover_and_verify(self, component, context=None, **kwargs):
            self.calls.append((component, kwargs))
            return {"component": component, "status": "recovered"}

    recovery_manager = FakeRecoveryManager()

    monitor_once(recovery_manager)

    assert recovery_manager.calls == [("cpu", {})]


def test_monitor_once_disk_recovery(monkeypatch):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 20)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 95)
    monkeypatch.setattr("agent.main.get_process_info", lambda name: None)
    monkeypatch.setattr("agent.main.get_network_info", lambda interface: None)

    class FakeRecoveryManager:
        def __init__(self):
            self.calls = []

        def recover_and_verify(self, component, context=None, **kwargs):
            self.calls.append((component, kwargs))
            return {"component": component, "status": "recovery_unavailable"}

    recovery_manager = FakeRecoveryManager()

    monitor_once(recovery_manager)

    assert recovery_manager.calls == [("disk", {})]


def test_monitor_once_network_recovery_when_interface_is_down(monkeypatch):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 20)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_process_info", lambda name: None)
    monkeypatch.setattr(
        "agent.main.get_network_info",
        lambda interface: {
            "interface": interface,
            "is_up": False,
            "bytes_sent": 0,
            "bytes_recv": 0,
        },
    )

    class FakeRecoveryManager:
        def __init__(self):
            self.calls = []

        def recover_and_verify(self, component, context=None, **kwargs):
            self.calls.append((component, kwargs))
            return {"component": component, "status": "recovery_unavailable"}

    recovery_manager = FakeRecoveryManager()

    monitor_once(recovery_manager)

    assert recovery_manager.calls == [("network", {"interface": "Wi-Fi"})]


def test_monitor_once_process_recovery(monkeypatch):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 20)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr(
        "agent.main.get_process_info",
        lambda name: {
            "pid": 1234,
            "name": name,
            "cpu_percent": 95,
            "memory_percent": 20,
        },
    )
    monkeypatch.setattr("agent.main.get_network_info", lambda interface: None)

    class FakeRecoveryManager:
        def __init__(self):
            self.calls = []

        def recover_and_verify(self, component, context=None, **kwargs):
            self.calls.append((component, kwargs))
            return {
                "component": component,
                "status": "recovered",
            }

    recovery_manager = FakeRecoveryManager()

    monitor_once(recovery_manager)

    assert recovery_manager.calls == [
        ("process", {"pid": 1234})
    ]


def test_monitor_once_healthy_no_recovery(monkeypatch):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 20)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr(
        "agent.main.get_process_info",
        lambda name: {
            "pid": 1234,
            "name": name,
            "cpu_percent": 20,
            "memory_percent": 20,
        },
    )
    monkeypatch.setattr(
        "agent.main.get_network_info",
        lambda interface: {
            "interface": interface,
            "is_up": True,
            "bytes_sent": 100,
            "bytes_recv": 100,
        },
    )

    class FakeRecoveryManager:
        def __init__(self):
            self.calls = []

        def recover_and_verify(self, component, context=None, **kwargs):
            self.calls.append((component, kwargs))

    recovery_manager = FakeRecoveryManager()

    monitor_once(recovery_manager)

    assert recovery_manager.calls == []


def test_monitor_once_missing_process_no_recovery(monkeypatch):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 20)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_process_info", lambda name: None)
    monkeypatch.setattr(
        "agent.main.get_network_info",
        lambda interface: {
            "interface": interface,
            "is_up": True,
            "bytes_sent": 100,
            "bytes_recv": 100,
        },
    )

    class FakeRecoveryManager:
        def __init__(self):
            self.calls = []

        def recover_and_verify(self, component, context=None, **kwargs):
            self.calls.append((component, kwargs))

    recovery_manager = FakeRecoveryManager()

    monitor_once(recovery_manager)

    assert recovery_manager.calls == []


def test_monitor_once_missing_network_does_not_attempt_recovery(monkeypatch):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 20)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_process_info", lambda name: None)
    monkeypatch.setattr("agent.main.get_network_info", lambda interface: None)

    class FakeRecoveryManager:
        def __init__(self):
            self.calls = []

        def recover_and_verify(self, component, context=None, **kwargs):
            self.calls.append((component, kwargs))

    recovery_manager = FakeRecoveryManager()

    monitor_once(recovery_manager)

    assert recovery_manager.calls == []


def test_monitor_once_reports_cooldown_without_executing_action(monkeypatch, capsys):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 95)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_process_info", lambda name: None)
    monkeypatch.setattr("agent.main.get_network_info", lambda interface: None)

    manager = RecoveryManager(clock=lambda: 10)
    manager._get_state("cpu")["cooldown_until"] = 20
    action_calls = []
    monkeypatch.setattr(
        manager,
        "recover",
        lambda component, **kwargs: action_calls.append(component),
    )

    monitor_once(manager)

    assert action_calls == []
    assert "cooldown_active" in capsys.readouterr().out


def test_monitor_once_process_passes_pid_in_verification_context(monkeypatch):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 20)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr(
        "agent.main.get_process_info",
        lambda name: {
            "pid": 1234,
            "name": name,
            "cpu_percent": 95,
            "memory_percent": 20,
        },
    )
    monkeypatch.setattr("agent.main.get_network_info", lambda interface: None)

    calls = []

    class FakeManager:
        def recover_and_verify(self, component, context=None, **kwargs):
            calls.append((component, context, kwargs))
            return {"status": "recovered"}

    monitor_once(FakeManager())

    assert len(calls) == 1
    component, context, kwargs = calls[0]
    assert component == "process"
    assert context["target_pid"] == 1234
    assert context["process_name"] == "python.exe"
    assert kwargs["pid"] == 1234


def test_monitor_once_missing_process_requests_restart_when_configured(monkeypatch):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 20)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_process_info", lambda name: None)
    monkeypatch.setattr(
        "agent.main.get_network_info",
        lambda interface: {
            "interface": interface,
            "is_up": True,
            "bytes_sent": 100,
            "bytes_recv": 100,
        },
    )

    calls = []

    class RestartableManager:
        def can_restart_process(self):
            return True

        def recover_and_verify(self, component, context=None, **kwargs):
            calls.append((component, context, kwargs))
            return {"status": "recovered"}

    monitor_once(RestartableManager())

    assert len(calls) == 1
    component, context, kwargs = calls[0]
    assert component == "process"
    assert context["process_name"] == "python.exe"
    assert kwargs["action"] == "start"
    assert kwargs["process_name"] == "python.exe"


def test_monitor_once_missing_process_safely_unattempted_when_not_configured(monkeypatch):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 20)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_process_info", lambda name: None)
    monkeypatch.setattr(
        "agent.main.get_network_info",
        lambda interface: {
            "interface": interface,
            "is_up": True,
            "bytes_sent": 100,
            "bytes_recv": 100,
        },
    )

    calls = []

    class NonRestartableManager:
        def can_restart_process(self):
            return False

        def recover_and_verify(self, component, context=None, **kwargs):
            calls.append((component, context, kwargs))

    monitor_once(NonRestartableManager())

    assert calls == []
