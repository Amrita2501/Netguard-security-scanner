"""
Network scanning engine.

Wraps `python-nmap` to perform:
  1. Host discovery (ping sweep) across a single IP / IP range / CIDR subnet.
  2. Per-host deep scan: open ports, service/version detection, OS fingerprint.

Design notes
------------
Rather than issuing one giant `nmap` call for an entire /24 (which blocks
until everything finishes and gives no visibility into progress), we:
  (a) run a fast `-sn` ping sweep to discover which hosts are alive, then
  (b) scan discovered hosts one at a time, updating a shared progress
      object after each host completes.

This gives the frontend real, incremental progress to poll, and keeps
a single slow/unresponsive host from stalling visibility into the rest
of the scan.

`nmap` itself must be installed on the host OS (e.g. `brew install nmap`
on macOS) — python-nmap is a thin wrapper around the `nmap` binary.
"""
import time
import threading
import logging
from typing import List, Dict

import nmap

from app import database as db
from app import snmp_client
from app.risk_engine import analyze_host
from app.config import DEFAULT_PORT_RANGE, DEEP_PORT_RANGE, NMAP_ARGS_FAST, NMAP_ARGS_DEEP

logger = logging.getLogger("netguard.scanner")

# In-memory progress tracker, keyed by scan_id.
# { scan_id: {"phase": str, "current": int, "total": int, "percent": float, "current_host": str} }
SCAN_PROGRESS: Dict[int, dict] = {}
_progress_lock = threading.Lock()


def _set_progress(scan_id: int, **kwargs):
    with _progress_lock:
        SCAN_PROGRESS.setdefault(scan_id, {})
        SCAN_PROGRESS[scan_id].update(kwargs)


def get_progress(scan_id: int) -> dict:
    with _progress_lock:
        return dict(SCAN_PROGRESS.get(scan_id, {"phase": "unknown", "percent": 0}))


def classify_target(target: str) -> str:
    target = target.strip()
    if "/" in target:
        return "subnet"
    if "-" in target:
        return "range"
    return "single"


def _map_os_family(os_name: str) -> str:
    if not os_name:
        return "Unknown"
    name = os_name.lower()
    if "windows" in name:
        return "Windows"
    if "linux" in name:
        return "Linux"
    if "mac" in name or "darwin" in name or "os x" in name:
        return "macOS"
    return "Unknown"


def discover_hosts(nm: nmap.PortScanner, target: str) -> List[dict]:
    """Fast ping sweep. Returns basic host info (IP, MAC, vendor, status, latency)."""
    nm.scan(hosts=target, arguments="-sn -T4")
    hosts = []
    for ip in nm.all_hosts():
        host_data = nm[ip]
        status = host_data.state()
        mac = host_data["addresses"].get("mac")
        vendor = None
        if mac and host_data.get("vendor"):
            vendor = host_data["vendor"].get(mac)
        hostnames = host_data.get("hostnames", [])
        hostname = hostnames[0]["name"] if hostnames and hostnames[0]["name"] else None

        hosts.append({
            "ip_address": ip,
            "hostname": hostname,
            "mac_address": mac,
            "vendor": vendor,
            "status": "online" if status == "up" else "offline",
            "latency_ms": None,
        })
    return hosts


def deep_scan_host(nm: nmap.PortScanner, ip: str, profile: str) -> dict:
    """Run service/version + OS detection against a single host."""
    ports = DEFAULT_PORT_RANGE if profile == "fast" else DEEP_PORT_RANGE
    args = NMAP_ARGS_FAST if profile == "fast" else NMAP_ARGS_DEEP

    start = time.time()
    nm.scan(hosts=ip, ports=ports, arguments=args)
    latency_ms = round((time.time() - start) * 1000, 1)

    result = {"ports": [], "os_name": None, "os_family": "Unknown", "os_confidence": None,
              "latency_ms": latency_ms}

    if ip not in nm.all_hosts():
        return result

    host_data = nm[ip]

    # --- OS fingerprint --------------------------------------------------
    os_matches = host_data.get("osmatch", [])
    if os_matches:
        best = os_matches[0]
        result["os_name"] = best.get("name")
        result["os_confidence"] = int(best.get("accuracy", 0))
        result["os_family"] = _map_os_family(best.get("name"))

    # --- Ports / services --------------------------------------------------
    for proto in host_data.all_protocols() if hasattr(host_data, "all_protocols") else []:
        port_dict = host_data[proto]
        for port_num, pdata in port_dict.items():
            service_parts = [pdata.get("product", ""), pdata.get("version", "")]
            version_str = " ".join(p for p in service_parts if p).strip() or None
            result["ports"].append({
                "port_number": int(port_num),
                "protocol": proto,
                "service_name": pdata.get("name"),
                "state": pdata.get("state"),
                "version": version_str,
                "banner": pdata.get("extrainfo") or None,
            })

    return result


