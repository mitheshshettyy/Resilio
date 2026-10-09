"""Load monitoring thresholds and targets from environment variables."""

import os
from typing import Any, Dict, Mapping, Optional

from dotenv import load_dotenv

load_dotenv()


class ConfigurationError(ValueError):
    """Raised when configuration values are invalid or malformed."""

    pass


VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})

DEFAULTS = {
    "MONITOR_INTERVAL": "5",
    "MAX_RECOVERY_ATTEMPTS": "2",
    "RECOVERY_COOLDOWN_SECONDS": "60",
    "LOG_LEVEL": "INFO",
    "CPU_WARNING_THRESHOLD": "80",
    "CPU_CRITICAL_THRESHOLD": "90",
    "MEMORY_WARNING_THRESHOLD": "70",
    "MEMORY_CRITICAL_THRESHOLD": "85",
    "DISK_WARNING_THRESHOLD": "80",
    "DISK_CRITICAL_THRESHOLD": "90",
    "PROCESS_CPU_WARNING_THRESHOLD": "80",
    "PROCESS_CPU_CRITICAL_THRESHOLD": "90",
    "PROCESS_MEMORY_WARNING_THRESHOLD": "70",
    "PROCESS_MEMORY_CRITICAL_THRESHOLD": "85",
    "PROCESS_NAME": "python.exe",
    "NETWORK_INTERFACE": "Wi-Fi",
}


def _parse_int(val: Any, name: str, min_val: Optional[int] = None) -> int:
    try:
        parsed = int(val)
    except (ValueError, TypeError):
        raise ConfigurationError(f"Invalid integer value for {name}: {val!r}")
    if min_val is not None and parsed < min_val:
        raise ConfigurationError(
            f"Invalid value for {name}: must be at least {min_val}, got {parsed}"
        )
    return parsed


