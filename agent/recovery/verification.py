"""Fresh health verification for recovery actions."""

import time

import psutil

from agent.collectors.cpu import get_cpu_usage
from agent.collectors.disk import get_disk_usage
from agent.collectors.memory import get_memory_usage
from agent.collectors.network import get_network_info
from agent.collectors.process import get_process_info
from agent.health import (
    get_cpu_status,
    get_disk_status,
    get_memory_status,
    get_network_status,
    get_process_status,
)


class RecoveryVerifier:
    """Collect a component's current state after a recovery action."""

    def __init__(self, pid_exists_func=None, sleep_func=None, stabilization_delay=0.0):
        self._pid_exists_func = pid_exists_func or psutil.pid_exists
        self._sleep_func = sleep_func or time.sleep
        self._stabilization_delay = stabilization_delay

    def verify(self, component, context=None):
        """Return fresh health evidence without making policy decisions."""
        context = context or {}

        if component == "cpu":
            return self._metric_result(
                component, get_cpu_usage(), get_cpu_status
            )

        if component == "memory":
            return self._metric_result(
                component, get_memory_usage(), get_memory_status
            )

        if component == "disk":
            return self._metric_result(
                component, get_disk_usage(), get_disk_status
            )

        if component == "network":
            interface = context.get("interface")
            if not interface:
                return self._unverifiable(
                    component, "network interface is required for verification"
                )

            network_info = get_network_info(interface)
            health_status = get_network_status(network_info)
            return {
                "component": component,
                "verification_status": self._verification_status(health_status),
                "health_status": health_status,
                "measurement": network_info,
            }

        if component == "process":
            target_pid = context.get("target_pid")
            process_name = context.get("process_name")

            if target_pid is None and not process_name:
                return self._unverifiable(
                    component,
                    "process verification requires target_pid or process_name",
                )

            if target_pid is not None:
                if self._pid_exists_func(target_pid):
                    return {
                        "component": component,
                        "verification_status": "not_verified",
                        "health_status": "CRITICAL",
                        "reason": f"process with target PID {target_pid} is still running",
                    }

            if self._stabilization_delay > 0:
                self._sleep_func(self._stabilization_delay)

            if process_name:
                current_process = get_process_info(process_name)
                if current_process is not None:
                    health_status = get_process_status(current_process)
                    if health_status in {"HEALTHY", "WARNING"}:
                        return {
                            "component": component,
                            "verification_status": "verified",
                            "health_status": health_status,
                            "measurement": current_process,
                        }
                    else:
                        return {
                            "component": component,
                            "verification_status": "not_verified",
                            "health_status": health_status,
                            "measurement": current_process,
                            "reason": f"replacement process {process_name} is {health_status}",
                        }
                else:
                    if target_pid is not None:
                        return {
                            "component": component,
                            "verification_status": "verified",
                            "health_status": "CRITICAL",
                            "measurement": None,
                        }
                    else:
                        return {
                            "component": component,
                            "verification_status": "not_verified",
                            "health_status": "CRITICAL",
                            "measurement": None,
                            "reason": f"process {process_name} is not running",
                        }

            return {
                "component": component,
                "verification_status": "verified",
                "health_status": None,
            }

        return self._unverifiable(component, "unsupported recovery component")

    @classmethod
    def _metric_result(cls, component, measurement, health_function):
        health_status = health_function(measurement)
        return {
            "component": component,
            "verification_status": cls._verification_status(health_status),
            "health_status": health_status,
            "measurement": measurement,
        }

    @staticmethod
    def _verification_status(health_status):
        if health_status in {"HEALTHY", "WARNING"}:
            return "verified"

        return "not_verified"

    @staticmethod
    def _unverifiable(component, reason):
        return {
            "component": component,
            "verification_status": "unverifiable",
            "health_status": None,
            "reason": reason,
        }
