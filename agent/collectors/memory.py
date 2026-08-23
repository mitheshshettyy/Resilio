import psutil


def get_memory_usage():
    memory = psutil.virtual_memory()
    return memory.percent