def _parse_float(
    val: Any,
    name: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> float:
    try:
        parsed = float(val)
    except (ValueError, TypeError):
        raise ConfigurationError(f"Invalid numeric value for {name}: {val!r}")
    if min_val is not None and parsed < min_val:
        raise ConfigurationError(
            f"Invalid value for {name}: must be at least {min_val}, got {parsed}"
        )
    if max_val is not None and parsed > max_val:
        raise ConfigurationError(
            f"Invalid value for {name}: must be at most {max_val}, got {parsed}"
        )
    return parsed


def _parse_str(val: Any, name: str) -> str:
    if val is None or not str(val).strip():
        raise ConfigurationError(f"{name} cannot be empty")
    return str(val).strip()


def validate_config(env: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Validate and return parsed configuration values.

    Reads from the provided mapping (or os.environ if None), applying defaults
    for missing settings and verifying types, ranges, and threshold invariants.
    """
    source = os.environ if env is None else env

    def get_val(key: str) -> Any:
        if key in source and source[key] is not None:
            return source[key]
        return DEFAULTS[key]

    # Monitoring interval (> 0)
    monitor_interval = _parse_int(
        get_val("MONITOR_INTERVAL"), "MONITOR_INTERVAL", min_val=1
    )

    # Recovery limits
    max_recovery_attempts = _parse_int(
        get_val("MAX_RECOVERY_ATTEMPTS"), "MAX_RECOVERY_ATTEMPTS", min_val=1
    )
    recovery_cooldown_seconds = _parse_int(
        get_val("RECOVERY_COOLDOWN_SECONDS"), "RECOVERY_COOLDOWN_SECONDS", min_val=0
    )

    # Logging level
    raw_log_level = get_val("LOG_LEVEL")
    if raw_log_level is None or not str(raw_log_level).strip():
        raise ConfigurationError("LOG_LEVEL cannot be empty")
    log_level = str(raw_log_level).strip().upper()
    if log_level not in VALID_LOG_LEVELS:
        valid_sorted = ", ".join(sorted(VALID_LOG_LEVELS))
        raise ConfigurationError(
            f"Invalid LOG_LEVEL {log_level!r}: must be one of {valid_sorted}"
        )

    # Threshold pairs: warning must be strictly lower than critical, both in [0, 100]
    threshold_pairs = [
        ("CPU_WARNING_THRESHOLD", "CPU_CRITICAL_THRESHOLD"),
        ("MEMORY_WARNING_THRESHOLD", "MEMORY_CRITICAL_THRESHOLD"),
        ("DISK_WARNING_THRESHOLD", "DISK_CRITICAL_THRESHOLD"),
        ("PROCESS_CPU_WARNING_THRESHOLD", "PROCESS_CPU_CRITICAL_THRESHOLD"),
        ("PROCESS_MEMORY_WARNING_THRESHOLD", "PROCESS_MEMORY_CRITICAL_THRESHOLD"),
    ]

    thresholds: Dict[str, float] = {}
    for warn_key, crit_key in threshold_pairs:
        warn_val = _parse_float(get_val(warn_key), warn_key, min_val=0.0, max_val=100.0)
        crit_val = _parse_float(get_val(crit_key), crit_key, min_val=0.0, max_val=100.0)
        if warn_val >= crit_val:
            raise ConfigurationError(
                f"{warn_key} ({warn_val}) must be lower than {crit_key} ({crit_val})"
            )
        thresholds[warn_key] = warn_val
        thresholds[crit_key] = crit_val

    # String configurations
    process_name = _parse_str(get_val("PROCESS_NAME"), "PROCESS_NAME")
    network_interface = _parse_str(get_val("NETWORK_INTERFACE"), "NETWORK_INTERFACE")

    return {
        "MONITOR_INTERVAL": monitor_interval,
        "MAX_RECOVERY_ATTEMPTS": max_recovery_attempts,
        "RECOVERY_COOLDOWN_SECONDS": recovery_cooldown_seconds,
        "LOG_LEVEL": log_level,
        "CPU_WARNING_THRESHOLD": thresholds["CPU_WARNING_THRESHOLD"],
        "CPU_CRITICAL_THRESHOLD": thresholds["CPU_CRITICAL_THRESHOLD"],
        "MEMORY_WARNING_THRESHOLD": thresholds["MEMORY_WARNING_THRESHOLD"],
        "MEMORY_CRITICAL_THRESHOLD": thresholds["MEMORY_CRITICAL_THRESHOLD"],
        "DISK_WARNING_THRESHOLD": thresholds["DISK_WARNING_THRESHOLD"],
        "DISK_CRITICAL_THRESHOLD": thresholds["DISK_CRITICAL_THRESHOLD"],
        "PROCESS_CPU_WARNING_THRESHOLD": thresholds["PROCESS_CPU_WARNING_THRESHOLD"],
        "PROCESS_CPU_CRITICAL_THRESHOLD": thresholds["PROCESS_CPU_CRITICAL_THRESHOLD"],
        "PROCESS_MEMORY_WARNING_THRESHOLD": thresholds["PROCESS_MEMORY_WARNING_THRESHOLD"],
        "PROCESS_MEMORY_CRITICAL_THRESHOLD": thresholds["PROCESS_MEMORY_CRITICAL_THRESHOLD"],
        "PROCESS_NAME": process_name,
        "NETWORK_INTERFACE": network_interface,
    }


load_config = validate_config

_CONFIG = validate_config()

MONITOR_INTERVAL = _CONFIG["MONITOR_INTERVAL"]
MAX_RECOVERY_ATTEMPTS = _CONFIG["MAX_RECOVERY_ATTEMPTS"]
RECOVERY_COOLDOWN_SECONDS = _CONFIG["RECOVERY_COOLDOWN_SECONDS"]
LOG_LEVEL = _CONFIG["LOG_LEVEL"]
CPU_WARNING_THRESHOLD = _CONFIG["CPU_WARNING_THRESHOLD"]
CPU_CRITICAL_THRESHOLD = _CONFIG["CPU_CRITICAL_THRESHOLD"]
MEMORY_WARNING_THRESHOLD = _CONFIG["MEMORY_WARNING_THRESHOLD"]
MEMORY_CRITICAL_THRESHOLD = _CONFIG["MEMORY_CRITICAL_THRESHOLD"]
DISK_WARNING_THRESHOLD = _CONFIG["DISK_WARNING_THRESHOLD"]
DISK_CRITICAL_THRESHOLD = _CONFIG["DISK_CRITICAL_THRESHOLD"]
PROCESS_CPU_WARNING_THRESHOLD = _CONFIG["PROCESS_CPU_WARNING_THRESHOLD"]
PROCESS_CPU_CRITICAL_THRESHOLD = _CONFIG["PROCESS_CPU_CRITICAL_THRESHOLD"]
PROCESS_MEMORY_WARNING_THRESHOLD = _CONFIG["PROCESS_MEMORY_WARNING_THRESHOLD"]
PROCESS_MEMORY_CRITICAL_THRESHOLD = _CONFIG["PROCESS_MEMORY_CRITICAL_THRESHOLD"]
PROCESS_NAME = _CONFIG["PROCESS_NAME"]
NETWORK_INTERFACE = _CONFIG["NETWORK_INTERFACE"]
