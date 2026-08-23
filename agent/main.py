import time

from .collectors.cpu import get_cpu_usage
from .config import MONITOR_INTERVAL
from .health import get_cpu_status, get_memory_status
from .collectors.memory import get_memory_usage


def main():
    print("Resilio monitoring agent started.")
    print(f"Monitoring interval: {MONITOR_INTERVAL} seconds\n")

    try:
        while True:
            cpu_usage = get_cpu_usage()
            memory_usage = get_memory_usage()

            cpu_status = get_cpu_status(cpu_usage)
            memory_status = get_memory_status(memory_usage)

            print(f"CPU Usage: {cpu_usage}% | CPU Status: {cpu_status} | "f"Memory Usage: {memory_usage}% | Memory Status: {memory_status}")

            time.sleep(MONITOR_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping Resilio monitoring agent...")
        print("Agent stopped.")


if __name__ == "__main__":
    main()