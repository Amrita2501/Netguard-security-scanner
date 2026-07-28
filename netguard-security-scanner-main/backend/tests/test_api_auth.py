"""
API-level tests for authentication.
"""


def test_login_with_correct_credentials_returns_token(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    body = response.json()
    assert "token" in body
    assert body["username"] == "admin"


def test_login_with_wrong_password_is_rejected(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401


def test_login_with_unknown_username_is_rejected(client):
    response = client.post("/api/auth/login", json={"username": "nobody", "password": "admin123"})
    assert response.status_code == 401


def test_login_rejects_blank_password(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": ""})
    assert response.status_code == 422  # caught by Pydantic's min_length, before auth logic runs


def test_protected_endpoint_without_token_is_unauthorized(client):
    response = client.get("/api/hosts/latest")
    assert response.status_code == 401


def test_protected_endpoint_with_garbage_token_is_unauthorized(client):
    response = client.get("/api/hosts/latest", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_protected_endpoint_with_valid_token_succeeds(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "admin"
