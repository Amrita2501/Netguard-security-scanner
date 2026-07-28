# NetGuard — Enterprise Network Discovery & Security Scanner

A full-stack network discovery and security assessment platform: host discovery, port/service
enumeration, OS fingerprinting, SNMP polling, VLAN-aware topology, CVE correlation, automated risk
scoring, and PDF/CSV/JSON reporting — wrapped in a modern, dark-mode dashboard.

![CI](https://github.com/ayushkumar9122006/netguard/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![React](https://img.shields.io/badge/react-18-61dafb)
![License](https://img.shields.io/badge/license-MIT-green)

> **Note:** the CI badge above assumes this repo is pushed to
> `https://github.com/Amrita2501/Netguard-security-scanner` — update the URL if you push it under a different name.

---

## Table of Contents

- [Overview](#overview)
- [Motivation](#motivation)
- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Local Development](#local-development)
- [Docker Setup](#docker-setup)
- [Usage Guide](#usage-guide)
- [Screenshots](#screenshots)
- [API Overview](#api-overview)
- [Database Schema](#database-schema)
- [Security Notes](#security-notes)
- [Testing](#testing)
- [Future Improvements](#future-improvements)
- [License](#license)
- [Author](#author)

---

## Overview

NetGuard scans a network — a single host, an IP range, or a full CIDR subnet — discovers live
devices, fingerprints their operating systems, enumerates open ports and running services, polls
SNMP-enabled network gear for device/interface info, and scores each host's security risk using a
transparent, rule-based engine. Findings are visualized on a live dashboard, mapped in an
interactive VLAN-aware topology graph, cross-referenced against known CVEs, and exportable as
polished PDF/CSV/JSON reports.

## Motivation

This project was built to demonstrate practical, applied networking and security engineering in a
full-stack context: real Nmap-based scanning and OS fingerprinting, SNMP device polling, and
security risk analysis — rather than a toy CRUD app. It doubles as a working reference for how a
FastAPI + React project can be structured with proper configuration management, structured logging,
typed API responses, and test coverage on both ends of the stack.

## Key Features

| Area | What it does |
|---|---|
| **Dashboard** | Device counts, open ports, high-risk device count, and charts (scan history, risk distribution, protocol breakdown, top ports) |
| **Network Scan** | Single IP, IP range, or CIDR subnet, with a fast or deep port profile and real-time progress over a WebSocket (falls back to REST polling) |
| **Host Discovery** | IP, hostname, MAC, vendor, OS, status, latency, last seen |
| **Port & Service Scan** | Port, protocol, service name, state, version, banner |
| **OS Fingerprinting** | Nmap OS detection mapped to Windows / Linux / macOS / Unknown with a confidence % |
| **SNMP Polling** | SNMPv2c queries against managed switches/routers/APs for system identity + interface table (`IF-MIB`) |
| **Risk Scoring** | Rule-based 0–100 score per host, bucketed LOW/MEDIUM/HIGH/CRITICAL, with concrete remediation text |
| **CVE Correlation** | Matches detected service+version against a curated offline table plus a live NVD API lookup (cached locally) |
| **VLAN-Aware Topology** | Interactive, drag/zoom/pan SVG graph clustering hosts by VLAN |
| **Search & Filters** | By hostname, IP, MAC, OS, vendor, port, service, or risk level |
| **Scan History & Reports** | Every scan persisted; export findings as PDF, CSV, or JSON |
| **Auth & Theming** | Simple local login, full dark/light mode |

## Architecture Overview

```
                 ┌──────────────────────┐        ┌───────────────────────┐
                 │   React + Vite SPA    │  REST  │   FastAPI Backend     │
                 │  (TypeScript + TW)    │◄──────►│   (Python 3.12)       │
                 └──────────────────────┘  JSON/  └───────────┬──────────┘
                          ▲                  WS                │
                          │                                    │
                          └──── real-time scan progress ────────┤
                                                                 │
                     ┌───────────────────────┬───────────────────┼───────────────────┐
                     │                       │                   │                   │
              ┌──────▼──────┐        ┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
              │ python-nmap  │        │  Risk Engine   │   │ SNMP (puresnmp)│   │ CVE Lookup    │
              │ (nmap CLI)   │        │ (rule-based)   │   │  IF-MIB polling│   │ offline + NVD │
              └─────────────┘        └───────────────┘   └───────────────┘   └───────────────┘
                                                                 │
                                                          ┌───────▼───────┐
                                                          │ SQLite (file)  │
                                                          │ scans/hosts/   │
                                                          │ ports/snmp/cve │
                                                          └───────┬───────┘
                                                                  │
                                                           ┌───────▼───────┐
                                                           │ ReportLab PDF │
                                                           │ CSV / JSON    │
                                                           └───────────────┘
```

- **Backend** (`backend/app/`): FastAPI app exposing REST + one WebSocket endpoint, with
  environment-driven configuration, structured logging, and Pydantic response models throughout.
- **Frontend** (`frontend/src/`): React + TypeScript SPA, route-based code-split, with an error
  boundary and accessible (ARIA-labeled) interactive controls.
- **Persistence**: SQLite (`backend/data/netscan.db`), created automatically on first run.

## Technology Stack

**Backend:** Python 3.12 · FastAPI · python-nmap · puresnmp (SNMPv2c) · SQLite · ReportLab ·
Uvicorn · WebSockets · python-dotenv · NVD REST API (CVE enrichment) · pytest
**Frontend:** React 18 · Vite · TypeScript · TailwindCSS · React Router · Recharts · React Icons ·
Axios · Vitest + React Testing Library
**Tooling:** ESLint · pyflakes · GitHub Actions CI · Docker + Docker Compose

## Folder Structure

```
netguard/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, routes, lifespan, exception handlers
│   │   ├── config.py          # environment-variable-driven configuration
│   │   ├── logging_config.py  # structured logging setup
│   │   ├── database.py        # SQLite schema + all query helpers
│   │   ├── models.py          # Pydantic request/response schemas
│   │   ├── scanner.py         # nmap discovery + deep scan pipeline
│   │   ├── snmp_client.py     # SNMPv2c device/interface polling
│   │   ├── risk_engine.py     # rule-based risk scoring
│   │   ├── cve_lookup.py      # offline + live NVD CVE correlation
│   │   ├── reports.py         # PDF/CSV/JSON report generation
│   │   ├── auth.py            # local login + signed session tokens
│   │   └── seed_data.py       # realistic demo dataset
│   ├── tests/                 # pytest suite (unit + API tests)
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/             # one file per route
│   │   ├── components/        # Layout, Cards, Badges, Charts, Topology, Common
│   │   ├── context/            # Auth + Theme providers
│   │   ├── api/                # axios client
│   │   └── types/              # shared TypeScript types
│   ├── package.json
│   ├── .env.example
│   └── Dockerfile
├── docs/
│   └── SETUP.md               # detailed macOS (M-series) setup guide
├── assets/screenshots/         # screenshot placeholders (see below)
├── .github/workflows/ci.yml    # lint + test + build on every push/PR
├── docker-compose.yml
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── CHANGELOG.md
└── LICENSE
```

## Installation

**Prerequisites:** Python 3.12+, Node.js 18+, and `nmap` (only required for real scans — the app
runs fully off seed data without it).

```bash
# macOS
brew install nmap
```

```bash
# Ubuntu/Debian
sudo apt-get install nmap
```

## Local Development

**Backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # optional - defaults work out of the box
uvicorn app.main:app --reload --port 8000
```
API docs (Swagger UI): `http://127.0.0.1:8000/docs`

On first run the backend creates `backend/data/netscan.db`, a default local user
(`admin`/`admin123`), and seeds one realistic demo scan so the UI isn't empty.

> Real scans need elevated privileges for Nmap OS detection (`-O`) — run with `sudo` on
> macOS/Linux, or accept less-accurate OS detection without it.

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env              # optional - defaults to http://127.0.0.1:8000/api
npm run dev
```
Open `http://localhost:5173` and log in with `admin` / `admin123`.

Full step-by-step macOS (Apple Silicon) instructions: [`docs/SETUP.md`](docs/SETUP.md).

## Docker Setup

```bash
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`

The backend container installs `nmap` and is granted `NET_ADMIN`/`NET_RAW` capabilities so
OS-detection scans work without running fully privileged. On Linux, real LAN scans work out of the
box; on macOS/Windows (Docker Desktop), container networking is more restricted, so for full
real-scan capability there, run the backend natively instead. Scan data persists in the
`netguard-data` named volume across restarts.

## Usage Guide

1. Log in (`admin` / `admin123`).
2. **Network Scan** → enter a target (`192.168.1.10`, `192.168.1.1-50`, or `192.168.1.0/24`),
   choose **Fast** or **Deep**, and start the scan — progress streams in real time.
3. **Hosts** → browse, search, and filter discovered devices by risk, OS, vendor, port, or service.
4. Click any host → view open ports, OS confidence, SNMP device info (if available), matched CVEs,
   and remediation recommendations.
5. **Topology** → drag nodes, scroll to zoom, click a host to jump to its detail page.
6. **Reports** → generate a PDF/CSV/JSON findings report for any completed scan.

## Screenshots

Screenshots depend on your own scan results and OS theme, so placeholders live in
`assets/screenshots/` rather than being committed pre-rendered. After running the app locally,
capture and drop in:

| File | Shows |
|---|---|
| `assets/screenshots/dashboard.png` | Main dashboard — stat cards + charts |
| `assets/screenshots/scan.png` | Scan console with live progress |
| `assets/screenshots/hosts.png` | Host table with search/filters |
| `assets/screenshots/host-detail.png` | Host detail — ports, SNMP, CVEs, recommendations |
| `assets/screenshots/topology.png` | Interactive VLAN-grouped topology graph |
| `assets/screenshots/reports.png` | Report generation screen |
| `assets/demo.gif` | Short screen recording of a full scan → report flow |

Using these exact filenames means they'll render automatically wherever this README is viewed.

<!--
![Dashboard](assets/screenshots/dashboard.png)
![Scan](assets/screenshots/scan.png)
![Hosts](assets/screenshots/hosts.png)
![Host Detail](assets/screenshots/host-detail.png)
![Topology](assets/screenshots/topology.png)
![Reports](assets/screenshots/reports.png)
![Demo](assets/demo.gif)
-->

## API Overview

Full interactive docs are auto-generated at `/docs` (Swagger UI) and `/redoc` once the backend is
running. Summary of the REST surface:

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/login` | Authenticate, returns a signed session token |
| GET | `/api/auth/me` | Current authenticated username |
| GET | `/api/dashboard/summary` | Device/port/risk counts for the dashboard |
| GET | `/api/dashboard/charts` | Chart data (protocols, top ports, scan history, host status) |
| POST | `/api/scans` | Start a new scan (`201 Created`) |
| GET | `/api/scans` | List all scans |
| GET | `/api/scans/{id}` | Get one scan |
| DELETE | `/api/scans/{id}` | Delete a scan (`404` if it doesn't exist) |
| GET | `/api/scans/{id}/progress` | Poll scan progress |
| GET | `/api/scans/{id}/hosts` | Hosts discovered in a scan |
| GET | `/api/hosts` / `/api/hosts/latest` | All hosts / hosts from the latest scan |
| GET | `/api/hosts/{id}` | Host detail (ports + recommendations) |
| GET | `/api/hosts/{id}/snmp` | SNMP device info + interfaces, if available |
| GET | `/api/hosts/{id}/cves` | Matched CVEs for the host's open ports |
| GET | `/api/topology/{scan_id}` | VLAN-grouped topology graph data |
| GET | `/api/reports/{scan_id}/{pdf|csv|json}` | Download a findings report |
| WS | `/ws/scans/{id}?token=...` | Real-time scan progress stream |

All endpoints except `/api/auth/login` and `/api/health` require a bearer token from login.

## Database Schema

SQLite, created automatically on first run (`backend/app/database.py`):

| Table | Key columns |
|---|---|
| `scans` | `id`, `target`, `scan_type`, `profile`, `status`, `started_at`, `finished_at`, `duration_seconds`, `total_hosts`, `live_hosts` |
| `hosts` | `id`, `scan_id` (FK), `ip_address`, `hostname`, `mac_address`, `vendor`, `os_name`, `os_family`, `os_confidence`, `status`, `latency_ms`, `risk_score`, `risk_level`, `vlan_id`, `vlan_name` |
| `ports` | `id`, `host_id` (FK), `port_number`, `protocol`, `service_name`, `state`, `version`, `banner` |
| `recommendations` | `id`, `host_id` (FK), `port_number`, `severity`, `title`, `description` |
| `snmp_info` | `id`, `host_id` (FK), `sys_descr`, `sys_name`, `sys_uptime`, `sys_contact`, `sys_location` |
| `interfaces` | `id`, `host_id` (FK), `if_index`, `if_descr`, `if_type`, `if_speed_mbps`, `if_admin_status`, `if_oper_status` |
| `cve_cache` | `id`, `service_name`, `service_version`, `cve_id`, `severity`, `cvss_score`, `source` |

All foreign keys cascade on delete (deleting a scan cleans up its hosts/ports/recommendations).

## Security Notes

This is a portfolio-grade demo, not a production-hardened deployment. See
[`SECURITY.md`](SECURITY.md) for the full breakdown, in short:

- Single local demo account (`admin`/`admin123`), stored in a local JSON file, not a full IdP.
- The session-signing secret ships with an insecure default for zero-config local use — the app
  **logs an explicit warning** at startup if it's still in use; set `NETGUARD_SESSION_SECRET` via
  `.env` before deploying anywhere reachable by others.
- No rate limiting on login — fine for local/demo use, not for a public deployment.
- Passwords are hashed (not stored/compared in plaintext); all SQL is parameterized; session
  tokens are HMAC-signed and time-limited.
- Only scan networks/hosts you own or have explicit permission to scan.

## Testing

```bash
# Backend - 45 tests (unit + API), plus static dead-code analysis
cd backend && pytest
python3 -m pyflakes app/ tests/

# Frontend - component tests + lint + type-checked build
cd frontend && npm test && npm run lint && npm run build
```

Both suites run automatically on every push/PR via [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Future Improvements

- Scan scheduling (cron-style recurring scans)
- Multi-user accounts with role-based access
- SNMP-based VLAN auto-discovery (Q-BRIDGE-MIB) instead of static VLAN assignment
- SNMPv3 support (authentication + encryption) alongside the current SNMPv2c
- Exportable topology diagrams (PNG/SVG)
- Historical trend analysis and diffing between scans
- Rate limiting on the login endpoint

## License

Released under the [MIT License](LICENSE).

## Author

**Ayush Kumar**
- GitHub: [Amrita2501](https://github.com/Amrita2501)
- LinkedIn: [amrita-kumari-b97496375](https://www.linkedin.com/in/amrita-kumari-b97496375/)
- Email: [kumari26amrita@gmail.com](mailto:kumari26amrita@gmail.com)
