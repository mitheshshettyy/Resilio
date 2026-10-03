import time

from agent.recovery.process import ProcessRecovery
from agent.recovery.memory import MemoryRecovery
from agent.recovery.cpu import CpuRecovery
from agent.recovery.disk import DiskRecovery
from agent.recovery.network import NetworkRecovery


class RecoveryManager:
    """Manages recovery actions for system components."""

    MAX_RECOVERY_ATTEMPTS = 2
    RECOVERY_COOLDOWN = 60

    def __init__(self, clock=None):
        self._clock = clock or time.monotonic
        self._state = {}

    def _get_state(self, component):
        if component not in self._state:
            self._state[component] = {
                "attempt_count": 0,
                "cooldown_until": None,
                "last_outcome": None,
            }

        return self._state[component]

    def _can_recover(self, component):
        state = self._get_state(component)
        current_time = self._clock()

        if state["cooldown_until"] is not None:
            if current_time < state["cooldown_until"]:
                return False

            state["cooldown_until"] = None
            state["attempt_count"] = 0

        if state["attempt_count"] >= self.MAX_RECOVERY_ATTEMPTS:
            state["cooldown_until"] = (
                current_time + self.RECOVERY_COOLDOWN
            )
            state["last_outcome"] = "COOLDOWN"
            return False

        return True

    def _record_failure(self, component, outcome):
        state = self._get_state(component)

        state["attempt_count"] += 1
        state["last_outcome"] = outcome

    def _record_success(self, component):
        state = self._get_state(component)

        state["attempt_count"] = 0
        state["cooldown_until"] = None
        state["last_outcome"] = "RECOVERY_VERIFIED"

    def recover(self, component, **kwargs):
        """Dispatch a component recovery request after validating its inputs."""

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