def run_scan(scan_id: int, target: str, profile: str):
    """
    Full scan pipeline, intended to run in a background thread.
    Persists results incrementally to SQLite and updates SCAN_PROGRESS.
    """
    nm = nmap.PortScanner()
    started = time.time()
    logger.info("Scan #%s started (target=%s, profile=%s)", scan_id, target, profile)
    _set_progress(scan_id, phase="discovery", current=0, total=0, percent=2, current_host=None)

    try:
        hosts = discover_hosts(nm, target)
        total = len(hosts)
        logger.info("Scan #%s discovery complete: %d host(s) found", scan_id, total)
        _set_progress(scan_id, phase="scanning", current=0, total=total, percent=5, current_host=None)

        live_count = 0
        for idx, host in enumerate(hosts, start=1):
            _set_progress(scan_id, current_host=host["ip_address"])

            if host["status"] == "online":
                live_count += 1
                details = deep_scan_host(nm, host["ip_address"], profile)
                host["latency_ms"] = details["latency_ms"]
                host["os_name"] = details["os_name"]
                host["os_family"] = details["os_family"]
                host["os_confidence"] = details["os_confidence"]

                open_ports = [p for p in details["ports"] if p["state"] == "open"]
                score, level, recos = analyze_host(open_ports, details["os_family"])
                host["risk_score"] = score
                host["risk_level"] = level

                host_id = db.insert_host(scan_id, host)
                for p in details["ports"]:
                    db.insert_port(host_id, p)
                for r in recos:
                    db.insert_recommendation(host_id, r)
                logger.debug(
                    "Host %s: %d open port(s), risk=%s", host["ip_address"], len(open_ports), level
                )

                # Best-effort SNMP probe (SNMPv2c, community "public").
                # Most consumer/home devices do not run an SNMP agent, so a
                # None result here is the normal, expected outcome - only
                # managed network gear (switches/routers/APs) will respond.
                snmp_result = snmp_client.query_device(host["ip_address"])
                if snmp_result:
                    logger.info("Host %s responded to SNMP - storing device info", host["ip_address"])
                    db.insert_snmp_info(host_id, snmp_result)
                    for iface in snmp_result.get("interfaces", []):
                        db.insert_interface(host_id, iface)
            else:
                host["risk_score"] = 0
                host["risk_level"] = "LOW"
                db.insert_host(scan_id, host)

            percent = 5 + round((idx / total) * 93, 1) if total else 100
            _set_progress(scan_id, current=idx, total=total, percent=percent)

        duration = round(time.time() - started, 2)
        db.finish_scan(scan_id, "completed", duration, total, live_count)
        _set_progress(scan_id, phase="completed", percent=100, current_host=None)
        logger.info(
            "Scan #%s completed in %.2fs: %d/%d host(s) live", scan_id, duration, live_count, total
        )

    except Exception as exc:  # pragma: no cover - defensive, surfaced to UI
        duration = round(time.time() - started, 2)
        logger.exception("Scan #%s failed after %.2fs", scan_id, duration)
        db.finish_scan(scan_id, "failed", duration, 0, 0, error_message=str(exc))
        _set_progress(scan_id, phase="failed", percent=100, error=str(exc))


def start_scan_async(scan_id: int, target: str, profile: str):
    thread = threading.Thread(target=run_scan, args=(scan_id, target, profile), daemon=True)
    thread.start()
