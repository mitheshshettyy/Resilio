from agent.recovery.network import NetworkRecovery


def test_network_recovery_reports_missing_interface(monkeypatch):
    monkeypatch.setattr("agent.recovery.network.get_network_info", lambda interface: None)

    result = NetworkRecovery().recover("Wi-Fi")

    assert result == {
        "component": "network",
        "status": "interface_missing",
        "interface": "Wi-Fi",
    }


def test_network_recovery_not_required_when_interface_is_up(monkeypatch):
    info = {"interface": "Wi-Fi", "is_up": True}
    monkeypatch.setattr("agent.recovery.network.get_network_info", lambda interface: info)

    result = NetworkRecovery().recover("Wi-Fi")

    assert result["status"] == "not_required"


def test_network_recovery_is_unavailable_without_platform_action(monkeypatch):
    info = {"interface": "Wi-Fi", "is_up": False}
    monkeypatch.setattr("agent.recovery.network.get_network_info", lambda interface: info)

    result = NetworkRecovery().recover("Wi-Fi")

    assert result["status"] == "recovery_unavailable"


def test_network_recovery_restarts_and_verifies_interface(monkeypatch):
    infos = iter([
        {"interface": "Wi-Fi", "is_up": False},
        {"interface": "Wi-Fi", "is_up": True},
    ])
    restarted = []
    monkeypatch.setattr(
        "agent.recovery.network.get_network_info", lambda interface: next(infos)
    )

    result = NetworkRecovery(
        restart_interface=lambda interface: restarted.append(interface) is None
    ).recover("Wi-Fi")

    assert restarted == ["Wi-Fi"]
    assert result["status"] == "recovered"
    assert result["after"]["is_up"] is True


def test_network_recovery_handles_permission_denied(monkeypatch):
    monkeypatch.setattr(
        "agent.recovery.network.get_network_info",
        lambda interface: {"interface": interface, "is_up": False},
    )

    def denied_restart(interface):
        raise PermissionError

    result = NetworkRecovery(restart_interface=denied_restart).recover("Wi-Fi")

    assert result["status"] == "permission_denied"


def test_network_recovery_reports_failed_verification(monkeypatch):
    infos = iter([
        {"interface": "Wi-Fi", "is_up": False},
        {"interface": "Wi-Fi", "is_up": False},
    ])
    monkeypatch.setattr(
        "agent.recovery.network.get_network_info", lambda interface: next(infos)
    )

    result = NetworkRecovery(restart_interface=lambda interface: True).recover("Wi-Fi")

    assert result["status"] == "recovery_failed"
