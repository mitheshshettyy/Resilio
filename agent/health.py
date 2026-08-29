from .config import ( CPU_CRITICAL_THRESHOLD, CPU_WARNING_THRESHOLD, MEMORY_CRITICAL_THRESHOLD, MEMORY_WARNING_THRESHOLD, DISK_CRITICAL_THRESHOLD, DISK_WARNING_THRESHOLD,)
def get_cpu_status(cpu_usage):
    if cpu_usage >= CPU_CRITICAL_THRESHOLD:
        return "CRITICAL"
    elif cpu_usage >= CPU_WARNING_THRESHOLD:
        return "WARNING"
    else:
        return "HEALTHY"


def get_memory_status(memory_usage):
    if memory_usage > MEMORY_CRITICAL_THRESHOLD:
        return "CRITICAL"

    elif memory_usage >= MEMORY_WARNING_THRESHOLD:
        return "WARNING"

    else:
        return "HEALTHY"


def get_disk_status(disk_usage):
    if disk_usage >= DISK_CRITICAL_THRESHOLD:
        return "CRITICAL"
    elif disk_usage >= DISK_WARNING_THRESHOLD:
        return "WARNING"
    else:
        return "HEALTHY"


def get_process_status(process_info):
    if process_info is None:
        return "CRITICAL"

    return "HEALTHY"