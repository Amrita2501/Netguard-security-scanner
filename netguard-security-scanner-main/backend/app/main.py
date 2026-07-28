"""
Enterprise Network Discovery & Security Scanner - API entrypoint.

Run with:
    uvicorn app.main:app --reload --port 8000

See docs/SETUP.md for full macOS setup instructions (nmap install, venv, etc).
Configuration is environment-variable driven - see .env.example and app/config.py.
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Response, Request, status
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import database as db
from app import auth
from app import scanner
from app import reports
from app import cve_lookup
from app.logging_config import configure_logging
from app.seed_data import seed_if_empty
from app.config import CORS_ORIGINS, LOG_LEVEL
from app.models import (
    LoginRequest, LoginResponse, ScanRequest, ScanCreatedResponse, ScanOut,
    ScanProgressOut, DeleteResponse, HostOut, HostDetailOut, SnmpResponseOut,
    CveResponseOut, TopologyOut, DashboardSummaryOut, DashboardChartsOut,
    ErrorResponse,
)

configure_logging(LOG_LEVEL)
logger = logging.getLogger("netguard.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup: ensure schema exists and the demo dataset is seeded.
    logger.info("Starting up - initializing database")
    db.init_db()
    seed_if_empty()
    logger.info("Startup complete")
    yield
    # Shutdown: nothing to clean up today (SQLite connections are opened
    # per-request via a context manager in database.py), but the hook is
    # here so future resources (e.g. a connection pool) have a clear home.
    logger.info("Shutting down")


app = FastAPI(
    title="Enterprise Network Discovery & Security Scanner",
    description="Full-stack network discovery, port/service/OS fingerprinting, "
                "and security risk analysis platform.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Lightweight request/response logging: method, path, status, latency."""
    started = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - started) * 1000, 1)
    logger.info(
        "%s %s -> %d (%.1fms)", request.method, request.url.path, response.status_code, duration_ms
    )
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for anything not already raised as an HTTPException.
    Logs the full traceback server-side but returns a generic message to
    the client - we don't want internal error details (stack traces, SQL,
    file paths) leaking into API responses.
    """
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again."},
    )


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.post("/api/auth/login", response_model=LoginResponse, responses={401: {"model": ErrorResponse}})
def login(payload: LoginRequest):
    user = auth.authenticate(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token = auth.create_token(user["username"])
    return LoginResponse(token=token, username=user["username"], full_name=user["full_name"])


@app.get("/api/auth/me")
def me(username: str = Depends(auth.require_auth)):
    return {"username": username}


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.get("/api/dashboard/summary", response_model=DashboardSummaryOut)
def dashboard_summary(username: str = Depends(auth.require_auth)):
    hosts = db.get_latest_hosts()
    scans = db.list_scans(limit=1)
    latest_scan = scans[0] if scans else None

    total_devices = len(hosts)
    live_hosts = sum(1 for h in hosts if h["status"] == "online")
    offline_hosts = total_devices - live_hosts

    total_ports = 0
    high_risk = 0
    risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for h in hosts:
        ports = db.get_ports_for_host(h["id"])
        total_ports += sum(1 for p in ports if p["state"] == "open")
        risk_distribution[h["risk_level"]] = risk_distribution.get(h["risk_level"], 0) + 1
        if h["risk_level"] in ("HIGH", "CRITICAL"):
            high_risk += 1

    return {
        "total_devices": total_devices,
        "live_hosts": live_hosts,
        "offline_hosts": offline_hosts,
        "total_open_ports": total_ports,
        "high_risk_devices": high_risk,
        "scan_duration": latest_scan["duration_seconds"] if latest_scan else None,
        "last_scan_target": latest_scan["target"] if latest_scan else None,
        "last_scan_at": latest_scan["started_at"] if latest_scan else None,
        "risk_distribution": risk_distribution,
    }


@app.get("/api/dashboard/charts", response_model=DashboardChartsOut)
def dashboard_charts(username: str = Depends(auth.require_auth)):
    hosts = db.get_latest_hosts()

    protocol_counts: dict = {}
    port_counts: dict = {}
    for h in hosts:
        for p in db.get_ports_for_host(h["id"]):
            if p["state"] != "open":
                continue
            svc = p["service_name"] or f'port-{p["port_number"]}'
            protocol_counts[svc] = protocol_counts.get(svc, 0) + 1
            key = f'{p["port_number"]}/{p["protocol"]}'
            port_counts[key] = port_counts.get(key, 0) + 1

    protocol_chart = [{"name": k, "value": v} for k, v in
                       sorted(protocol_counts.items(), key=lambda x: -x[1])][:8]
    top_ports_chart = [{"port": k, "count": v} for k, v in
                        sorted(port_counts.items(), key=lambda x: -x[1])][:8]

    scans = db.list_scans(limit=10)
    scan_history_chart = [
        {"scan_id": s["id"], "date": s["started_at"][:10], "live_hosts": s["live_hosts"],
         "duration": s["duration_seconds"]}
        for s in reversed(scans)
    ]

    host_status_chart = [
        {"name": "Online", "value": sum(1 for h in hosts if h["status"] == "online")},
        {"name": "Offline", "value": sum(1 for h in hosts if h["status"] == "offline")},
    ]

    return {
        "protocol_distribution": protocol_chart,
        "top_open_ports": top_ports_chart,
        "scan_history": scan_history_chart,
        "host_status": host_status_chart,
    }


# ---------------------------------------------------------------------------
# Scans
# ---------------------------------------------------------------------------
@app.post("/api/scans", response_model=ScanCreatedResponse, status_code=status.HTTP_201_CREATED)
def start_scan(payload: ScanRequest, username: str = Depends(auth.require_auth)):
    scan_type = scanner.classify_target(payload.target)
    scan_id = db.create_scan(payload.target, scan_type, payload.profile)
    scanner.start_scan_async(scan_id, payload.target, payload.profile)
    logger.info("User %r started scan #%s (target=%s, profile=%s)",
                username, scan_id, payload.target, payload.profile)
    return {"scan_id": scan_id, "status": "running"}


@app.get("/api/scans", response_model=list[ScanOut])
def list_scans(username: str = Depends(auth.require_auth)):
    return db.list_scans(limit=50)


@app.get("/api/scans/{scan_id}", response_model=ScanOut, responses={404: {"model": ErrorResponse}})
def get_scan(scan_id: int, username: str = Depends(auth.require_auth)):
    scan = db.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    return scan


@app.get("/api/scans/{scan_id}/progress", response_model=ScanProgressOut)
def scan_progress(scan_id: int, username: str = Depends(auth.require_auth)):
    return scanner.get_progress(scan_id)


@app.get("/api/scans/{scan_id}/hosts", response_model=list[HostDetailOut])
def scan_hosts(scan_id: int, username: str = Depends(auth.require_auth)):
    hosts = db.get_hosts_for_scan(scan_id)
    for h in hosts:
        h["ports"] = db.get_ports_for_host(h["id"])
        h["recommendations"] = db.get_recommendations_for_host(h["id"])
    return hosts


@app.delete("/api/scans/{scan_id}", response_model=DeleteResponse)
def remove_scan(scan_id: int, username: str = Depends(auth.require_auth)):
    scan = db.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    db.delete_scan(scan_id)
    logger.info("User %r deleted scan #%s", username, scan_id)
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Hosts
# ---------------------------------------------------------------------------
@app.get("/api/hosts", response_model=list[HostOut])
def all_hosts(username: str = Depends(auth.require_auth)):
    hosts = db.get_all_hosts()
    for h in hosts:
        h["ports"] = db.get_ports_for_host(h["id"])
    return hosts


@app.get("/api/hosts/latest", response_model=list[HostOut])
def latest_hosts(username: str = Depends(auth.require_auth)):
    hosts = db.get_latest_hosts()
    for h in hosts:
        h["ports"] = db.get_ports_for_host(h["id"])
    return hosts


@app.get("/api/hosts/{host_id}", response_model=HostDetailOut, responses={404: {"model": ErrorResponse}})
def host_detail(host_id: int, username: str = Depends(auth.require_auth)):
    host = db.get_host(host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    host["ports"] = db.get_ports_for_host(host_id)
    host["recommendations"] = db.get_recommendations_for_host(host_id)
    return host


# ---------------------------------------------------------------------------
# Topology
# ---------------------------------------------------------------------------
@app.get("/api/topology/{scan_id}", response_model=TopologyOut, responses={404: {"model": ErrorResponse}})
def topology(scan_id: int, username: str = Depends(auth.require_auth)):
    scan = db.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    hosts = db.get_hosts_for_scan(scan_id)

    nodes = [{"id": "core", "label": scan["target"], "type": "network"}]
    edges = []

    # Group hosts by VLAN so the graph reflects network segmentation instead
    # of a flat star - hosts without a known VLAN are bucketed together.
    vlan_groups: dict = {}
    for h in hosts:
        vlan_id = h.get("vlan_id")
        vlan_name = h.get("vlan_name") or "Unassigned"
        key = vlan_id if vlan_id is not None else "unassigned"
        vlan_groups.setdefault(key, {"name": vlan_name, "id": vlan_id, "hosts": []})
        vlan_groups[key]["hosts"].append(h)

    for key, group in vlan_groups.items():
        vlan_node_id = f"vlan-{key}"
        label = f"VLAN {group['id']}" if group["id"] is not None else "Unassigned"
        nodes.append({
            "id": vlan_node_id,
            "label": label,
            "type": "vlan",
            "vlan_name": group["name"],
        })
        edges.append({"source": "core", "target": vlan_node_id})

        for h in group["hosts"]:
            nodes.append({
                "id": str(h["id"]),
                "label": h["ip_address"],
                "hostname": h["hostname"],
                "type": "host",
                "status": h["status"],
                "risk_level": h["risk_level"],
                "os_family": h["os_family"],
            })
            edges.append({"source": vlan_node_id, "target": str(h["id"])})

    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# SNMP
# ---------------------------------------------------------------------------
@app.get("/api/hosts/{host_id}/snmp", response_model=SnmpResponseOut, responses={404: {"model": ErrorResponse}})
def host_snmp(host_id: int, username: str = Depends(auth.require_auth)):
    host = db.get_host(host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    info = db.get_snmp_info(host_id)
    interfaces = db.get_interfaces(host_id)
    return {"available": info is not None, "info": info, "interfaces": interfaces}


# ---------------------------------------------------------------------------
# CVE correlation
# ---------------------------------------------------------------------------
@app.get("/api/hosts/{host_id}/cves", response_model=CveResponseOut, responses={404: {"model": ErrorResponse}})
def host_cves(host_id: int, username: str = Depends(auth.require_auth)):
    host = db.get_host(host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    ports = [p for p in db.get_ports_for_host(host_id) if p["state"] == "open"]

    results = []
    for p in ports:
        if not p["service_name"]:
            continue
        cves = cve_lookup.get_cves_for_service(p["service_name"], p["version"] or "")
        if cves:
            results.append({
                "port_number": p["port_number"],
                "service_name": p["service_name"],
                "version": p["version"],
                "cves": cves,
            })
    return {"host_id": host_id, "findings": results}


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
@app.get("/api/reports/{scan_id}/pdf", responses={404: {"model": ErrorResponse}})
def report_pdf(scan_id: int, username: str = Depends(auth.require_auth)):
    try:
        content = reports.generate_pdf_report(scan_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return Response(content=content, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="scan_{scan_id}_report.pdf"'
    })


@app.get("/api/reports/{scan_id}/csv", responses={404: {"model": ErrorResponse}})
def report_csv(scan_id: int, username: str = Depends(auth.require_auth)):
    try:
        content = reports.generate_csv_report(scan_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return Response(content=content, media_type="text/csv", headers={
        "Content-Disposition": f'attachment; filename="scan_{scan_id}_report.csv"'
    })


@app.get("/api/reports/{scan_id}/json", responses={404: {"model": ErrorResponse}})
def report_json(scan_id: int, username: str = Depends(auth.require_auth)):
    try:
        content = reports.generate_json_report(scan_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return Response(content=content, media_type="application/json", headers={
        "Content-Disposition": f'attachment; filename="scan_{scan_id}_report.json"'
    })


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# WebSocket - real-time scan progress
# ---------------------------------------------------------------------------
@app.websocket("/ws/scans/{scan_id}")
async def scan_progress_ws(websocket: WebSocket, scan_id: int):
    """
    Pushes scan progress updates every ~700ms until the scan reaches a
    terminal state (completed/failed), then closes. Auth token is passed as
    a query parameter (`?token=...`) since browsers can't set custom headers
    on WebSocket handshakes.

    The frontend falls back to REST polling (`/api/scans/{id}/progress`) if
    this connection can't be established, so this is a progressive
    enhancement rather than a hard dependency.
    """
    token = websocket.query_params.get("token")
    username = auth.verify_token(token) if token else None
    if not username:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    try:
        while True:
            progress = scanner.get_progress(scan_id)
            await websocket.send_json(progress)
            if progress.get("phase") in ("completed", "failed"):
                break
            await asyncio.sleep(0.7)
    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected from scan #%s progress stream", scan_id)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
