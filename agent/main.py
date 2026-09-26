import time

from .collectors.cpu import get_cpu_usage
from .collectors.memory import get_memory_usage
from .collectors.disk import get_disk_usage
from .collectors.process import get_process_info
from .collectors.network import get_network_info
from .config import MONITOR_INTERVAL, PROCESS_NAME, NETWORK_INTERFACE
from .health import (
    get_cpu_status,
    get_memory_status,
    get_disk_status,
    get_process_status,
    get_network_status,
)
from .recovery.manager import RecoveryManager


def monitor_once(recovery_manager):
    """Run one monitoring and recovery cycle."""

    cpu_usage = get_cpu_usage()
    memory_usage = get_memory_usage()
    disk_usage = get_disk_usage()
    process_info = get_process_info(PROCESS_NAME)
    network_info = get_network_info(NETWORK_INTERFACE)

    cpu_status = get_cpu_status(cpu_usage)
    memory_status = get_memory_status(memory_usage)
    disk_status = get_disk_status(disk_usage)
    process_status = get_process_status(process_info)
    network_status = get_network_status(network_info)

    if cpu_status == "CRITICAL":
        result = recovery_manager.recover("cpu")
        print(f"CPU Recovery: {result}")

    if memory_status == "CRITICAL":
        result = recovery_manager.recover("memory")
        print(f"Memory Recovery: {result}")

    if disk_status == "CRITICAL":
        result = recovery_manager.recover("disk")
        print(f"Disk Recovery: {result}")

    if process_status == "CRITICAL" and process_info:
        result = recovery_manager.recover(
            "process",
            pid=process_info["pid"],
        )
        print(f"Process Recovery: {result}")

    if network_info:
        print(
            f"CPU Usage: {cpu_usage}% | CPU Status: {cpu_status} | "
            f"Memory Usage: {memory_usage}% | Memory Status: {memory_status} | "
            f"Disk Usage: {disk_usage}% | Disk Status: {disk_status} | "
            f"Process: {process_info['name'] if process_info else PROCESS_NAME} | "
            f"PID: {process_info['pid'] if process_info else 'N/A'} | "
            f"Process Status: {process_status} | "
            f"Network: {network_info['interface']} | "
            f"Network Status: {network_status} | "
            f"Bytes Sent: {network_info['bytes_sent']} | "
            f"Bytes Received: {network_info['bytes_recv']}"
        )
    else:
        print(
            f"CPU Usage: {cpu_usage}% | CPU Status: {cpu_status} | "
            f"Memory Usage: {memory_usage}% | Memory Status: {memory_status} | "
            f"Disk Usage: {disk_usage}% | Disk Status: {disk_status} | "
            f"Process: {PROCESS_NAME} | "
            f"Process Status: {process_status} | "
            f"Network: {NETWORK_INTERFACE} | "
            f"Network Status: {network_status}"
        )


def main():
    print("Resilio monitoring agent started.")
    print(f"Monitoring interval: {MONITOR_INTERVAL} seconds\n")

    recovery_manager = RecoveryManager()

    try:
        while True:
            monitor_once(recovery_manager)
            time.sleep(MONITOR_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping Resilio monitoring agent...")
        print("Agent stopped.")


if __name__ == "__main__":
    main()
