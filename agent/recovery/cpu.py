import inspect
import time

from agent.collectors.cpu import get_cpu_usage
from agent.config import CPU_CRITICAL_THRESHOLD, PROCESS_CPU_CRITICAL_THRESHOLD
from agent.recovery.process import ProcessRecovery


class CpuRecovery:
    """Safely relieve sustained system CPU pressure when possible."""

    def __init__(
        self,
        threshold=CPU_CRITICAL_THRESHOLD,
        process_threshold=PROCESS_CPU_CRITICAL_THRESHOLD,
        sample_interval=0.1,
        sleep_func=None,
    ):
        self.threshold = threshold
        self.process_threshold = process_threshold
        self.sample_interval = sample_interval
        self._sleep_func = sleep_func or time.sleep

    def get_cpu_processes(self, sample_interval=None):
        """Return processes ordered by their reported CPU consumption.

        Follows psutil's two-pass sampling requirement: an initial pass primes
        the CPU counters on active processes, followed by a short sample
        interval, and a second pass measures the actual CPU percentage elapsed.
        """
        procs = []
        for process in ProcessRecovery.iter_processes(["pid", "name", "create_time"]):
            try:
                # First call primes the CPU counter (psutil returns 0.0 on initial call)
                process.cpu_percent(None)
                procs.append(process)
            except ProcessRecovery.process_errors():
                continue

        if not procs:
            return []

        interval = (
            self.sample_interval
            if sample_interval is None
            else sample_interval
        )
        if interval > 0:
            self._sleep_func(interval)

        processes = []
        for process in procs:
            try:
                cpu_percent = process.cpu_percent(None)
                if cpu_percent is None:
                    continue

                info = getattr(process, "info", None) or {}
                pid = info.get("pid", getattr(process, "pid", None))
                name = info.get("name")
                if name is None and callable(getattr(process, "name", None)):
                    try:
                        name = process.name()
                    except ProcessRecovery.process_errors():
                        continue

                if pid is None or name is None:
                    continue

                proc_data = {
                    "pid": pid,
                    "name": name,
                    "cpu_percent": cpu_percent,
                }

                create_time = info.get("create_time")
                if create_time is None and callable(getattr(process, "create_time", None)):
                    try:
                        create_time = process.create_time()
                    except ProcessRecovery.process_errors():
                        create_time = None

                if create_time is not None:
                    proc_data["create_time"] = create_time

                processes.append(proc_data)
            except ProcessRecovery.process_errors():
                # Process terminated or permission denied during sampling
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

        proc_recovery = ProcessRecovery()
        call_kwargs = {}
        if "name" in candidate:
            call_kwargs["expected_name"] = candidate["name"]
        if "create_time" in candidate:
            call_kwargs["expected_create_time"] = candidate["create_time"]

        try:
            sig = inspect.signature(proc_recovery.recover)
            accepts_kwargs = any(
                p.kind == inspect.Parameter.VAR_KEYWORD
                for p in sig.parameters.values()
            )
            filtered = {
                k: v
                for k, v in call_kwargs.items()
                if accepts_kwargs or k in sig.parameters
            }
            process_result = proc_recovery.recover(candidate["pid"], **filtered)
        except TypeError:
            process_result = proc_recovery.recover(candidate["pid"])

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
