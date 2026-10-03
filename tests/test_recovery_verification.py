from agent.recovery.verification import RecoveryVerifier


def test_cpu_verification_fails_when_cpu_remains_critical(monkeypatch):
    monkeypatch.setattr("agent.recovery.verification.get_cpu_usage", lambda: 95)

    result = RecoveryVerifier().verify("cpu")

    assert result["health_status"] == "CRITICAL"
    assert result["verification_status"] == "not_verified"


def test_cpu_verification_succeeds_when_cpu_is_warning(monkeypatch):
    monkeypatch.setattr("agent.recovery.verification.get_cpu_usage", lambda: 85)

    result = RecoveryVerifier().verify("cpu")

    assert result["health_status"] == "WARNING"
    assert result["verification_status"] == "verified"


def test_memory_verification_fails_when_memory_remains_critical(monkeypatch):
    monkeypatch.setattr("agent.recovery.verification.get_memory_usage", lambda: 95)

    result = RecoveryVerifier().verify("memory")

    assert result["health_status"] == "CRITICAL"
    assert result["verification_status"] == "not_verified"


def test_disk_verification_fails_when_disk_remains_critical(monkeypatch):
    monkeypatch.setattr("agent.recovery.verification.get_disk_usage", lambda: 95)

    result = RecoveryVerifier().verify("disk")

    assert result["health_status"] == "CRITICAL"
    assert result["verification_status"] == "not_verified"


def test_network_verification_succeeds_when_interface_is_up(monkeypatch):
    monkeypatch.setattr(
        "agent.recovery.verification.get_network_info",
        lambda interface: {"interface": interface, "is_up": True},
    )

    result = RecoveryVerifier().verify("network", {"interface": "Wi-Fi"})

    assert result["health_status"] == "HEALTHY"
    assert result["verification_status"] == "verified"


def test_network_verification_is_unverifiable_without_interface():
    result = RecoveryVerifier().verify("network")

    assert result["verification_status"] == "unverifiable"
    assert "interface" in result["reason"]


def test_process_verification_is_explicitly_unverifiable():
    result = RecoveryVerifier().verify("process", {"process_name": "python.exe"})

    assert result["verification_status"] == "unverifiable"
    assert "unsupported" in result["reason"]
