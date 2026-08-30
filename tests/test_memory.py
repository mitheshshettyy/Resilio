from agent.health import get_memory_status
from agent.config import (
    MEMORY_WARNING_THRESHOLD,
    MEMORY_CRITICAL_THRESHOLD,
)


def test_memory_status_healthy():
    memory_usage = MEMORY_WARNING_THRESHOLD - 1

    assert get_memory_status(memory_usage) == "HEALTHY"


def test_memory_status_warning():
    memory_usage = MEMORY_WARNING_THRESHOLD

    assert get_memory_status(memory_usage) == "WARNING"


def test_memory_status_critical():
    memory_usage = MEMORY_CRITICAL_THRESHOLD + 1

    assert get_memory_status(memory_usage) == "CRITICAL"
