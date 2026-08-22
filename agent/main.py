import time

from config import MONITOR_INTERVAL
from collectors.cpu import get_cpu_usage


def main():
    print("Resilio monitoring agent started.")
    print(f"Monitoring interval: {MONITOR_INTERVAL} seconds\n")

    while True:
        cpu_usage = get_cpu_usage()

        print(f"CPU Usage: {cpu_usage}%")

        time.sleep(MONITOR_INTERVAL)


if __name__ == "__main__":
    main()