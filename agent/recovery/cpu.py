from agent.collectors.cpu import get_cpu_usage
from agent.config import CPU_CRITICAL_THRESHOLD, PROCESS_CPU_CRITICAL_THRESHOLD
from agent.recovery.process import ProcessRecovery


class CpuRecovery:
    """Safely relieve sustained system CPU pressure when possible."""

    def __init__(
        self,
        threshold=CPU_CRITICAL_THRESHOLD,
        process_threshold=PROCESS_CPU_CRITICAL_THRESHOLD,
    ):
        self.threshold = threshold
        self.process_threshold = process_threshold

    def get_cpu_processes(self):
        """Return processes ordered by their reported CPU consumption."""
        processes = []

        for process in ProcessRecovery.iter_processes(["pid", "name", "cpu_percent"]):
            try:
                info = process.info
                cpu_percent = info.get("cpu_percent")

                if cpu_percent is None:
                    continue

                processes.append(
                    {
                        "pid": info.get("pid"),
                        "name": info.get("name"),
                        "cpu_percent": cpu_percent,
                    }
                )
            except ProcessRecovery.process_errors():
                continue

        return sorted(
            processes,
            key=lambda process: process["cpu_percent"],
            reverse=True,
        )

    def recover(self):
        """Recover only by terminating a verified, safe high-CPU process."""
        before = get_cpu_usage()

        if before < self.threshold:
            return self._result("not_required", before, before)

        candidates = [
            process
            for process in self.get_cpu_processes()
            if process["cpu_percent"] >= self.process_threshold
        ]
        candidate = ProcessRecovery().select_recovery_candidate(candidates)

        if candidate is None:
            return self._result("no_safe_candidate", before, before)

        process_result = ProcessRecovery().recover(candidate["pid"])
        after = get_cpu_usage()

        if process_result["status"] == "recovered" and after < before:
            return self._result("recovered", before, after, candidate["pid"])

        return self._result(
            "recovery_failed",
            before,
            after,
            candidate["pid"],
            reason=process_result["status"],
        )

    @staticmethod
    def _result(status, before, after, pid=None, reason=None):
        result = {
            "component": "cpu",
            "status": status,
            "before": before,
            "after": after,
        }
        if pid is not None:
            result["pid"] = pid
        if reason is not None:
            result["reason"] = reason
        return result
