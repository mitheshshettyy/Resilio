import psutil
import os
from unittest.mock import patch

from agent.recovery.process import ProcessRecovery


@patch("agent.recovery.process.psutil.Process")
def test_recover_process_successfully(mock_process):
    process = mock_process.return_value
    process.name.return_value = "worker.exe"

    recovery = ProcessRecovery()
    result = recovery.recover(1234)

    mock_process.assert_called_once_with(1234)
    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=5)

    assert result == {
        "component": "process",
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
        "component": "process",
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
        "component": "process",
        "pid": 1234,
        "status": "access_denied",
    }


@patch("agent.recovery.process.psutil.Process")
def test_recover_process_timeout(mock_process):
    process = mock_process.return_value
    process.name.return_value = "worker.exe"
    process.wait.side_effect = psutil.TimeoutExpired(1234, 5)

    recovery = ProcessRecovery()

    result = recovery.recover(1234)

    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=5)

    assert result == {
        "component": "process",
        "pid": 1234,
        "status": "recovery_failed",
    }


def test_get_memory_processes():
    recovery = ProcessRecovery()

    heavy = type(
        "Process",
        (),
        {
            "info": {
                "pid": 200,
                "name": "heavy.exe",
                "memory_info": type("Memory", (), {"rss": 20 * 1024 * 1024})(),
            }
        },
    )()
    light = type(
        "Process",
        (),
        {
            "info": {
                "pid": 100,
                "name": "light.exe",
                "memory_info": type("Memory", (), {"rss": 10 * 1024 * 1024})(),
            }
        },
    )()

    with patch(
        "agent.recovery.process.psutil.process_iter",
        return_value=[light, heavy],
    ):
        processes = recovery.get_memory_processes()

    assert isinstance(processes, list)

    assert [process["pid"] for process in processes] == [200, 100]


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


@patch("agent.recovery.process.psutil.Process")
def test_recover_process_refuses_protected_process(mock_process):
    process = mock_process.return_value
    process.name.return_value = "lsass.exe"

    result = ProcessRecovery().recover(1234)

    process.terminate.assert_not_called()
    assert result["status"] == "protected_process"


@patch("agent.recovery.process.psutil.Process")
def test_recover_process_refuses_current_process(mock_process):
    result = ProcessRecovery().recover(os.getpid())

    mock_process.assert_not_called()
    assert result["status"] == "current_process"


@patch("agent.recovery.process.psutil.Process")
def test_recover_process_rejects_invalid_pid(mock_process):
    result = ProcessRecovery().recover(0)

    mock_process.assert_not_called()
    assert result["status"] == "invalid_pid"


def test_process_start_unavailable_without_starter_hook():
    recovery = ProcessRecovery(starter=None)

    result = recovery.start("python.exe")

    assert result == {
        "component": "process",
        "status": "recovery_unavailable",
    }


def test_process_start_executes_starter_hook_successfully():
    called_with = []

    def starter(name):
        called_with.append(name)
        return 4321

    recovery = ProcessRecovery(starter=starter)
    result = recovery.start("python.exe")

    assert called_with == ["python.exe"]
    assert result == {
        "component": "process",
        "status": "recovered",
        "process_name": "python.exe",
        "pid": 4321,
    }


def test_process_start_handles_starter_exception():
    def failing_starter(name):
        raise OSError("failed to launch process")

    recovery = ProcessRecovery(starter=failing_starter)
    result = recovery.start("python.exe")

    assert result["status"] == "recovery_failed"
    assert "failed to launch process" in result["reason"]


def test_invalid_starter_result_is_handled_safely():
    recovery = ProcessRecovery(starter=lambda name: False)
    result = recovery.start("python.exe")
    assert result["status"] == "recovery_failed"

    recovery_negative_pid = ProcessRecovery(starter=lambda name: -1)
    result_neg = recovery_negative_pid.start("python.exe")
    assert result_neg["status"] == "recovery_failed"
    assert result_neg["reason"] == "invalid_pid"


def test_process_start_rejects_invalid_process_name():
    recovery = ProcessRecovery(starter=lambda name: 1234)
    result = recovery.start("")
    assert result["status"] == "invalid_arguments"
