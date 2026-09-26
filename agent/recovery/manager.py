from agent.recovery.process import ProcessRecovery
from agent.recovery.memory import MemoryRecovery
from agent.recovery.cpu import CpuRecovery
from agent.recovery.disk import DiskRecovery


class RecoveryManager:
    """Manages recovery actions for system components."""

    def recover(self, component, **kwargs):
        """Attempt recovery for the given component."""

        if component == "process":
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

        return {
            "component": component,
            "status": "not_implemented",
        }
