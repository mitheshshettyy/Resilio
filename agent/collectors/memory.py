import psutil


def get_memory_usage():
    """Return the percentage of virtual memory currently in use."""
    memory = psutil.virtual_memory()
    return memory.percent
