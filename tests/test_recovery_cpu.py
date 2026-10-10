from unittest.mock import patch, MagicMock

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


class MockProcess:
    """Mock psutil.Process for deterministic CPU sampling tests."""

    def __init__(self, pid, name, cpu_readings=None, raise_on_call=None):
        self.pid = pid
        self._name = name
        self.info = {"pid": pid, "name": name}
        self._readings = iter(cpu_readings) if cpu_readings is not None else None
        self._raise_on_call = raise_on_call or {}
        self._calls = 0

    def cpu_percent(self, interval=None):
        self._calls += 1
        if self._calls in self._raise_on_call:
            raise self._raise_on_call[self._calls]
        if self._readings is not None:
            return next(self._readings)
        return 0.0

    def name(self):
        return self._name


def test_get_cpu_processes_primes_then_reads_meaningful_cpu(monkeypatch):
    """Initial call returns 0.0; second call returns real usage after interval."""
    import psutil

    proc_a = MockProcess(101, "heavy_app.exe", [0.0, 88.5])
    proc_b = MockProcess(102, "light_app.exe", [0.0, 12.0])

    monkeypatch.setattr(
        "agent.recovery.cpu.ProcessRecovery.iter_processes",
        lambda attrs: [proc_a, proc_b],
    )

    sleep_calls = []
    recovery = CpuRecovery(
        sample_interval=0.05,
        sleep_func=lambda s: sleep_calls.append(s),
    )

    results = recovery.get_cpu_processes()

    assert sleep_calls == [0.05]
    assert proc_a._calls == 2
    assert proc_b._calls == 2
    assert results == [
        {"pid": 101, "name": "heavy_app.exe", "cpu_percent": 88.5},
        {"pid": 102, "name": "light_app.exe", "cpu_percent": 12.0},
    ]


def test_get_cpu_processes_handles_process_disappearance(monkeypatch):
    """A process that terminates between sample passes is safely ignored."""
    import psutil

    # proc_a disappears on pass 2
    proc_a = MockProcess(
        201,
        "ephemeral.exe",
        [0.0],
        raise_on_call={2: psutil.NoSuchProcess(201)},
    )
    proc_b = MockProcess(202, "stable.exe", [0.0, 75.0])

    monkeypatch.setattr(
        "agent.recovery.cpu.ProcessRecovery.iter_processes",
        lambda attrs: [proc_a, proc_b],
    )

    recovery = CpuRecovery(sample_interval=0.0, sleep_func=lambda s: None)
    results = recovery.get_cpu_processes()

    assert len(results) == 1
    assert results[0] == {"pid": 202, "name": "stable.exe", "cpu_percent": 75.0}


def test_get_cpu_processes_handles_permission_errors(monkeypatch):
    """Processes raising AccessDenied on either pass are safely ignored."""
    import psutil

    # proc_a denies access on pass 1
    proc_a = MockProcess(
        301,
        "protected_svc.exe",
        raise_on_call={1: psutil.AccessDenied(301)},
    )
    # proc_b denies access on pass 2
    proc_b = MockProcess(
        302,
        "restricted.exe",
        [0.0],
        raise_on_call={2: psutil.AccessDenied(302)},
    )
    # proc_c succeeds
    proc_c = MockProcess(303, "user_tool.exe", [0.0, 65.0])

    monkeypatch.setattr(
        "agent.recovery.cpu.ProcessRecovery.iter_processes",
        lambda attrs: [proc_a, proc_b, proc_c],
    )

    recovery = CpuRecovery(sample_interval=0.0, sleep_func=lambda s: None)
    results = recovery.get_cpu_processes()

    assert len(results) == 1
    assert results[0] == {"pid": 303, "name": "user_tool.exe", "cpu_percent": 65.0}


def test_cpu_recovery_ignores_initial_zero_readings_avoids_false_candidate(monkeypatch):
    """Uninitialized / 0.0 readings do not qualify for recovery termination."""
    proc = MockProcess(401, "idle_worker.exe", [0.0, 0.0])

    monkeypatch.setattr(
        "agent.recovery.cpu.ProcessRecovery.iter_processes",
        lambda attrs: [proc],
    )
    monkeypatch.setattr("agent.recovery.cpu.get_cpu_usage", lambda: 95.0)

    recovered_pids = []
    monkeypatch.setattr(
        "agent.recovery.cpu.ProcessRecovery.recover",
        lambda self, pid: recovered_pids.append(pid),
    )

    recovery = CpuRecovery(
        threshold=90,
        process_threshold=80,
        sample_interval=0.0,
        sleep_func=lambda s: None,
    )
    result = recovery.recover()

    assert result["status"] == "no_safe_candidate"
    assert recovered_pids == []


