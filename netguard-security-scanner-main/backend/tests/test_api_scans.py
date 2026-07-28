"""
API-level tests for scan creation, retrieval, and deletion.
"""


def test_list_scans_returns_seeded_data(client, auth_headers):
    response = client.get("/api/scans", headers=auth_headers)
    assert response.status_code == 200
    scans = response.json()
    assert len(scans) >= 1
    assert all("id" in s and "status" in s for s in scans)


def test_get_nonexistent_scan_returns_404(client, auth_headers):
    response = client.get("/api/scans/999999", headers=auth_headers)
    assert response.status_code == 404


def test_delete_nonexistent_scan_returns_404(client, auth_headers):
    # Regression: this endpoint previously deleted unconditionally and
    # always returned 200, even for a scan_id that didn't exist.
    response = client.delete("/api/scans/999999", headers=auth_headers)
    assert response.status_code == 404


def test_create_scan_rejects_blank_target(client, auth_headers):
    response = client.post("/api/scans", json={"target": "   ", "profile": "fast"}, headers=auth_headers)
    assert response.status_code == 422


def test_create_scan_rejects_target_with_extra_nmap_flags(client, auth_headers):
    # Regression: `target` is forwarded to the nmap CLI via
    # `shlex.split()` (see python-nmap), so a value containing a space
    # could previously smuggle in extra nmap arguments, e.g. enabling
    # NSE scripts the operator never asked for.
    response = client.post(
        "/api/scans",
        json={"target": "127.0.0.1 --script vuln", "profile": "fast"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_create_scan_rejects_target_starting_with_dash(client, auth_headers):
    response = client.post(
        "/api/scans", json={"target": "--script=vuln", "profile": "fast"}, headers=auth_headers
    )
    assert response.status_code == 422


def test_create_scan_rejects_invalid_profile(client, auth_headers):
    response = client.post(
        "/api/scans", json={"target": "192.168.1.1", "profile": "ultra-deep"}, headers=auth_headers
    )
    assert response.status_code == 422


def test_create_scan_without_auth_is_rejected(client):
    response = client.post("/api/scans", json={"target": "192.168.1.1", "profile": "fast"})
    assert response.status_code == 401


def test_create_and_delete_scan_lifecycle(client, auth_headers):
    # 127.0.0.1 resolves near-instantly, unlike a non-routable test IP, which
    # would otherwise leave a background scan thread hanging for the full
    # 30s Nmap host-timeout in CI even though this test doesn't wait on it.
    create = client.post(
        "/api/scans", json={"target": "127.0.0.1", "profile": "fast"}, headers=auth_headers
    )
    assert create.status_code == 201
    scan_id = create.json()["scan_id"]

    get_resp = client.get(f"/api/scans/{scan_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["target"] == "127.0.0.1"

    delete_resp = client.delete(f"/api/scans/{scan_id}", headers=auth_headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True

    get_after_delete = client.get(f"/api/scans/{scan_id}", headers=auth_headers)
    assert get_after_delete.status_code == 404
