from agent.health import get_network_status


def test_network_status_critical_when_interface_missing():
    assert get_network_status(None) == "CRITICAL"


def test_network_status_critical_when_interface_down():
    network_info = {"is_up": False}

    assert get_network_status(network_info) == "CRITICAL"


def test_network_status_healthy_when_interface_up():
    network_info = {"is_up": True}

    assert get_network_status(network_info) == "HEALTHY"