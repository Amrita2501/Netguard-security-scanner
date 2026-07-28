"""
Minimal local authentication.

This is intentionally simple: the assignment calls for "a simple login
page, username/password, store user locally" for a portfolio demo -
not a production identity system. Credentials live in a local JSON
file (created on first run with a default demo account) and a signed,
time-limited token is issued on login. The token is verified on every
protected request via the `require_auth` dependency.

NOTE: This is NOT hardened for production use (no bcrypt work factor
tuning, no refresh-token rotation, no rate limiting). For a real
deployment, swap this module for OAuth2 / a proper IdP.
"""
import json
import os
import hmac
import hashlib
import time
import base64

from fastapi import Header, HTTPException, status

from app.config import AUTH_FILE, SESSION_SECRET, TOKEN_TTL_SECONDS

DEFAULT_USER = {
    "username": "admin",
    # sha256("admin123") - demo password, shown in README
    "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
    "full_name": "Network Administrator",
}


def _ensure_user_file():
    if not os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "w") as f:
            json.dump([DEFAULT_USER], f, indent=2)


def _load_users():
    _ensure_user_file()
    with open(AUTH_FILE) as f:
        return json.load(f)


def _sign(payload: str) -> str:
    sig = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return sig


def create_token(username: str) -> str:
    expires = int(time.time()) + TOKEN_TTL_SECONDS
    payload = f"{username}:{expires}"
    sig = _sign(payload)
    raw = f"{payload}:{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def verify_token(token: str):
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        username, expires, sig = raw.split(":")
        expected_sig = _sign(f"{username}:{expires}")
        if not hmac.compare_digest(sig, expected_sig):
            return None
        if int(expires) < time.time():
            return None
        return username
    except Exception:
        return None


def authenticate(username: str, password: str):
    users = _load_users()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    for user in users:
        if user["username"] == username and hmac.compare_digest(user["password_hash"], password_hash):
            return user
    return None


def require_auth(authorization: str = Header(default=None)):
    """FastAPI dependency: raises 401 if the bearer token is missing/invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return username
