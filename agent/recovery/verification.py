"""Fresh health verification for recovery actions."""

from agent.collectors.cpu import get_cpu_usage
from agent.collectors.disk import get_disk_usage
from agent.collectors.memory import get_memory_usage
from agent.collectors.network import get_network_info
from agent.health import (
    get_cpu_status,
    get_disk_status,
    get_memory_status,
    get_network_status,
)


class RecoveryVerifier:
    """Collect a component's current state after a recovery action."""

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
            return self._unverifiable(
                component,
                "process recovery verification is unsupported until its contract is defined",
            )

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
