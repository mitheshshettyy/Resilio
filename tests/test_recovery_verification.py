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


def test_process_verification_succeeds_when_terminated_pid_is_gone(monkeypatch):
    verifier = RecoveryVerifier(pid_exists_func=lambda pid: False)
    monkeypatch.setattr(
        "agent.recovery.verification.get_process_info", lambda name: None
    )

    result = verifier.verify("process", {"target_pid": 1234, "process_name": "python.exe"})

    assert result["verification_status"] == "verified"


def test_process_verification_fails_when_target_pid_still_exists():
    verifier = RecoveryVerifier(pid_exists_func=lambda pid: True)

    result = verifier.verify("process", {"target_pid": 1234, "process_name": "python.exe"})

    assert result["verification_status"] == "not_verified"
    assert "1234" in result["reason"]
    assert "still running" in result["reason"]


def test_process_verification_succeeds_when_replacement_process_is_healthy(monkeypatch):
    verifier = RecoveryVerifier(pid_exists_func=lambda pid: False)
    monkeypatch.setattr(
        "agent.recovery.verification.get_process_info",
        lambda name: {"pid": 5678, "name": name, "cpu_percent": 10, "memory_percent": 10},
    )

    result = verifier.verify("process", {"target_pid": 1234, "process_name": "python.exe"})

    assert result["verification_status"] == "verified"
    assert result["health_status"] == "HEALTHY"
    assert result["measurement"]["pid"] == 5678


def test_process_verification_fails_when_replacement_process_is_critical(monkeypatch):
    verifier = RecoveryVerifier(pid_exists_func=lambda pid: False)
    monkeypatch.setattr(
        "agent.recovery.verification.get_process_info",
        lambda name: {"pid": 5678, "name": name, "cpu_percent": 99, "memory_percent": 90},
    )

    result = verifier.verify("process", {"target_pid": 1234, "process_name": "python.exe"})

    assert result["verification_status"] == "not_verified"
    assert result["health_status"] == "CRITICAL"
    assert "CRITICAL" in result["reason"]


def test_process_verification_handles_missing_process_name_or_pid():
    verifier = RecoveryVerifier()

    result = verifier.verify("process", {})

    assert result["verification_status"] == "unverifiable"
    assert "requires target_pid or process_name" in result["reason"]
