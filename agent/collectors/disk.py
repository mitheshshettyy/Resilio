import os

import psutil


def get_disk_usage():
    disk_path = os.path.abspath(os.sep)
    disk = psutil.disk_usage(disk_path)
    return disk.percent