from agent.collectors.memory import get_memory_usage


class MemoryRecovery:
    """Handles recovery operations for high memory usage."""

    def __init__(self, threshold=85):
        self.threshold = threshold

    def recover(self):
        """Attempt memory recovery and verify the result."""

        before = get_memory_usage()

        # Memory usage is below the recovery threshold.
        if before < self.threshold:
            return {
                "component": "memory",
                "status": "not_required",
                "before": before,
                "after": before,
            }

        # Perform safe memory cleanup.
        self.reclaim()

        # Measure memory again after recovery.
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
        """Perform safe memory cleanup."""

        # Python garbage collection releases unused Python objects.
        import gc

        gc.collect()