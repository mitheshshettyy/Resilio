import psutil


class ProcessRecovery:
    """Handles recovery operations for processes."""

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
        """Select the highest-memory process that is safe to recover."""
        if protected_names is None:
            protected_names = {
                "System",
                "System Idle Process",
                "Registry",
                "smss.exe",
                "csrss.exe",
                "wininit.exe",
                "services.exe",
                "lsass.exe",
            }

        protected_names = {
            name.lower() for name in protected_names
        }

        current_pid = psutil.Process().pid

        for process in processes:
            pid = process.get("pid")
            name = process.get("name")

            if pid is None or name is None:
                continue

            if pid == current_pid:
                continue

            if name.lower() in protected_names:
                continue

            return process

        return None

    def recover(self, pid):
        """Terminate the process and verify that it stopped."""
        try:
            process = psutil.Process(pid)
            process.terminate()
            process.wait(timeout=5)

            return {
                "pid": pid,
                "status": "recovered",
            }

        except psutil.NoSuchProcess:
            return {
                "pid": pid,
                "status": "not_found",
            }

        except psutil.AccessDenied:
            return {
                "pid": pid,
                "status": "access_denied",
            }

        except psutil.TimeoutExpired:
            return {
                "pid": pid,
                "status": "recovery_failed",
            }