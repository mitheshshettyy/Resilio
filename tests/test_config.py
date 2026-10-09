import importlib
import pytest

import agent.config as config_module
from agent.config import ConfigurationError, validate_config


def test_config_valid_defaults():
    """Default configuration should parse without errors and have expected defaults."""
    cfg = validate_config({})
    assert cfg["MONITOR_INTERVAL"] == 5
    assert cfg["MAX_RECOVERY_ATTEMPTS"] == 2
    assert cfg["RECOVERY_COOLDOWN_SECONDS"] == 60
    assert cfg["LOG_LEVEL"] == "INFO"
    assert cfg["CPU_WARNING_THRESHOLD"] == 80.0
    assert cfg["CPU_CRITICAL_THRESHOLD"] == 90.0
    assert cfg["MEMORY_WARNING_THRESHOLD"] == 70.0
    assert cfg["MEMORY_CRITICAL_THRESHOLD"] == 85.0
    assert cfg["DISK_WARNING_THRESHOLD"] == 80.0
    assert cfg["DISK_CRITICAL_THRESHOLD"] == 90.0
    assert cfg["PROCESS_CPU_WARNING_THRESHOLD"] == 80.0
    assert cfg["PROCESS_CPU_CRITICAL_THRESHOLD"] == 90.0
    assert cfg["PROCESS_MEMORY_WARNING_THRESHOLD"] == 70.0
    assert cfg["PROCESS_MEMORY_CRITICAL_THRESHOLD"] == 85.0
    assert cfg["PROCESS_NAME"] == "python.exe"
    assert cfg["NETWORK_INTERFACE"] == "Wi-Fi"


def test_config_valid_custom_values():
    """Custom valid configuration should parse properly."""
    custom_env = {
        "MONITOR_INTERVAL": "10",
        "MAX_RECOVERY_ATTEMPTS": "3",
        "RECOVERY_COOLDOWN_SECONDS": "120",
        "LOG_LEVEL": "debug",
        "CPU_WARNING_THRESHOLD": "60.5",
        "CPU_CRITICAL_THRESHOLD": "75.0",
        "MEMORY_WARNING_THRESHOLD": "55.0",
        "MEMORY_CRITICAL_THRESHOLD": "80.0",
        "DISK_WARNING_THRESHOLD": "70",
        "DISK_CRITICAL_THRESHOLD": "85",
        "PROCESS_CPU_WARNING_THRESHOLD": "50",
        "PROCESS_CPU_CRITICAL_THRESHOLD": "70",
        "PROCESS_MEMORY_WARNING_THRESHOLD": "60",
        "PROCESS_MEMORY_CRITICAL_THRESHOLD": "75",
        "PROCESS_NAME": "custom_worker",
        "NETWORK_INTERFACE": "eth0",
    }
    cfg = validate_config(custom_env)
    assert cfg["MONITOR_INTERVAL"] == 10
    assert cfg["MAX_RECOVERY_ATTEMPTS"] == 3
    assert cfg["RECOVERY_COOLDOWN_SECONDS"] == 120
    assert cfg["LOG_LEVEL"] == "DEBUG"
    assert cfg["CPU_WARNING_THRESHOLD"] == 60.5
    assert cfg["CPU_CRITICAL_THRESHOLD"] == 75.0
    assert cfg["PROCESS_NAME"] == "custom_worker"
    assert cfg["NETWORK_INTERFACE"] == "eth0"


@pytest.mark.parametrize(
    "key,val",
    [
        ("MONITOR_INTERVAL", "abc"),
        ("MAX_RECOVERY_ATTEMPTS", "xyz"),
        ("RECOVERY_COOLDOWN_SECONDS", "ten"),
        ("CPU_WARNING_THRESHOLD", "bad_float"),
        ("MEMORY_CRITICAL_THRESHOLD", "none"),
    ],
)
def test_config_invalid_numeric_strings(key, val):
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config({key: val})
    assert key in str(exc_info.value)


