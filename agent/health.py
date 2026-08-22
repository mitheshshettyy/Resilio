from .config import CPU_CRITICAL_THRESHOLD, CPU_WARNING_THRESHOLD

def get_cpu_status(cpu_usage):
    if cpu_usage > CPU_CRITICAL_THRESHOLD:
        return "CRITICAL"
    elif cpu_usage >= CPU_WARNING_THRESHOLD:
        return "WARNING"
    else:
        return "HEALTHY"