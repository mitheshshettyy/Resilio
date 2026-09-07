import psutil


class ProcessRecovery:
    """Handles recovery operations for processes."""

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