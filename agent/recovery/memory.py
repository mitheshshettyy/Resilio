from agent.collectors.memory import get_memory_usage
from agent.config import MEMORY_CRITICAL_THRESHOLD


class MemoryRecovery:
    """Handles recovery operations for high memory usage."""

    def __init__(self, threshold=MEMORY_CRITICAL_THRESHOLD):
        self.threshold = threshold

    def recover(self):
        """Attempt memory recovery and verify the result."""

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
        """Release unreachable Python objects without touching other processes."""

        import gc

        gc.collect()
