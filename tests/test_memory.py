from agent.collectors.memory import get_memory_usage
from unittest.mock import patch
from agent.health import get_memory_status
from agent.config import (
    MEMORY_WARNING_THRESHOLD,
    MEMORY_CRITICAL_THRESHOLD,
)


def test_get_memory_usage():
    with patch("agent.collectors.memory.psutil.virtual_memory") as mock_memory:
        mock_memory.return_value.percent = 65.5

        result = get_memory_usage()

        assert result == 65.5


def test_memory_status_healthy():
    memory_usage = MEMORY_WARNING_THRESHOLD - 1

    assert get_memory_status(memory_usage) == "HEALTHY"


def test_memory_status_warning():
    memory_usage = MEMORY_WARNING_THRESHOLD

    assert get_memory_status(memory_usage) == "WARNING"


def test_memory_status_critical():
    memory_usage = MEMORY_CRITICAL_THRESHOLD + 1

    assert get_memory_status(memory_usage) == "CRITICAL"