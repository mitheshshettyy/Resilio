from unittest.mock import patch

import psutil

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