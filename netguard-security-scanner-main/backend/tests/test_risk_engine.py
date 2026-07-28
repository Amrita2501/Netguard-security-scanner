"""
Unit tests for app.risk_engine - the core, dependency-free scoring logic.

These don't need the DB or network at all, so they're pure, fast unit tests.
"""
from app.risk_engine import analyze_host, score_to_level


def test_no_open_ports_is_low_risk():
    score, level, recos = analyze_host([], os_family="Linux")
    assert level == "LOW"
    assert score == 0
    assert recos == []


def test_telnet_open_is_flagged_critical_severity_recommendation():
    ports = [{"port_number": 23}]
    score, level, recos = analyze_host(ports, os_family="Linux")
    assert score > 0
    assert any(r["severity"] == "CRITICAL" for r in recos)
    assert any("Telnet" in r["title"] for r in recos)


def test_database_ports_score_higher_than_benign_ports():
    db_ports = [{"port_number": 3306}]  # MySQL
    benign_ports = [{"port_number": 53}]  # DNS
    db_score, _, _ = analyze_host(db_ports, os_family="Linux")
    benign_score, _, _ = analyze_host(benign_ports, os_family="Linux")
    assert db_score > benign_score


def test_unknown_os_adds_a_small_penalty():
    ports = [{"port_number": 80}]
    known_score, _, _ = analyze_host(ports, os_family="Linux")
    unknown_score, _, _ = analyze_host(ports, os_family="Unknown")
    assert unknown_score > known_score


def test_many_open_ports_triggers_lateral_movement_penalty():
    few_ports = [{"port_number": p} for p in [80, 443]]
    many_ports = [{"port_number": p} for p in [21, 22, 23, 80, 443, 445, 3306, 3389]]
    few_score, _, _ = analyze_host(few_ports, os_family="Linux")
    many_score, _, _ = analyze_host(many_ports, os_family="Linux")
    assert many_score > few_score


def test_score_to_level_boundaries():
    assert score_to_level(0) == "LOW"
    assert score_to_level(14) == "LOW"
    assert score_to_level(15) == "MEDIUM"
    assert score_to_level(39) == "MEDIUM"
    assert score_to_level(40) == "HIGH"
    assert score_to_level(69) == "HIGH"
    assert score_to_level(70) == "CRITICAL"
    assert score_to_level(100) == "CRITICAL"


def test_duplicate_ports_are_only_counted_once():
    ports = [{"port_number": 21}, {"port_number": 21}]
    single_score, _, single_recos = analyze_host([{"port_number": 21}], os_family="Linux")
    dup_score, _, dup_recos = analyze_host(ports, os_family="Linux")
    assert dup_score == single_score
    assert len(dup_recos) == len(single_recos)
