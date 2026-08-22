import os

from dotenv import load_dotenv

load_dotenv()


MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "5"))