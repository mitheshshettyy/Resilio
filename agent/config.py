import os

from dotenv import load_dotenv

load_dotenv()


MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "5"))

CPU_WARNING_THRESHOLD = float(
    os.getenv("CPU_WARNING_THRESHOLD", "80")
)

CPU_CRITICAL_THRESHOLD = float(
    os.getenv("CPU_CRITICAL_THRESHOLD", "90")
)