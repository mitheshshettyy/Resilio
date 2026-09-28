import os

import psutil


def get_disk_usage():
    """Return usage for the filesystem containing the operating-system root."""
    disk_path = os.path.abspath(os.sep)
    disk = psutil.disk_usage(disk_path)
    return disk.percent
