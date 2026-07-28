"""
API-level tests for host data, SNMP info, and CVE correlation endpoints.

These rely on the seeded demo dataset (see app/seed_data.py), which
deliberately includes a known-vulnerable legacy host and one simulated
SNMP-enabled switch, so the tests can assert on real, specific findings
rather than just "the endpoint returns 200".
"""


def _get_latest_hosts(client, auth_headers):
    response = client.get("/api/hosts/latest", headers=auth_headers)
    assert response.status_code == 200
    return response.json()


def test_latest_hosts_includes_seeded_demo_data(client, auth_headers):
    hosts = _get_latest_hosts(client, auth_headers)
    ips = [h["ip_address"] for h in hosts]
    assert "192.168.1.22" in ips  # the intentionally-vulnerable legacy NAS


def test_host_detail_includes_ports_and_recommendations(client, auth_headers):
    hosts = _get_latest_hosts(client, auth_headers)
    legacy_host = next(h for h in hosts if h["ip_address"] == "192.168.1.22")

    response = client.get(f"/api/hosts/{legacy_host['id']}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] in ("HIGH", "CRITICAL")
    assert len(body["ports"]) > 0
    assert len(body["recommendations"]) > 0


def test_host_detail_404_for_unknown_id(client, auth_headers):
    response = client.get("/api/hosts/999999", headers=auth_headers)
    assert response.status_code == 404


def test_cve_endpoint_finds_known_vulnerability_on_legacy_host(client, auth_headers):
    hosts = _get_latest_hosts(client, auth_headers)
    legacy_host = next(h for h in hosts if h["ip_address"] == "192.168.1.22")

    response = client.get(f"/api/hosts/{legacy_host['id']}/cves", headers=auth_headers)
    assert response.status_code == 200
    findings = response.json()["findings"]
    all_cve_ids = [c["cve_id"] for f in findings for c in f["cves"]]
    assert "CVE-2011-2523" in all_cve_ids  # vsftpd 2.3.4 backdoor


def test_cve_endpoint_empty_for_clean_host(client, auth_headers):
    hosts = _get_latest_hosts(client, auth_headers)
    macbook = next(h for h in hosts if h["ip_address"] == "192.168.1.42")

    response = client.get(f"/api/hosts/{macbook['id']}/cves", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["findings"] == []


def test_snmp_endpoint_available_for_simulated_switch(client, auth_headers):
    hosts = _get_latest_hosts(client, auth_headers)
    switch = next(h for h in hosts if h["ip_address"] == "192.168.1.2")

    response = client.get(f"/api/hosts/{switch['id']}/snmp", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["info"]["sys_name"] == "core-switch-01"
    assert len(body["interfaces"]) > 0


def test_snmp_endpoint_unavailable_for_non_snmp_host(client, auth_headers):
    hosts = _get_latest_hosts(client, auth_headers)
    macbook = next(h for h in hosts if h["ip_address"] == "192.168.1.42")

    response = client.get(f"/api/hosts/{macbook['id']}/snmp", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["info"] is None


def test_topology_groups_hosts_by_vlan(client, auth_headers):
    scans = client.get("/api/scans", headers=auth_headers).json()
    seeded_scan = max(scans, key=lambda s: s["total_hosts"])

    response = client.get(f"/api/topology/{seeded_scan['id']}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    vlan_nodes = [n for n in body["nodes"] if n["type"] == "vlan"]
    assert len(vlan_nodes) >= 2  # seeded data spans multiple VLANs
