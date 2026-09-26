from agent.health import get_network_status
from agent.collectors.network import get_network_info
from unittest.mock import patch

def test_network_status_critical_when_interface_missing():
    assert get_network_status(None) == "CRITICAL"


def test_network_status_critical_when_interface_down():
    network_info = {"is_up": False}

    assert get_network_status(network_info) == "CRITICAL"


def test_network_status_healthy_when_interface_up():
    network_info = {"is_up": True}

    assert get_network_status(network_info) == "HEALTHY"


def test_get_network_info():
    mock_stats = type("Stats", (), {"isup": True})()
    mock_counters = type(
        "Counters",
        (),
        {
            "bytes_sent": 1000,
            "bytes_recv": 2000,
            "errin": 0,
            "errout": 0,
            "dropin": 0,
            "dropout": 0,
        },
    )()

    with patch("agent.collectors.network.psutil.net_if_stats") as mock_stats_func:
        with patch(
            "agent.collectors.network.psutil.net_io_counters"
        ) as mock_counters_func:

            mock_stats_func.return_value = {"Wi-Fi": mock_stats}
            mock_counters_func.return_value = {"Wi-Fi": mock_counters}

            result = get_network_info("Wi-Fi")

            assert result["interface"] == "Wi-Fi"
            assert result["is_up"] is True
            assert result["bytes_sent"] == 1000
            assert result["bytes_recv"] == 2000


def test_get_network_info_when_counters_missing():
    mock_stats = type("Stats", (), {"isup": True})()

    with patch("agent.collectors.network.psutil.net_if_stats") as mock_stats_func:
        with patch(
            "agent.collectors.network.psutil.net_io_counters"
        ) as mock_counters_func:

            mock_stats_func.return_value = {"Wi-Fi": mock_stats}
            mock_counters_func.return_value = {}

            result = get_network_info("Wi-Fi")

            assert result is None


def test_get_network_info_when_interface_missing():
    with patch("agent.collectors.network.psutil.net_if_stats", return_value={}):
        assert get_network_info("Wi-Fi") is None
