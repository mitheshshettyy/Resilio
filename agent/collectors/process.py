import psutil


def get_process_info(process_name):
    """Return metrics for the first accessible process with the given name."""
    for process in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            if process.info["name"] == process_name:
                return {
                    "pid": process.info["pid"],
                    "name": process.info["name"],
                    "cpu_percent": process.info["cpu_percent"],
                    "memory_percent": process.info["memory_percent"],
                }

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return None