def test_cpu_recovery_protects_system_and_self_processes(monkeypatch):
    """Critical system processes and the agent itself are excluded from candidate selection."""
    import os

    proc_system = MockProcess(4, "system", [0.0, 95.0])
    proc_csrss = MockProcess(10, "csrss.exe", [0.0, 92.0])
    proc_self = MockProcess(os.getpid(), "python.exe", [0.0, 91.0])

    monkeypatch.setattr(
        "agent.recovery.cpu.ProcessRecovery.iter_processes",
        lambda attrs: [proc_system, proc_csrss, proc_self],
    )
    monkeypatch.setattr("agent.recovery.cpu.get_cpu_usage", lambda: 95.0)

    recovery = CpuRecovery(
        threshold=90,
        process_threshold=80,
        sample_interval=0.0,
        sleep_func=lambda s: None,
    )
    result = recovery.recover()

    assert result["status"] == "no_safe_candidate"


def test_get_cpu_processes_empty_list_does_not_sleep(monkeypatch):
    """If no processes are returned, sampling does not block."""
    monkeypatch.setattr(
        "agent.recovery.cpu.ProcessRecovery.iter_processes",
        lambda attrs: [],
    )

    sleep_called = False

    def fake_sleep(s):
        nonlocal sleep_called
        sleep_called = True

    recovery = CpuRecovery(sample_interval=0.1, sleep_func=fake_sleep)
    results = recovery.get_cpu_processes()

    assert results == []
    assert not sleep_called


def test_get_cpu_processes_skips_none_cpu_and_missing_metadata(monkeypatch):
    """Handles None cpu_percent or missing name/pid safely."""
    proc_none_cpu = MockProcess(501, "valid_name.exe", [0.0, None])
    proc_missing_name = MockProcess(502, None, [0.0, 50.0])
    proc_valid = MockProcess(503, "good.exe", [0.0, 70.0])

    monkeypatch.setattr(
        "agent.recovery.cpu.ProcessRecovery.iter_processes",
        lambda attrs: [proc_none_cpu, proc_missing_name, proc_valid],
    )

    recovery = CpuRecovery(sample_interval=0.0, sleep_func=lambda s: None)
    results = recovery.get_cpu_processes()

    assert len(results) == 1
    assert results[0] == {"pid": 503, "name": "good.exe", "cpu_percent": 70.0}


def test_get_cpu_processes_records_create_time_when_available(monkeypatch):
    """Processes with create_time metadata include it in the returned dictionary."""
    proc = MockProcess(601, "timed_proc.exe", [0.0, 85.0])
    proc.info["create_time"] = 1600000000.0

    monkeypatch.setattr(
        "agent.recovery.cpu.ProcessRecovery.iter_processes",
        lambda attrs: [proc],
    )

    recovery = CpuRecovery(sample_interval=0.0, sleep_func=lambda s: None)
    results = recovery.get_cpu_processes()

    assert len(results) == 1
    assert results[0] == {
        "pid": 601,
        "name": "timed_proc.exe",
        "cpu_percent": 85.0,
        "create_time": 1600000000.0,
    }


def test_cpu_recovery_prevents_terminating_reused_pid(monkeypatch):
    """When a PID is reused by another process before termination, recovery aborts safely."""
    usages = iter([95, 95])
    recovery = CpuRecovery(threshold=90, process_threshold=80)
    monkeypatch.setattr("agent.recovery.cpu.get_cpu_usage", lambda: next(usages))
    monkeypatch.setattr(
        recovery,
        "get_cpu_processes",
        lambda: [
            {
                "pid": 20,
                "name": "worker.exe",
                "cpu_percent": 90,
                "create_time": 100.0,
            }
        ],
    )

    with patch("agent.recovery.process.psutil.Process") as mock_psutil_proc:
        # Replacement process has inherited PID 20 but has different create_time
        reused_process = mock_psutil_proc.return_value
        reused_process.name.return_value = "worker.exe"
        reused_process.create_time.return_value = 200.0

        result = recovery.recover()

        # The replacement process must NEVER be terminated
        reused_process.terminate.assert_not_called()
        assert result["status"] == "recovery_failed"
        assert result["reason"] == "identity_mismatch"
        assert result["pid"] == 20


def test_cpu_recovery_terminates_process_when_identity_verified(monkeypatch):
    """When PID, name, and create_time all match, recovery proceeds to terminate."""
    usages = iter([95, 40])
    recovery = CpuRecovery(threshold=90, process_threshold=80)
    monkeypatch.setattr("agent.recovery.cpu.get_cpu_usage", lambda: next(usages))
    monkeypatch.setattr(
        recovery,
        "get_cpu_processes",
        lambda: [
            {
                "pid": 20,
                "name": "worker.exe",
                "cpu_percent": 90,
                "create_time": 100.0,
            }
        ],
    )

    with patch("agent.recovery.process.psutil.Process") as mock_psutil_proc:
        verified_proc = mock_psutil_proc.return_value
        verified_proc.name.return_value = "worker.exe"
        verified_proc.create_time.return_value = 100.0

        result = recovery.recover()

        verified_proc.terminate.assert_called_once()
        verified_proc.wait.assert_called_once_with(timeout=5)
        assert result["status"] == "recovered"
        assert result["pid"] == 20
        assert result["before"] == 95
        assert result["after"] == 40
