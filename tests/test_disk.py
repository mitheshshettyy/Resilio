from agent.collectors.disk import get_disk_usage
from unittest.mock import patch
from agent.health import get_disk_status
from agent.config import (
    DISK_WARNING_THRESHOLD,
    DISK_CRITICAL_THRESHOLD,
)

def test_get_disk_usage():
    with patch("agent.collectors.disk.psutil.disk_usage") as mock_disk:
        mock_disk.return_value.percent = 45.5

        result = get_disk_usage()

        assert result == 45.5

def test_disk_status_healthy():
    disk_usage = DISK_WARNING_THRESHOLD - 1

    assert get_disk_status(disk_usage) == "HEALTHY"


def test_disk_status_warning():
    disk_usage = DISK_WARNING_THRESHOLD

    assert get_disk_status(disk_usage) == "WARNING"


def test_disk_status_critical():
    disk_usage = DISK_CRITICAL_THRESHOLD

    assert get_disk_status(disk_usage) == "CRITICAL"