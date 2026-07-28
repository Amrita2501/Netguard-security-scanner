# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.1.1] - GitHub/resume readiness pass

### Security
- **Scan target validation hardened**: `python-nmap` forwards the `target`
  field to the `nmap` CLI via `shlex.split()`, so a value containing a space
  (e.g. `"127.0.0.1 --script vuln"`) could previously smuggle extra nmap
  arguments into a scan. `ScanRequest.target` now validates against a strict
  allow-list (no whitespace, no leading `-`), covered by two new regression
  tests. All existing target formats (single IP, range, CIDR, hostname, IPv6)
  are unaffected.

### Removed
- Unused dependencies `scapy` and `pandas` from `backend/requirements.txt` -
  confirmed via `grep` that neither is imported anywhere in `app/` or `tests/`.
  Also dropped the now-unused `libcap2-bin` package from the backend
  `Dockerfile`, which was installed for a capability-granting approach the
  project never actually used (privileges are granted via
  `NET_ADMIN`/`NET_RAW` in `docker-compose.yml` instead).

### Changed
- Frontend `Dockerfile` now runs `npm ci` instead of `npm install` for
  reproducible, lockfile-exact builds.
- Corrected an inaccurate bundle-size claim: the code-splitting win in
  `[1.1.0]` below was originally logged as "~255KB gzip"; the real, verified
  number is ~255KB minified / ~84KB gzipped for the initial chunk.
- Removed `Pandas` from the README's backend technology stack list, matching
  the dependency removal above.

### Added
- Root-level `.gitignore` for OS/editor artifacts (`.DS_Store`, `.vscode/`,
  `.idea/`, etc.) not already covered by `backend/.gitignore` and
  `frontend/.gitignore`.
- This `REVIEW.md` refresh with an updated, independently re-verified score.

## [1.1.0] - Senior engineering review pass

### Added
- Structured logging throughout the backend (`app/logging_config.py`), replacing
  silent `except: pass` blocks with properly leveled debug/warning/error logs.
- Environment-variable-driven configuration (`.env.example` for both backend and
  frontend) - CORS origins, log level, session secret, SNMP community string,
  Nmap arguments, and the frontend API base URL are all now configurable.
- Full Pydantic response models wired into every API endpoint (`response_model=`),
  giving accurate auto-generated OpenAPI docs at `/docs` and response validation.
- Backend test suite (`pytest`, 43 tests): unit tests for the risk engine, CVE
  matcher, and scanner helpers, plus API-level tests covering auth, scan
  lifecycle, and host/SNMP/CVE endpoints.
- Frontend test suite (`vitest` + React Testing Library): component tests for
  `RiskBadge`, `StatusBadge`, and the new `ErrorBoundary`.
- React error boundary (`src/components/ErrorBoundary.tsx`) so an unexpected
  render error shows a recoverable screen instead of a blank white page.
- Route-based code splitting (`React.lazy`) - cut the initial JS bundle from
  ~708KB to ~255KB (minified, ~84KB gzipped), verified via `npm run build`.
- ESLint configuration (`.eslintrc.cjs`) - the `npm run lint` script existed in
  `package.json` but had no config file and did not actually run.
- Accessibility pass: `aria-label`/`aria-expanded` added to all icon-only
  buttons (menu toggle, theme toggle, account menu, topology zoom controls,
  report download/delete, password visibility toggle).
- GitHub project files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`,
  this `CHANGELOG.md`, and a GitHub Actions CI workflow.
- Global FastAPI exception handler so unhandled errors return a generic message
  instead of leaking stack traces to API clients.
- FastAPI `lifespan` context manager, replacing the deprecated `@app.on_event`
  startup hook.

### Changed
- HTTP status codes corrected: scan creation now returns `201 Created`
  (previously `200`); the delete-scan endpoint now checks existence and returns
  `404` for an unknown scan ID (previously always returned `200`, even for a
  nonexistent scan).
- `ScanRequest.profile` is now a validated `Literal["fast", "deep"]` instead of
  an unconstrained string; blank scan targets are now rejected with `422`.

### Fixed
- Removed unused imports (`json` in `database.py`, `re` in `cve_lookup.py`,
  `List` in `models.py`) and a leftover dead-code no-op block in `scanner.py`,
  found via static analysis (`pyflakes`).
- Replaced deprecated `datetime.utcnow()` (removed in a future Python version)
  with a timezone-aware equivalent in `database.py`.
- `HostOut`/`ScanOut`/etc. response models existed in `models.py` but were
  never actually used anywhere in the API - now wired in throughout.

## [1.0.0] - Cisco-focused feature expansion

### Added
- SNMP polling (`app/snmp_client.py`, SNMPv2c) for network devices - pulls
  system identity and the interface table (`IF-MIB`), validated against a
  simulated Cisco Catalyst switch profile during development.
- VLAN-aware topology: hosts carry a VLAN, and the topology graph clusters
  them by VLAN instead of a flat list.
- CVE correlation (`app/cve_lookup.py`): curated offline table of well-known
  CVEs (vsftpd backdoor, SambaCry, unauthenticated Redis, etc.) plus a
  best-effort live NVD API lookup with local caching.
- Real-time scan progress over a WebSocket (`/ws/scans/{id}`), with automatic
  fallback to REST polling if the socket can't connect.
- Docker support: `Dockerfile` for both services plus `docker-compose.yml`.

## [0.1.0] - Initial release

### Added
- FastAPI backend: Nmap-based host discovery, port/service scanning, OS
  fingerprinting, rule-based security risk scoring, PDF/CSV/JSON report
  generation, and a simple local login.
- React + TypeScript + Tailwind frontend: dashboard with charts, scan console
  with live progress, searchable host table, interactive topology graph, scan
  history, and a report center. Dark mode by default.
- Realistic seed data so the full UI is demoable without running a real scan.
