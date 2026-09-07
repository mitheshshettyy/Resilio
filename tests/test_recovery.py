from unittest.mock import patch

from agent.recovery.manager import RecoveryManager


def test_recovery_not_implemented():
    manager = RecoveryManager()

    result = manager.recover("memory")

    assert result["component"] == "memory"
    assert result["status"] == "not_implemented"


@patch("agent.recovery.manager.ProcessRecovery")
def test_process_recovery(mock_process_recovery):
    recovery = mock_process_recovery.return_value
    recovery.recover.return_value = {
        "pid": 1234,
        "status": "recovered",
    }

    manager = RecoveryManager()

    result = manager.recover("process", pid=1234)

    mock_process_recovery.assert_called_once_with()
    recovery.recover.assert_called_once_with(1234)

    assert result == {
        "pid": 1234,
        "status": "recovered",
    }