# Security Policy

## Project Status

NetGuard is a **portfolio/demo project**. It is functional and reasonably built,
but it has **not** undergone a formal security audit and is not intended to be
deployed as-is on a network you don't fully trust, or exposed to the public
internet. See "Known Limitations" below before using it anywhere beyond your own
local machine/LAN.

## Reporting a Vulnerability

If you find a security issue in this repository, please **do not** open a public
GitHub issue. Instead, email the maintainer directly (see the Author section in
`README.md`) with:

- A description of the issue and its potential impact
- Steps to reproduce
- Any suggested fix, if you have one

You can expect an acknowledgment within a few days. As this is a personal
portfolio project rather than a maintained production service, response times
may vary, but reports are taken seriously.

## Known Limitations (by design, for a demo project)

- **Authentication is intentionally minimal**: a single local account stored in
  a plaintext JSON file (`backend/data/users.json`), with a lightweight signed
  token rather than a full OAuth2/JWT identity provider. This is a deliberate
  scope decision for a portfolio build, not an oversight - see `README.md`.
- **Default session secret**: `NETGUARD_SESSION_SECRET` ships with an insecure
  default for zero-config local use. The app logs an explicit warning if this
  default is still in use at startup. **Set a real random secret via `.env`
  before running this anywhere reachable by other people.**
- **No rate limiting** on the login endpoint - acceptable for local/demo use,
  not for a public deployment.
- **Real network scans require elevated privileges** (root/sudo) for full Nmap
  OS-detection accuracy. Only run scans against networks/hosts you own or have
  explicit permission to scan - unauthorized scanning of third-party networks
  may be illegal in your jurisdiction.
- **SNMP uses SNMPv2c** (community-string auth, unencrypted) rather than SNMPv3
  (user-based auth + encryption). Fine for a home lab/demo; not recommended for
  a real enterprise network.

## What This Project Does Handle Reasonably

- Passwords are hashed (SHA-256) before comparison, not stored or compared in
  plaintext.
- Session tokens are HMAC-signed and time-limited, and verified on every
  protected request.
- SQL access goes through parameterized queries throughout (`app/database.py`)
  - no string-interpolated SQL.
- CORS origins, log level, and the session secret are environment-configurable
  rather than hardcoded, so a real deployment isn't stuck with demo defaults.
- Generated reports (PDF/CSV/JSON) are built from data already in the local
  database - no arbitrary file paths or user-supplied paths are ever passed to
  the filesystem layer.

## Dependency Security

Dependencies are pinned to specific versions in `requirements.txt` and
`package.json`/`package-lock.json`. The CI workflow (`.github/workflows/ci.yml`)
runs on every push; consider adding `pip-audit` / `npm audit` as a scheduled job
if you extend this project further.
