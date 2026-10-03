"""Load monitoring thresholds and targets from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "5"))

MAX_RECOVERY_ATTEMPTS = int(os.getenv("MAX_RECOVERY_ATTEMPTS", "2"))

RECOVERY_COOLDOWN_SECONDS = int(
    os.getenv("RECOVERY_COOLDOWN_SECONDS", "60")
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

CPU_WARNING_THRESHOLD = float(
    os.getenv("CPU_WARNING_THRESHOLD", "80")
)

CPU_CRITICAL_THRESHOLD = float(
    os.getenv("CPU_CRITICAL_THRESHOLD", "90")
)

MEMORY_WARNING_THRESHOLD = float(
    os.getenv("MEMORY_WARNING_THRESHOLD", "70")
)

MEMORY_CRITICAL_THRESHOLD = float(
    os.getenv("MEMORY_CRITICAL_THRESHOLD", "85")
)

DISK_WARNING_THRESHOLD = float(
    os.getenv("DISK_WARNING_THRESHOLD", "80")
)

DISK_CRITICAL_THRESHOLD = float(
    os.getenv("DISK_CRITICAL_THRESHOLD", "90")
)

PROCESS_CPU_WARNING_THRESHOLD = float(
    os.getenv("PROCESS_CPU_WARNING_THRESHOLD", "80")
)

PROCESS_CPU_CRITICAL_THRESHOLD = float(
    os.getenv("PROCESS_CPU_CRITICAL_THRESHOLD", "90")
)

PROCESS_MEMORY_WARNING_THRESHOLD = float(
    os.getenv("PROCESS_MEMORY_WARNING_THRESHOLD", "70")
)

PROCESS_MEMORY_CRITICAL_THRESHOLD = float(
    os.getenv("PROCESS_MEMORY_CRITICAL_THRESHOLD", "85")
)

PROCESS_NAME = os.getenv("PROCESS_NAME", "python.exe")

NETWORK_INTERFACE = os.getenv("NETWORK_INTERFACE", "Wi-Fi")
