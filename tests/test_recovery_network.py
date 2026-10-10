import subprocess
import pytest

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


def test_network_recovery_handles_called_process_error(monkeypatch):
    monkeypatch.setattr(
        "agent.recovery.network.get_network_info",
        lambda interface: {"interface": interface, "is_up": False},
    )

    def failing_restart(interface):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=["netsh", "interface", "set", "interface", interface, "admin=enable"],
        )

    result = NetworkRecovery(restart_interface=failing_restart).recover("Wi-Fi")

    assert result["status"] == "recovery_failed"
    assert "netsh" in result["reason"]
    assert result["interface"] == "Wi-Fi"
    assert result["before"]["is_up"] is False
    assert result["after"]["is_up"] is False


def test_network_recovery_handles_runtime_error(monkeypatch):
    monkeypatch.setattr(
        "agent.recovery.network.get_network_info",
        lambda interface: {"interface": interface, "is_up": False},
    )

    def failing_restart(interface):
        raise RuntimeError("restart command timed out")

    result = NetworkRecovery(restart_interface=failing_restart).recover("Wi-Fi")

    assert result["status"] == "recovery_failed"
    assert result["reason"] == "restart command timed out"
    assert result["interface"] == "Wi-Fi"


def test_network_recovery_propagates_base_exception(monkeypatch):
    monkeypatch.setattr(
        "agent.recovery.network.get_network_info",
        lambda interface: {"interface": interface, "is_up": False},
    )

    def fatal_restart(interface):
        raise KeyboardInterrupt()

    recovery = NetworkRecovery(restart_interface=fatal_restart)
    with pytest.raises(KeyboardInterrupt):
        recovery.recover("Wi-Fi")
