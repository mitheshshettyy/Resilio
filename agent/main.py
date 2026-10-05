import logging
import time

from .collectors.cpu import get_cpu_usage
from .collectors.memory import get_memory_usage
from .collectors.disk import get_disk_usage
from .collectors.process import get_process_info
from .collectors.network import get_network_info
from .config import LOG_LEVEL, MONITOR_INTERVAL, PROCESS_NAME, NETWORK_INTERFACE
from .health import (
    get_cpu_status,
    get_memory_status,
    get_disk_status,
    get_process_status,
    get_network_status,
)
from .recovery.manager import RecoveryManager
from .monitoring import MonitoringPipeline, MonitoringTarget

def monitor_once(recovery_manager):
    """Run, print, and return one structured monitoring cycle."""
    result = MonitoringPipeline(recovery_manager, _monitoring_targets()).run()
    _print_cycle_result(result)
    return result


def _monitoring_targets():
    """Build monitoring targets while retaining the existing collector contracts."""
    return [
        MonitoringTarget("cpu", get_cpu_usage, get_cpu_status, _no_arguments),
        MonitoringTarget("memory", get_memory_usage, get_memory_status, _no_arguments),
        MonitoringTarget("disk", get_disk_usage, get_disk_status, _no_arguments),
        MonitoringTarget(
            "process",
            lambda: get_process_info(PROCESS_NAME),
            get_process_status,
            _process_recovery_arguments,
        ),
        MonitoringTarget(
            "network",
            lambda: get_network_info(NETWORK_INTERFACE),
            get_network_status,
            _network_recovery_arguments,
        ),
    ]


def _no_arguments(measurement):
    return {}, {}


def _process_recovery_arguments(process_info):
    if process_info is None:
        return {}, None
    return {"process_name": PROCESS_NAME}, {"pid": process_info["pid"]}


def _network_recovery_arguments(network_info):
    if network_info is None:
        return {}, None
    return {"interface": NETWORK_INTERFACE}, {"interface": NETWORK_INTERFACE}


def _print_cycle_result(cycle_result):
    """Print concise, complete status for every component in a cycle."""
    for result in cycle_result.components:
        message = (
            f"{result.component.upper()}: health={result.health_status} "
            f"recovery_required={result.recovery_required} "
            f"recovery_attempted={result.recovery_attempted}"
        )
        if result.recovery_result:
            message += (
                f" action={result.recovery_result.get('action_status', result.recovery_result.get('status'))}"
                f" verification={result.recovery_result.get('verification_status', 'N/A')}"
            )
        else:
            message += " action=not_attempted verification=not_attempted"
        if result.recovery_result:
            if result.recovery_result.get("reason"):
                message += f" reason={result.recovery_result['reason']}"
        if result.error:
            message += f" error={result.error}"
        print(message)


def main():
    """Run monitoring cycles until the agent is interrupted."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
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
