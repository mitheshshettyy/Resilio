from agent.recovery.memory import MemoryRecovery
from agent.config import MEMORY_CRITICAL_THRESHOLD


def test_memory_recovery_not_required(monkeypatch):

    monkeypatch.setattr(
        "agent.recovery.memory.get_memory_usage",
        lambda: 60
    )

    recovery = MemoryRecovery(threshold=85)

    result = recovery.recover()

    assert result["component"] == "memory"
    assert result["status"] == "not_required"
    assert result["before"] == 60
    assert result["after"] == 60


def test_memory_recovery_success(monkeypatch):

    memory_values = iter([95, 70])

    monkeypatch.setattr(
        "agent.recovery.memory.get_memory_usage",
        lambda: next(memory_values)
    )

    recovery = MemoryRecovery(threshold=85)

    result = recovery.recover()

    assert result["component"] == "memory"
    assert result["status"] == "recovered"
    assert result["before"] == 95
    assert result["after"] == 70


def test_memory_recovery_failed(monkeypatch):

    memory_values = iter([95, 96])

    monkeypatch.setattr(
        "agent.recovery.memory.get_memory_usage",
        lambda: next(memory_values)
    )

    recovery = MemoryRecovery(threshold=85)

    result = recovery.recover()

    assert result["component"] == "memory"
    assert result["status"] == "recovery_failed"
    assert result["before"] == 95
    assert result["after"] == 96


def test_memory_recovery_uses_configured_critical_threshold(monkeypatch):
    monkeypatch.setattr(
        "agent.recovery.memory.get_memory_usage",
        lambda: MEMORY_CRITICAL_THRESHOLD - 1,
    )

    result = MemoryRecovery().recover()

    assert result["status"] == "not_required"
