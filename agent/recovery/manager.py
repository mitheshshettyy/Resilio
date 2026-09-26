from agent.recovery.process import ProcessRecovery
from agent.recovery.memory import MemoryRecovery
from agent.recovery.cpu import CpuRecovery
from agent.recovery.disk import DiskRecovery
from agent.recovery.network import NetworkRecovery


class RecoveryManager:
    """Manages recovery actions for system components."""

    def recover(self, component, **kwargs):
        """Attempt recovery for the given component."""

        if component == "process":
            if "pid" not in kwargs:
                return {
                    "component": "process",
                    "status": "invalid_arguments",
                }
            recovery = ProcessRecovery()
            return recovery.recover(kwargs["pid"])

        if component == "memory":
            recovery = MemoryRecovery()
            return recovery.recover()

        if component == "cpu":
            recovery = CpuRecovery()
            return recovery.recover()

        if component == "disk":
            recovery = DiskRecovery()
            return recovery.recover()

        if component == "network":
            if "interface" not in kwargs:
                return {
                    "component": "network",
                    "status": "invalid_arguments",
                }
            recovery = NetworkRecovery()
            return recovery.recover(kwargs["interface"])

        return {
            "component": component,
            "status": "not_implemented",
        }