@pytest.mark.parametrize(
    "key,val",
    [
        ("MONITOR_INTERVAL", "-1"),
        ("MAX_RECOVERY_ATTEMPTS", "-2"),
        ("RECOVERY_COOLDOWN_SECONDS", "-5"),
        ("CPU_WARNING_THRESHOLD", "-0.1"),
        ("MEMORY_CRITICAL_THRESHOLD", "-10"),
    ],
)
def test_config_negative_values(key, val):
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config({key: val})
    assert key in str(exc_info.value)


def test_config_zero_monitor_interval():
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config({"MONITOR_INTERVAL": "0"})
    assert "MONITOR_INTERVAL" in str(exc_info.value)


def test_config_zero_max_recovery_attempts():
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config({"MAX_RECOVERY_ATTEMPTS": "0"})
    assert "MAX_RECOVERY_ATTEMPTS" in str(exc_info.value)


@pytest.mark.parametrize(
    "warn_key,crit_key",
    [
        ("CPU_WARNING_THRESHOLD", "CPU_CRITICAL_THRESHOLD"),
        ("MEMORY_WARNING_THRESHOLD", "MEMORY_CRITICAL_THRESHOLD"),
        ("DISK_WARNING_THRESHOLD", "DISK_CRITICAL_THRESHOLD"),
        ("PROCESS_CPU_WARNING_THRESHOLD", "PROCESS_CPU_CRITICAL_THRESHOLD"),
        ("PROCESS_MEMORY_WARNING_THRESHOLD", "PROCESS_MEMORY_CRITICAL_THRESHOLD"),
    ],
)
def test_config_inverted_thresholds(warn_key, crit_key):
    # Warning > critical
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config({warn_key: "95", crit_key: "85"})
    assert "lower than" in str(exc_info.value)
    assert warn_key in str(exc_info.value)
    assert crit_key in str(exc_info.value)

    # Warning == critical (must be strictly lower)
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config({warn_key: "80", crit_key: "80"})
    assert "lower than" in str(exc_info.value)


@pytest.mark.parametrize("invalid_level", ["VERBOSE", "TRACE", "WARNINGS", "10", ""])
def test_config_invalid_log_levels(invalid_level):
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config({"LOG_LEVEL": invalid_level})
    assert "LOG_LEVEL" in str(exc_info.value)


@pytest.mark.parametrize("empty_name", ["", "   ", "\t"])
def test_config_empty_process_name(empty_name):
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config({"PROCESS_NAME": empty_name})
    assert "PROCESS_NAME" in str(exc_info.value)


@pytest.mark.parametrize("empty_interface", ["", "   "])
def test_config_empty_network_interface(empty_interface):
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config({"NETWORK_INTERFACE": empty_interface})
    assert "NETWORK_INTERFACE" in str(exc_info.value)


@pytest.mark.parametrize(
    "key,val",
    [
        ("CPU_WARNING_THRESHOLD", "101"),
        ("DISK_CRITICAL_THRESHOLD", "150"),
    ],
)
def test_config_threshold_exceeds_100(key, val):
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config({key: val})
    assert key in str(exc_info.value)
    assert "at most 100.0" in str(exc_info.value)


def test_config_error_does_not_expose_unrelated_environment_secrets():
    """Ensure error messages only describe the invalid key and don't dump other env vars."""
    secret_key = "DATABASE_PASSWORD"
    secret_val = "super_secret_value_12345"
    env = {
        secret_key: secret_val,
        "MONITOR_INTERVAL": "invalid_num",
    }
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(env)
    err_msg = str(exc_info.value)
    assert "MONITOR_INTERVAL" in err_msg
    assert secret_key not in err_msg
    assert secret_val not in err_msg


def test_config_module_reload_fails_with_invalid_env(monkeypatch):
    """Reloading agent.config with invalid environment variables raises ConfigurationError."""
    monkeypatch.setenv("MONITOR_INTERVAL", "-10")
    with pytest.raises(ValueError) as exc_info:
        importlib.reload(config_module)
    assert exc_info.type.__name__ == "ConfigurationError"
    assert "MONITOR_INTERVAL" in str(exc_info.value)

    # Clean up and reload back to clean state
    monkeypatch.delenv("MONITOR_INTERVAL", raising=False)
    importlib.reload(config_module)
