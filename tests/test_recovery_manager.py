from agent.recovery.manager import RecoveryManager


class FakeVerifier:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def verify(self, component, context):
        self.calls.append((component, context))
        return self.result


def test_manager_memory_recovery(monkeypatch):

    monkeypatch.setattr(
        "agent.recovery.memory.get_memory_usage",
        lambda: 60
    )

    manager = RecoveryManager()

    result = manager.recover("memory")

    assert result["component"] == "memory"
    assert result["status"] == "not_required"


def test_manager_process_recovery(monkeypatch):

    monkeypatch.setattr(
        "agent.recovery.process.ProcessRecovery.recover",
        lambda self, pid: {
            "component": "process",
            "status": "recovered",
            "pid": pid,
        }
    )

    manager = RecoveryManager()

    result = manager.recover("process", pid=1234)

    assert result["component"] == "process"
    assert result["status"] == "recovered"
    assert result["pid"] == 1234


def test_manager_process_recovery_requires_pid():
    result = RecoveryManager().recover("process")

    assert result == {"component": "process", "status": "invalid_arguments"}


def test_manager_unknown_component():

    manager = RecoveryManager()

    result = manager.recover("unknown")

    assert result["component"] == "unknown"
    assert result["status"] == "not_implemented"


def test_manager_cpu_recovery(monkeypatch):
    monkeypatch.setattr(
        "agent.recovery.cpu.CpuRecovery.recover",
        lambda self: {"component": "cpu", "status": "recovered"},
    )

    result = RecoveryManager().recover("cpu")

    assert result == {"component": "cpu", "status": "recovered"}


def test_manager_disk_recovery(monkeypatch):
    monkeypatch.setattr(
        "agent.recovery.disk.DiskRecovery.recover",
        lambda self: {"component": "disk", "status": "recovery_unavailable"},
    )

    result = RecoveryManager().recover("disk")

    assert result == {"component": "disk", "status": "recovery_unavailable"}


def test_manager_network_recovery(monkeypatch):
    monkeypatch.setattr(
        "agent.recovery.network.NetworkRecovery.recover",
        lambda self, interface: {
            "component": "network",
            "status": "recovered",
            "interface": interface,
        },
    )

    result = RecoveryManager().recover("network", interface="Wi-Fi")

    assert result["status"] == "recovered"


def test_manager_network_recovery_requires_interface():
    result = RecoveryManager().recover("network")

    assert result == {"component": "network", "status": "invalid_arguments"}


def test_manager_records_successful_action_and_verification(monkeypatch):
    verifier = FakeVerifier(
        {
            "component": "cpu",
            "verification_status": "verified",
            "health_status": "WARNING",
            "measurement": 85,
        }
    )
    manager = RecoveryManager(verifier=verifier)
    monkeypatch.setattr(
        manager, "recover", lambda component, **kwargs: {"status": "recovered"}
    )

    result = manager.recover_and_verify("cpu")

    assert result["action_status"] == "recovered"
    assert result["verification_status"] == "verified"
    assert result["health_status"] == "WARNING"
    assert result["attempt_number"] == 0


def test_manager_records_failed_verification_and_allows_retry(monkeypatch):
    verifier = FakeVerifier(
        {
            "component": "cpu",
            "verification_status": "not_verified",
            "health_status": "CRITICAL",
            "measurement": 95,
        }
    )
    manager = RecoveryManager(verifier=verifier)
    monkeypatch.setattr(
        manager, "recover", lambda component, **kwargs: {"status": "recovered"}
    )

    result = manager.recover_and_verify("cpu")

    assert result["verification_status"] == "not_verified"
    assert result["attempt_number"] == 1
    assert result["retry_remaining"] == 1


def test_manager_records_action_failure_without_verification(monkeypatch):
    verifier = FakeVerifier({"verification_status": "verified"})
    manager = RecoveryManager(verifier=verifier)
    monkeypatch.setattr(
        manager,
        "recover",
        lambda component, **kwargs: {"status": "access_denied"},
    )

    result = manager.recover_and_verify("cpu")

    assert result["action_status"] == "access_denied"
    assert result["verification_status"] == "not_attempted"
    assert result["attempt_number"] == 1
    assert verifier.calls == []


def test_manager_marks_unavailable_network_recovery_unverifiable(monkeypatch):
    manager = RecoveryManager(verifier=FakeVerifier({"verification_status": "verified"}))
    monkeypatch.setattr(
        manager,
        "recover",
        lambda component, **kwargs: {"status": "recovery_unavailable"},
    )

    result = manager.recover_and_verify("network", {"interface": "Wi-Fi"})

    assert result["action_status"] == "recovery_unavailable"
    assert result["verification_status"] == "unverifiable"


def test_manager_enters_cooldown_then_allows_recovery_after_expiry(monkeypatch):
    now = [100]
    verifier = FakeVerifier(
        {
            "component": "cpu",
            "verification_status": "not_verified",
            "health_status": "CRITICAL",
        }
    )
    manager = RecoveryManager(clock=lambda: now[0], verifier=verifier)
    calls = []
    monkeypatch.setattr(
        manager,
        "recover",
        lambda component, **kwargs: calls.append(component) or {"status": "recovered"},
    )

    manager.recover_and_verify("cpu")
    manager.recover_and_verify("cpu")
    cooldown = manager.recover_and_verify("cpu")

    assert cooldown["reason"] == "cooldown_active"
    assert cooldown["cooldown_until"] == 160
    assert calls == ["cpu", "cpu"]

    now[0] = 160
    result = manager.recover_and_verify("cpu")

    assert calls == ["cpu", "cpu", "cpu"]
    assert result["attempt_number"] == 1


def test_manager_success_resets_component_state(monkeypatch):
    verifier = FakeVerifier(
        {
            "component": "memory",
            "verification_status": "verified",
            "health_status": "HEALTHY",
        }
    )
    manager = RecoveryManager(verifier=verifier)
    manager._get_state("memory")["attempt_count"] = 1
    monkeypatch.setattr(
        manager, "recover", lambda component, **kwargs: {"status": "recovered"}
    )

    result = manager.recover_and_verify("memory")

    assert result["attempt_number"] == 0
    assert result["retry_remaining"] == manager.MAX_RECOVERY_ATTEMPTS


def test_manager_maintains_independent_component_state(monkeypatch):
    verifier = FakeVerifier(
        {
            "verification_status": "not_verified",
            "health_status": "CRITICAL",
        }
    )
    manager = RecoveryManager(verifier=verifier)
    monkeypatch.setattr(
        manager, "recover", lambda component, **kwargs: {"status": "recovered"}
    )

    manager.recover_and_verify("cpu")
    memory_result = manager.recover_and_verify("memory")

    assert manager._get_state("cpu")["attempt_count"] == 1
    assert memory_result["attempt_number"] == 1
