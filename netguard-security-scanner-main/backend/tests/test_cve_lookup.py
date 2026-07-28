"""
Unit tests for app.cve_lookup's offline matching logic.

Several of these are direct regression tests for real bugs found and fixed
during development:
  - a generic service name ("ftp") was falsely matching a specific
    software rule ("vsftpd"), and
  - a rule keyed on the actual software name ("samba") failed to match
    when that name only appeared in the version string, not service_name.
"""
from app.cve_lookup import _offline_matches


def test_generic_ftp_does_not_match_vsftpd_rule():
    # Regression: a bidirectional substring check previously let the
    # generic "ftp" service name incorrectly match the specific vsftpd CVE.
    assert _offline_matches("ftp", "2.3.4") == []


def test_vsftpd_version_string_matches_backdoor_cve():
    matches = _offline_matches("ftp", "vsftpd 2.3.4")
    ids = [m["cve_id"] for m in matches]
    assert "CVE-2011-2523" in ids


def test_samba_matches_even_when_only_in_version_field():
    # Regression: nmap reports the generic "netbios-ssn"/"microsoft-ds" as
    # service_name; "Samba" only appears in the version string.
    matches = _offline_matches("netbios-ssn", "Samba 3.6")
    ids = [m["cve_id"] for m in matches]
    assert "CVE-2017-7494" in ids


def test_telnet_always_flagged():
    matches = _offline_matches("telnet", "BusyBox telnetd")
    assert any(m["cve_id"] == "CVE-1999-0619" for m in matches)


def test_unrelated_service_has_no_matches():
    assert _offline_matches("http", "nginx 1.25.0") == []


def test_mysql_version_prefix_is_specific_not_generic():
    # Only the curated 8.0.1x rule should match - a newer, unrelated
    # MySQL version should not be flagged by this offline heuristic.
    assert _offline_matches("mysql", "MySQL 8.0.34") == []
    matches = _offline_matches("mysql", "MySQL 8.0.15")
    assert any(m["cve_id"] == "CVE-2021-2154" for m in matches)
