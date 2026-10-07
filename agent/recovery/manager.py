import time
import logging

from agent.config import MAX_RECOVERY_ATTEMPTS, RECOVERY_COOLDOWN_SECONDS
from agent.recovery.process import ProcessRecovery
from agent.recovery.memory import MemoryRecovery
from agent.recovery.cpu import CpuRecovery
from agent.recovery.disk import DiskRecovery
from agent.recovery.network import NetworkRecovery
from agent.recovery.verification import RecoveryVerifier


logger = logging.getLogger(__name__)


class RecoveryManager:
    """Manages recovery actions for system components."""

    MAX_RECOVERY_ATTEMPTS = MAX_RECOVERY_ATTEMPTS
    RECOVERY_COOLDOWN = RECOVERY_COOLDOWN_SECONDS

    def __init__(self, clock=None, verifier=None, process_starter=None):
        self._clock = clock or time.monotonic
        self._state = {}
        self._verifier = verifier or RecoveryVerifier()
        self._process_starter = process_starter

    def can_restart_process(self):
        """Return True if an optional process starter is configured."""
        return self._process_starter is not None

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
            logger.warning(
                "Recovery retry budget exhausted; cooldown entered for component=%s",
                component,
            )
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

    def recover_and_verify(self, component, context=None, **kwargs):
        """Apply the existing policy around an action and fresh verification."""
        context = dict(context or {})
        if component == "process":
            if "pid" in kwargs and "target_pid" not in context:
                context["target_pid"] = kwargs["pid"]
            if "process_name" in kwargs and "process_name" not in context:
                context["process_name"] = kwargs["process_name"]
        logger.info("Recovery requested for component=%s", component)

        if not self._can_recover(component):
            logger.info("Recovery skipped due to cooldown for component=%s", component)
            return self._result(
                component,
                action_status="not_attempted",
                verification_status="not_attempted",
                reason="cooldown_active",
            )

        logger.info("Recovery attempted for component=%s", component)
        try:
            action_result = self.recover(component, **kwargs)
        except Exception as error:
            self._record_failure(component, "RECOVERY_ACTION_FAILED")
            logger.exception("Recovery action raised an error for component=%s", component)
            return self._result(
                component,
                action_status="recovery_failed",
                verification_status="not_attempted",
                reason=str(error),
            )

        action_status = action_result["status"]

        if action_status not in {"recovered", "not_required"}:
            outcome = (
                "RECOVERY_UNAVAILABLE"
                if action_status == "recovery_unavailable"
                else "RECOVERY_ACTION_FAILED"
            )
            self._record_failure(component, outcome)
            logger.warning(
                "Recovery action failed for component=%s status=%s",
                component,
                action_status,
            )
            verification_status = (
                "unverifiable"
                if action_status == "recovery_unavailable"
                else "not_attempted"
            )
            return self._result(
                component,
                action_status=action_status,
                verification_status=verification_status,
                reason=action_result.get("reason", action_status),
            )

        logger.info("Recovery verification started for component=%s", component)
        try:
            verification = self._verifier.verify(component, context)
        except Exception as error:
            self._record_failure(component, "RECOVERY_UNVERIFIABLE")
            logger.exception("Recovery verification raised an error for component=%s", component)
            return self._result(
                component,
                action_status=action_status,
                verification_status="unverifiable",
                reason=str(error),
            )

        verification_status = verification["verification_status"]

        if verification_status == "verified":
            self._record_success(component)
            logger.info("Recovery verification succeeded for component=%s", component)
        else:
            outcome = (
                "RECOVERY_UNVERIFIABLE"
                if verification_status == "unverifiable"
                else "RECOVERY_VERIFICATION_FAILED"
            )
            self._record_failure(component, outcome)
            logger.warning(
                "Recovery verification failed for component=%s status=%s",
                component,
                verification_status,
            )

        return self._result(
            component,
            action_status=action_status,
            verification_status=verification_status,
            health_status=verification.get("health_status"),
            measurement=verification.get("measurement"),
            reason=verification.get("reason"),
        )

    def _result(
        self,
        component,
        action_status,
        verification_status,
        health_status=None,
        measurement=None,
        reason=None,
    ):
        state = self._get_state(component)
        result = {
            "component": component,
            "action_status": action_status,
            "verification_status": verification_status,
            "health_status": health_status,
            "attempt_number": state["attempt_count"],
            "retry_remaining": max(
                self.MAX_RECOVERY_ATTEMPTS - state["attempt_count"], 0
            ),
            "cooldown_until": state["cooldown_until"],
        }
        if measurement is not None:
            result["measurement"] = measurement
        if reason is not None:
            result["reason"] = reason
        return result

    def recover(self, component, **kwargs):
        """Dispatch a component recovery request after validating its inputs."""

        if component == "process":
            action = kwargs.get("action")
            if action == "start":
                process_name = kwargs.get("process_name")
                if not process_name:
                    return {
                        "component": "process",
                        "status": "invalid_arguments",
                    }
                recovery = ProcessRecovery(starter=self._process_starter)
                return recovery.start(process_name)

            if "pid" not in kwargs:
                return {
                    "component": "process",
                    "status": "invalid_arguments",
                }
            recovery = ProcessRecovery(starter=self._process_starter)
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
