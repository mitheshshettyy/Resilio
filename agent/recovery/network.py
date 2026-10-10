from agent.collectors.network import get_network_info


class NetworkRecovery:
    """Coordinates an optional, platform-specific network recovery action."""

    def __init__(self, restart_interface=None):
        self.restart_interface = restart_interface

    def recover(self, interface_name):
        """Recover a known interface and verify that it is up afterwards."""
        before = get_network_info(interface_name)

        if before is None:
            return self._result("interface_missing", interface_name)

        if before["is_up"]:
            return self._result("not_required", interface_name, before, before)

        if self.restart_interface is None:
            return self._result("recovery_unavailable", interface_name, before, before)

        try:
            restart_succeeded = self.restart_interface(interface_name)
        except PermissionError:
            return self._result("permission_denied", interface_name, before, before)
        except Exception as error:
            return self._result(
                "recovery_failed", interface_name, before, before, str(error)
            )

        after = get_network_info(interface_name)
        if restart_succeeded and after is not None and after["is_up"]:
            return self._result("recovered", interface_name, before, after)

        return self._result("recovery_failed", interface_name, before, after)

    @staticmethod
    def _result(status, interface, before=None, after=None, reason=None):
        result = {
            "component": "network",
            "status": status,
            "interface": interface,
        }
        if before is not None:
            result["before"] = before
        if after is not None:
            result["after"] = after
        if reason is not None:
            result["reason"] = reason
        return result
