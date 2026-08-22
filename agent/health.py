def get_cpu_status(cpu_usage):
    if cpu_usage > 90:
        return "CRITICAL"
    elif cpu_usage >= 80:
        return "WARNING"
    else:
        return "HEALTHY"