"""
Unit tests for the pure-logic helpers in app.scanner (no nmap/network needed).
"""
from app.scanner import classify_target, _map_os_family


def test_classify_single_ip():
    assert classify_target("192.168.1.10") == "single"


def test_classify_ip_range():
    assert classify_target("192.168.1.1-50") == "range"


def test_classify_cidr_subnet():
    assert classify_target("192.168.1.0/24") == "subnet"


def test_classify_strips_whitespace():
    assert classify_target("  192.168.1.10  ") == "single"


def test_map_os_family_windows():
    assert _map_os_family("Microsoft Windows 11") == "Windows"


def test_map_os_family_linux():
    assert _map_os_family("Linux 5.15") == "Linux"


def test_map_os_family_macos_variants():
    assert _map_os_family("Apple macOS 14 (Sonoma)") == "macOS"
    assert _map_os_family("Darwin 23.0") == "macOS"


def test_map_os_family_unknown_for_none_or_unrecognized():
    assert _map_os_family(None) == "Unknown"
    assert _map_os_family("") == "Unknown"
    assert _map_os_family("Some Obscure Embedded RTOS") == "Unknown"
