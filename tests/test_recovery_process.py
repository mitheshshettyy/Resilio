import psutil
from unittest.mock import patch

from agent.recovery.process import ProcessRecovery


@patch("agent.recovery.process.psutil.Process")
def test_recover_process_successfully(mock_process):
    process = mock_process.return_value

    recovery = ProcessRecovery()
    result = recovery.recover(1234)

    mock_process.assert_called_once_with(1234)
    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=5)

    assert result == {
        "pid": 1234,
        "status": "recovered",
    }


@patch(
    "agent.recovery.process.psutil.Process",
    side_effect=psutil.NoSuchProcess(1234),
)
def test_recover_process_not_found(mock_process):
    recovery = ProcessRecovery()

    result = recovery.recover(1234)

    mock_process.assert_called_once_with(1234)

    assert result == {
        "pid": 1234,
        "status": "not_found",
    }


@patch(
    "agent.recovery.process.psutil.Process",
    side_effect=psutil.AccessDenied(1234),
)
def test_recover_process_access_denied(mock_process):
    recovery = ProcessRecovery()

    result = recovery.recover(1234)

    mock_process.assert_called_once_with(1234)

    assert result == {
        "pid": 1234,
        "status": "access_denied",
    }


@patch("agent.recovery.process.psutil.Process")
def test_recover_process_timeout(mock_process):
    process = mock_process.return_value
    process.wait.side_effect = psutil.TimeoutExpired(1234, 5)

    recovery = ProcessRecovery()

    result = recovery.recover(1234)

    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=5)

    assert result == {
        "pid": 1234,
        "status": "recovery_failed",
    }


def test_get_memory_processes():
    recovery = ProcessRecovery()

    processes = recovery.get_memory_processes()

    assert isinstance(processes, list)

    if processes:
        assert "pid" in processes[0]
        assert "name" in processes[0]
        assert "memory_mb" in processes[0]

        for i in range(len(processes) - 1):
            assert (
                processes[i]["memory_mb"]
                >= processes[i + 1]["memory_mb"]
            )


def test_select_recovery_candidate():
    recovery = ProcessRecovery()

    processes = [
        {"pid": 100, "name": "lsass.exe", "memory_mb": 1000},
        {"pid": 200, "name": "chrome.exe", "memory_mb": 800},
    ]

    candidate = recovery.select_recovery_candidate(processes)

    assert candidate["pid"] == 200
    assert candidate["name"] == "chrome.exe"


def test_select_recovery_candidate_skips_current_process():
    recovery = ProcessRecovery()

    current_pid = psutil.Process().pid

    processes = [
        {
            "pid": current_pid,
            "name": "python.exe",
            "memory_mb": 1000,
        },
        {
            "pid": 200,
            "name": "chrome.exe",
            "memory_mb": 800,
        },
    ]

    candidate = recovery.select_recovery_candidate(processes)

    assert candidate["pid"] == 200


def test_select_recovery_candidate_returns_none_when_all_unsafe():
    recovery = ProcessRecovery()

    current_pid = psutil.Process().pid

    processes = [
        {
            "pid": current_pid,
            "name": "python.exe",
            "memory_mb": 1000,
        },
        {
            "pid": 200,
            "name": "lsass.exe",
            "memory_mb": 900,
        },
    ]

    candidate = recovery.select_recovery_candidate(processes)

    assert candidate is None


def test_select_recovery_candidate_skips_missing_values():
    recovery = ProcessRecovery()

    processes = [
        {"pid": None, "name": "chrome.exe", "memory_mb": 1000},
        {"pid": 200, "name": None, "memory_mb": 900},
        {"pid": 300, "name": "chrome.exe", "memory_mb": 800},
    ]

    candidate = recovery.select_recovery_candidate(processes)

    assert candidate["pid"] == 300