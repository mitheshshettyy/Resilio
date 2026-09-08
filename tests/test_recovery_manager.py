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