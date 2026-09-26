from agent.main import monitor_once


def test_monitor_once_memory_recovery(monkeypatch):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 20)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 95)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_process_info", lambda name: None)
    monkeypatch.setattr("agent.main.get_network_info", lambda interface: None)

    class FakeRecoveryManager:
        def __init__(self):
            self.calls = []

        def recover(self, component, **kwargs):
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


def test_monitor_once_cpu_recovery(monkeypatch):
    monkeypatch.setattr("agent.main.get_cpu_usage", lambda: 95)
    monkeypatch.setattr("agent.main.get_memory_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_disk_usage", lambda: 40)
    monkeypatch.setattr("agent.main.get_process_info", lambda name: None)
    monkeypatch.setattr("agent.main.get_network_info", lambda interface: None)

    class FakeRecoveryManager:
        def __init__(self):
            self.calls = []

        def recover(self, component, **kwargs):
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

        def recover(self, component, **kwargs):
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

        def recover(self, component, **kwargs):
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

        def recover(self, component, **kwargs):
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

        def recover(self, component, **kwargs):
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

        def recover(self, component, **kwargs):
            self.calls.append((component, kwargs))

    recovery_manager = FakeRecoveryManager()

    monitor_once(recovery_manager)

    assert recovery_manager.calls == []
