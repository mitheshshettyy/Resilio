import time

from .collectors.cpu import get_cpu_usage
from .config import MONITOR_INTERVAL
from .health import get_cpu_status


def main():
    print("Resilio monitoring agent started.")
    print(f"Monitoring interval: {MONITOR_INTERVAL} seconds\n")

    while True:
        cpu_usage = get_cpu_usage()
        status = get_cpu_status(cpu_usage)

        print(f"CPU Usage: {cpu_usage}% | Status: {status}")

        time.sleep(MONITOR_INTERVAL)


if __name__ == "__main__":
    main()