from .config import (CPU_CRITICAL_THRESHOLD, CPU_WARNING_THRESHOLD, MEMORY_CRITICAL_THRESHOLD, MEMORY_WARNING_THRESHOLD, DISK_CRITICAL_THRESHOLD, DISK_WARNING_THRESHOLD, PROCESS_CPU_CRITICAL_THRESHOLD, PROCESS_CPU_WARNING_THRESHOLD, PROCESS_MEMORY_CRITICAL_THRESHOLD, PROCESS_MEMORY_WARNING_THRESHOLD)


def get_cpu_status(cpu_usage):
    """Classify CPU usage against the configured thresholds."""
    if cpu_usage >= CPU_CRITICAL_THRESHOLD:
        return "CRITICAL"
    elif cpu_usage >= CPU_WARNING_THRESHOLD:
        return "WARNING"
    else:
        return "HEALTHY"


def get_memory_status(memory_usage):
    """Classify memory usage against the configured thresholds."""
    if memory_usage >= MEMORY_CRITICAL_THRESHOLD:
        return "CRITICAL"

    elif memory_usage >= MEMORY_WARNING_THRESHOLD:
        return "WARNING"

    else:
        return "HEALTHY"


def get_disk_status(disk_usage):
    """Classify disk usage against the configured thresholds."""
    if disk_usage >= DISK_CRITICAL_THRESHOLD:
        return "CRITICAL"
    elif disk_usage >= DISK_WARNING_THRESHOLD:
        return "WARNING"
    else:
        return "HEALTHY"


def get_process_status(process_info):
    """Classify a monitored process or flag a missing process as critical."""
    if process_info is None:
        return "CRITICAL"

    cpu_usage = process_info["cpu_percent"]
    memory_usage = process_info["memory_percent"]

    if (
        cpu_usage >= PROCESS_CPU_CRITICAL_THRESHOLD
        or memory_usage >= PROCESS_MEMORY_CRITICAL_THRESHOLD
    ):
        return "CRITICAL"

    elif (
        cpu_usage >= PROCESS_CPU_WARNING_THRESHOLD
        or memory_usage >= PROCESS_MEMORY_WARNING_THRESHOLD
    ):
        return "WARNING"

    else:
        return "HEALTHY"


def get_network_status(network_info):
    """Classify a network interface or flag a missing interface as critical."""
    if network_info is None:
        return "CRITICAL"

    if not network_info["is_up"]:
        return "CRITICAL"

    return "HEALTHY"
