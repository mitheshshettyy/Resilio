import psutil


def get_network_info(interface_name):
    stats = psutil.net_if_stats().get(interface_name)

    if stats is None:
        return None

    counters = psutil.net_io_counters(pernic=True).get(interface_name)

    if counters is None:
        return None

    return {
        "interface": interface_name,
        "is_up": stats.isup,
        "bytes_sent": counters.bytes_sent,
        "bytes_recv": counters.bytes_recv,
        "errin": counters.errin,
        "errout": counters.errout,
        "dropin": counters.dropin,
        "dropout": counters.dropout,
    }