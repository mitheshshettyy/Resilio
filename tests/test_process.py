from unittest.mock import patch

import psutil

from agent.collectors.process import get_process_info
from agent.health import get_process_status
from agent.config import (
    PROCESS_CPU_WARNING_THRESHOLD,
    PROCESS_CPU_CRITICAL_THRESHOLD,
    PROCESS_MEMORY_WARNING_THRESHOLD,
    PROCESS_MEMORY_CRITICAL_THRESHOLD,
)

def test_process_found():
    process = type(
        "Process",
        (),
        {
            "info": {
                "pid": 1234,
                "name": "python.exe",
                "cpu_percent": 10,
                "memory_percent": 5,
            }
        },
    )()

    with patch("agent.collectors.process.psutil.process_iter", return_value=[process]):
        result = get_process_info("python.exe")

    assert result is not None
    assert result["name"] == "python.exe"
    assert "pid" in result
    assert "cpu_percent" in result
    assert "memory_percent" in result


def test_process_not_found():
    with patch("agent.collectors.process.psutil.process_iter", return_value=[]):
        result = get_process_info("definitely_not_a_real_process.exe")

    assert result is None


def test_process_skips_access_denied_process():
    class DeniedProcess:
        @property
        def info(self):
            raise psutil.AccessDenied(pid=1234)

    with patch(
        "agent.collectors.process.psutil.process_iter",
        return_value=[DeniedProcess()],
    ):
        assert get_process_info("python.exe") is None


def test_process_status_healthy():
    process_info = {
        "cpu_percent": PROCESS_CPU_WARNING_THRESHOLD - 1,
        "memory_percent": PROCESS_MEMORY_WARNING_THRESHOLD - 1,
    }

    assert get_process_status(process_info) == "HEALTHY"


def test_process_status_cpu_warning():
    process_info = {
        "cpu_percent": PROCESS_CPU_WARNING_THRESHOLD,
        "memory_percent": 0,
    }

    assert get_process_status(process_info) == "WARNING"


def test_process_status_memory_warning():
    process_info = {
        "cpu_percent": 0,
        "memory_percent": PROCESS_MEMORY_WARNING_THRESHOLD,
    }

    assert get_process_status(process_info) == "WARNING"


def test_process_status_cpu_critical():
    process_info = {
        "cpu_percent": PROCESS_CPU_CRITICAL_THRESHOLD,
        "memory_percent": 0,
    }

    assert get_process_status(process_info) == "CRITICAL"


def test_process_status_memory_critical():
    process_info = {
        "cpu_percent": 0,
        "memory_percent": PROCESS_MEMORY_CRITICAL_THRESHOLD,
    }

    assert get_process_status(process_info) == "CRITICAL"


def test_process_status_missing():
    assert get_process_status(None) == "CRITICAL"
