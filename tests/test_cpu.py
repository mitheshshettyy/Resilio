from unittest.mock import patch

from agent.collectors.cpu import get_cpu_usage
from agent.config import CPU_CRITICAL_THRESHOLD, CPU_WARNING_THRESHOLD
from agent.health import get_cpu_status


def test_get_cpu_usage():
    with patch("agent.collectors.cpu.psutil.cpu_percent", return_value=45.5) as mock_cpu:
        assert get_cpu_usage() == 45.5

    mock_cpu.assert_called_once_with(interval=1)


def test_cpu_status_healthy():
    assert get_cpu_status(CPU_WARNING_THRESHOLD - 1) == "HEALTHY"


def test_cpu_status_warning():
    assert get_cpu_status(CPU_WARNING_THRESHOLD) == "WARNING"


def test_cpu_status_critical():
    assert get_cpu_status(CPU_CRITICAL_THRESHOLD) == "CRITICAL"
