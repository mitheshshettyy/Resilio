import pytest

from agent.recovery.disk import DiskRecovery


def test_disk_recovery_not_required(monkeypatch):
    monkeypatch.setattr("agent.recovery.disk.get_disk_usage", lambda: 70)

    result = DiskRecovery(threshold=90).recover()

    assert result == {
        "component": "disk",
        "status": "not_required",
        "before": 70,
        "after": 70,
    }


def test_disk_recovery_is_unavailable_without_managed_cleanup(monkeypatch):
    monkeypatch.setattr("agent.recovery.disk.get_disk_usage", lambda: 95)

    result = DiskRecovery(threshold=90).recover()

    assert result["status"] == "recovery_unavailable"
    assert result["before"] == result["after"] == 95


def test_disk_recovery_runs_managed_cleanup_and_verifies(monkeypatch):
    usages = iter([95, 70])
    cleanup_calls = []
    monkeypatch.setattr("agent.recovery.disk.get_disk_usage", lambda: next(usages))

    result = DiskRecovery(
        threshold=90,
        cleanup=lambda: cleanup_calls.append(True) is None,
    ).recover()

    assert cleanup_calls == [True]
    assert result == {
        "component": "disk",
        "status": "recovered",
        "before": 95,
        "after": 70,
    }


def test_disk_recovery_reports_failed_cleanup(monkeypatch):
    usages = iter([95, 95])
    monkeypatch.setattr("agent.recovery.disk.get_disk_usage", lambda: next(usages))

    result = DiskRecovery(threshold=90, cleanup=lambda: False).recover()

    assert result["status"] == "recovery_failed"
    assert result["before"] == result["after"] == 95


def test_disk_recovery_handles_cleanup_permission_error(monkeypatch):
    monkeypatch.setattr("agent.recovery.disk.get_disk_usage", lambda: 95)

    def denied_cleanup():
        raise PermissionError("denied")

    result = DiskRecovery(threshold=90, cleanup=denied_cleanup).recover()

    assert result["status"] == "recovery_failed"
    assert result["reason"] == "denied"


def test_disk_recovery_handles_cleanup_runtime_error(monkeypatch):
    monkeypatch.setattr("agent.recovery.disk.get_disk_usage", lambda: 95)

    def failing_cleanup():
        raise RuntimeError("cleanup script crashed")

    result = DiskRecovery(threshold=90, cleanup=failing_cleanup).recover()

    assert result["status"] == "recovery_failed"
    assert result["reason"] == "cleanup script crashed"
    assert result["before"] == 95
    assert result["after"] == 95


def test_disk_recovery_handles_unexpected_exception(monkeypatch):
    monkeypatch.setattr("agent.recovery.disk.get_disk_usage", lambda: 95)

    def failing_cleanup():
        raise ValueError("invalid cleanup path configuration")

    result = DiskRecovery(threshold=90, cleanup=failing_cleanup).recover()

    assert result["status"] == "recovery_failed"
    assert result["reason"] == "invalid cleanup path configuration"
    assert result["before"] == 95
    assert result["after"] == 95


def test_disk_recovery_propagates_base_exception(monkeypatch):
    monkeypatch.setattr("agent.recovery.disk.get_disk_usage", lambda: 95)

    def fatal_cleanup():
        raise KeyboardInterrupt()

    recovery = DiskRecovery(threshold=90, cleanup=fatal_cleanup)
    with pytest.raises(KeyboardInterrupt):
        recovery.recover()
