import psutil


def get_cpu_usage():
    """Return system-wide CPU usage after a one-second sample."""
    return psutil.cpu_percent(interval=1)
