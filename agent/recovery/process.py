import os

import psutil


PROTECTED_PROCESS_NAMES = {
    "system",
    "system idle process",
    "registry",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "services.exe",
    "lsass.exe",
    "winlogon.exe",
    "fontdrvhost.exe",
    "dwm.exe",
}


class ProcessRecovery:
    """Handles recovery operations for processes."""

    @staticmethod
    def iter_processes(attributes):
        """Provide an overridable process iterator for recovery discovery."""
        return psutil.process_iter(attributes)

    @staticmethod
    def process_errors():
        """Return transient errors expected while inspecting processes."""
        return (psutil.NoSuchProcess, psutil.AccessDenied)

    def get_memory_processes(self):
        """Return running processes ordered by memory usage."""
        processes = []

        for process in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                memory_info = process.info["memory_info"]

                if memory_info is None:
                    continue

                processes.append(
                    {
                        "pid": process.info["pid"],
                        "name": process.info["name"],
                        "memory_mb": round(
                            memory_info.rss / (1024 * 1024), 2
                        ),
                    }
                )

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return sorted(
            processes,
            key=lambda process: process["memory_mb"],
            reverse=True,
        )

    def select_recovery_candidate(self, processes, protected_names=None):
        """Select the first safe process from a caller-ordered candidate list."""
        if protected_names is None:
            protected_names = PROTECTED_PROCESS_NAMES

        protected_names = {
            name.lower() for name in protected_names
        }

        current_pid = os.getpid()

        for process in processes:
            pid = process.get("pid")
            name = process.get("name")

            if not isinstance(pid, int) or not isinstance(name, str):
                continue

            if pid == current_pid:
                continue

            if name.lower() in protected_names:
                continue

            return process

        return None

    def recover(self, pid):
        """Terminate a validated non-system process and verify that it stopped."""
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
            return self._result(pid, "invalid_pid")

        if pid == os.getpid():
            return self._result(pid, "current_process")

        try:
            process = psutil.Process(pid)

            if process.name().lower() in PROTECTED_PROCESS_NAMES:
                return self._result(pid, "protected_process")

            process.terminate()
            process.wait(timeout=5)

            return self._result(pid, "recovered")

        except psutil.NoSuchProcess:
            return self._result(pid, "not_found")

        except psutil.AccessDenied:
            return self._result(pid, "access_denied")

        except psutil.TimeoutExpired:
            return self._result(pid, "recovery_failed")

    @staticmethod
    def _result(pid, status):
        return {
            "component": "process",
            "pid": pid,
            "status": status,
        }
