from agent.recovery.manager import RecoveryManager


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


def test_manager_unknown_component():

    manager = RecoveryManager()

    result = manager.recover("disk")

    assert result["component"] == "disk"
    assert result["status"] == "not_implemented"