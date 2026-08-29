import time

from .collectors.cpu import get_cpu_usage
from .collectors.memory import get_memory_usage
from .collectors.disk import get_disk_usage
from .collectors.process import get_process_info
from .config import MONITOR_INTERVAL, PROCESS_NAME
from .health import get_cpu_status, get_memory_status, get_disk_status, get_process_status

def main():
    print("Resilio monitoring agent started.")
    print(f"Monitoring interval: {MONITOR_INTERVAL} seconds\n")

    try:
        while True:
            cpu_usage = get_cpu_usage()
            memory_usage = get_memory_usage()
            disk_usage = get_disk_usage()
            process_info = get_process_info(PROCESS_NAME)

            cpu_status = get_cpu_status(cpu_usage)
            memory_status = get_memory_status(memory_usage)
            disk_status = get_disk_status(disk_usage)
            process_status = get_process_status(process_info)

            if process_info:
                print(f"CPU Usage: {cpu_usage}% | CPU Status: {cpu_status} | "f"Memory Usage: {memory_usage}% | Memory Status: {memory_status} | "f"Disk Usage: {disk_usage}% | Disk Status: {disk_status} | "f"Process: {process_info['name']} | PID: {process_info['pid']} | "f"Process Status: {process_status}")
            else:
                print(f"CPU Usage: {cpu_usage}% | CPU Status: {cpu_status} | "f"Memory Usage: {memory_usage}% | Memory Status: {memory_status} | "f"Disk Usage: {disk_usage}% | Disk Status: {disk_status} | "f"Process: {PROCESS_NAME} | Process Status: {process_status}")

            time.sleep(MONITOR_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping Resilio monitoring agent...")
        print("Agent stopped.")


if __name__ == "__main__":
    main()