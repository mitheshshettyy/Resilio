from agent.recovery.cpu import CpuRecovery


def test_cpu_recovery_not_required(monkeypatch):
    monkeypatch.setattr("agent.recovery.cpu.get_cpu_usage", lambda: 70)

    result = CpuRecovery(threshold=90).recover()

    assert result == {
        "component": "cpu",
        "status": "not_required",
        "before": 70,
        "after": 70,
    }


def test_cpu_recovery_uses_safe_high_cpu_candidate(monkeypatch):
    usages = iter([95, 60])
    recovery = CpuRecovery(threshold=90, process_threshold=80)
    monkeypatch.setattr("agent.recovery.cpu.get_cpu_usage", lambda: next(usages))
    monkeypatch.setattr(
        recovery,
        "get_cpu_processes",
        lambda: [
            {"pid": 10, "name": "lsass.exe", "cpu_percent": 99},
            {"pid": 20, "name": "worker.exe", "cpu_percent": 90},
        ],
    )
    monkeypatch.setattr(
        "agent.recovery.cpu.ProcessRecovery.recover",
        lambda self, pid: {"pid": pid, "status": "recovered"},
    )

    result = recovery.recover()

    assert result == {
        "component": "cpu",
        "status": "recovered",
        "before": 95,
        "after": 60,
        "pid": 20,
    }


def test_cpu_recovery_returns_no_safe_candidate(monkeypatch):
    recovery = CpuRecovery(threshold=90, process_threshold=80)
    monkeypatch.setattr("agent.recovery.cpu.get_cpu_usage", lambda: 95)
    monkeypatch.setattr(
        recovery,
        "get_cpu_processes",
        lambda: [{"pid": 10, "name": "lsass.exe", "cpu_percent": 99}],
    )

    result = recovery.recover()

    assert result["status"] == "no_safe_candidate"


def test_cpu_recovery_verifies_process_result_and_cpu_usage(monkeypatch):
    usages = iter([95, 96])
    recovery = CpuRecovery(threshold=90, process_threshold=80)
    monkeypatch.setattr("agent.recovery.cpu.get_cpu_usage", lambda: next(usages))
    monkeypatch.setattr(
        recovery,
        "get_cpu_processes",
        lambda: [{"pid": 20, "name": "worker.exe", "cpu_percent": 90}],
    )
    monkeypatch.setattr(
        "agent.recovery.cpu.ProcessRecovery.recover",
        lambda self, pid: {"pid": pid, "status": "not_found"},
    )

    result = recovery.recover()

    assert result["status"] == "recovery_failed"
    assert result["reason"] == "not_found"
