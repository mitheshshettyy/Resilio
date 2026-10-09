from agent.collectors.memory import get_memory_usage
from agent.config import MEMORY_CRITICAL_THRESHOLD


class MemoryRecovery:
    """Handles recovery operations for high memory usage.

    Behavior and Limitations:
    - Memory recovery runs in-process Python runtime garbage collection (`gc.collect()`)
      to reclaim unreachable cyclic objects within the agent's own execution space.
    - It intentionally does NOT terminate arbitrary external processes, drop kernel
      page caches, or manipulate operating system virtual memory / swap.
    - System-wide memory pressure caused by other applications cannot be resolved
      by runtime garbage collection. In such scenarios, post-recovery verification
      observes no reduction (`after >= before`) and safely reports `recovery_failed`,
      allowing the RecoveryManager to enforce bounded retries and cooldown.
    """

    def __init__(self, threshold=MEMORY_CRITICAL_THRESHOLD):
        self.threshold = threshold

    def recover(self):
        """Attempt in-process memory reclamation and verify the result.

        If system memory usage is below the critical threshold, recovery is
        reported as `not_required`. Otherwise, in-process garbage collection is
        executed and host memory is re-evaluated. If host memory usage does not
        strictly decrease (`after < before`), `recovery_failed` is reported.
        """
        before = get_memory_usage()

        if before < self.threshold:
            return {
                "component": "memory",
                "status": "not_required",
                "before": before,
                "after": before,
            }

        self.reclaim()

        # Recovery success requires an observed reduction, not just a successful call.
        after = get_memory_usage()

        if after < before:
            status = "recovered"
        else:
            status = "recovery_failed"

        return {
            "component": "memory",
            "status": status,
            "before": before,
            "after": after,
        }

    def reclaim(self):
        """Release unreachable Python objects in the agent runtime.

        Executes `gc.collect()` within the current Python interpreter. This
        action is non-destructive and strictly isolated to the agent's memory
        space without affecting other processes or operating system memory.
        """
        import gc

        gc.collect()
