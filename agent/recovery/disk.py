from agent.collectors.disk import get_disk_usage
from agent.config import DISK_CRITICAL_THRESHOLD


class DiskRecovery:
    """Coordinates only explicitly supplied, safe disk cleanup actions.

    Resilio has no application-owned storage location, so its default policy is
    deliberately non-destructive. A future deployment may supply a cleanup
    callable for a known, managed location.
    """

    def __init__(self, threshold=DISK_CRITICAL_THRESHOLD, cleanup=None):
        self.threshold = threshold
        self.cleanup = cleanup

    def recover(self):
        """Run a managed cleanup action and verify disk usage afterwards."""
        before = get_disk_usage()

        if before < self.threshold:
            return self._result("not_required", before, before)

        if self.cleanup is None:
            return self._result("recovery_unavailable", before, before)

        try:
            cleanup_succeeded = self.cleanup()
        except Exception as error:
            return self._result("recovery_failed", before, before, str(error))

        after = get_disk_usage()
        if cleanup_succeeded and after < before:
            return self._result("recovered", before, after)

        return self._result("recovery_failed", before, after)

    @staticmethod
    def _result(status, before, after, reason=None):
        result = {
            "component": "disk",
            "status": status,
            "before": before,
            "after": after,
        }
        if reason is not None:
            result["reason"] = reason
        return result
