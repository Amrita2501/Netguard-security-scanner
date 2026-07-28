"""
SQLite persistence layer.

Uses plain sqlite3 (no ORM) so the schema is transparent and the project
has zero heavyweight dependencies. A single module owns the connection
factory and schema creation; every other module talks to the DB through
the helper functions here.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
import logging

from app.config import DB_PATH

logger = logging.getLogger("netguard.database")


def _dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = _dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they do not already exist."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT NOT NULL,
                scan_type TEXT NOT NULL,          -- single / range / subnet
                profile TEXT NOT NULL,            -- fast / deep
                status TEXT NOT NULL,             -- running / completed / failed
                started_at TEXT NOT NULL,
                finished_at TEXT,
                duration_seconds REAL,
                total_hosts INTEGER DEFAULT 0,
                live_hosts INTEGER DEFAULT 0,
                error_message TEXT
            );

            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
                ip_address TEXT NOT NULL,
                hostname TEXT,
                mac_address TEXT,
                vendor TEXT,
                os_name TEXT,
                os_family TEXT,
                os_confidence INTEGER,
                status TEXT NOT NULL,             -- online / offline
                latency_ms REAL,
                last_seen TEXT,
                risk_score INTEGER DEFAULT 0,
                risk_level TEXT DEFAULT 'LOW',
                vlan_id INTEGER,
                vlan_name TEXT
            );

            CREATE TABLE IF NOT EXISTS ports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
                port_number INTEGER NOT NULL,
                protocol TEXT NOT NULL,           -- tcp / udp
                service_name TEXT,
                state TEXT,                       -- open / closed / filtered
                version TEXT,
                banner TEXT
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
                port_number INTEGER,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS snmp_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
                sys_descr TEXT,
                sys_name TEXT,
                sys_uptime TEXT,
                sys_contact TEXT,
                sys_location TEXT,
                community_used TEXT,
                queried_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS interfaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
                if_index INTEGER,
                if_descr TEXT,
                if_type TEXT,
                if_speed_mbps REAL,
                if_admin_status TEXT,
                if_oper_status TEXT
            );

            CREATE TABLE IF NOT EXISTS cve_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                service_version TEXT NOT NULL,
                cve_id TEXT NOT NULL,
                description TEXT,
                severity TEXT,
                cvss_score REAL,
                source TEXT NOT NULL DEFAULT 'offline',
                cached_at TEXT NOT NULL,
                UNIQUE(service_name, service_version, cve_id)
            );

            CREATE INDEX IF NOT EXISTS idx_hosts_scan ON hosts(scan_id);
            CREATE INDEX IF NOT EXISTS idx_ports_host ON ports(host_id);
            CREATE INDEX IF NOT EXISTS idx_reco_host ON recommendations(host_id);
            CREATE INDEX IF NOT EXISTS idx_snmp_host ON snmp_info(host_id);
            CREATE INDEX IF NOT EXISTS idx_iface_host ON interfaces(host_id);
            CREATE INDEX IF NOT EXISTS idx_cve_lookup ON cve_cache(service_name, service_version);
            """
        )


def now_iso() -> str:
    # datetime.utcnow() is deprecated as of Python 3.12 (naive datetimes are
    # error-prone); now(timezone.utc) is the timezone-aware replacement.
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Scan CRUD
# ---------------------------------------------------------------------------
def create_scan(target: str, scan_type: str, profile: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO scans (target, scan_type, profile, status, started_at) "
            "VALUES (?, ?, ?, 'running', ?)",
            (target, scan_type, profile, now_iso()),
        )
        return cur.lastrowid


def finish_scan(scan_id: int, status: str, duration: float, total_hosts: int,
                 live_hosts: int, error_message: str = None):
    with get_conn() as conn:
        conn.execute(
            """UPDATE scans SET status=?, finished_at=?, duration_seconds=?,
               total_hosts=?, live_hosts=?, error_message=? WHERE id=?""",
            (status, now_iso(), duration, total_hosts, live_hosts, error_message, scan_id),
        )


def get_scan(scan_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM scans WHERE id=?", (scan_id,)).fetchone()
        return row


def list_scans(limit: int = 50):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()


def delete_scan(scan_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM scans WHERE id=?", (scan_id,))


# ---------------------------------------------------------------------------
# Host CRUD
# ---------------------------------------------------------------------------
def insert_host(scan_id: int, host: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO hosts
               (scan_id, ip_address, hostname, mac_address, vendor, os_name,
                os_family, os_confidence, status, latency_ms, last_seen,
                risk_score, risk_level, vlan_id, vlan_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                scan_id, host["ip_address"], host.get("hostname"),
                host.get("mac_address"), host.get("vendor"), host.get("os_name"),
                host.get("os_family"), host.get("os_confidence"), host["status"],
                host.get("latency_ms"), host.get("last_seen", now_iso()),
                host.get("risk_score", 0), host.get("risk_level", "LOW"),
                host.get("vlan_id"), host.get("vlan_name"),
            ),
        )
        return cur.lastrowid


def insert_port(host_id: int, port: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO ports (host_id, port_number, protocol, service_name,
               state, version, banner) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                host_id, port["port_number"], port.get("protocol", "tcp"),
                port.get("service_name"), port.get("state"),
                port.get("version"), port.get("banner"),
            ),
        )
        return cur.lastrowid


def insert_recommendation(host_id: int, rec: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO recommendations (host_id, port_number, severity, title, description)
               VALUES (?, ?, ?, ?, ?)""",
            (host_id, rec.get("port_number"), rec["severity"], rec["title"], rec["description"]),
        )
        return cur.lastrowid


def get_hosts_for_scan(scan_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM hosts WHERE scan_id=? ORDER BY ip_address", (scan_id,)
        ).fetchall()


def get_latest_hosts():
    """Hosts belonging to the most recent completed scan (used by the dashboard)."""
    with get_conn() as conn:
        latest = conn.execute(
            "SELECT id FROM scans WHERE status='completed' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not latest:
            return []
        return conn.execute(
            "SELECT * FROM hosts WHERE scan_id=? ORDER BY ip_address", (latest["id"],)
        ).fetchall()


def get_all_hosts():
    with get_conn() as conn:
        return conn.execute(
            """SELECT h.*, s.target as scan_target, s.started_at as scan_started_at
               FROM hosts h JOIN scans s ON h.scan_id = s.id
               ORDER BY h.id DESC"""
        ).fetchall()


def get_host(host_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM hosts WHERE id=?", (host_id,)).fetchone()


def get_ports_for_host(host_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM ports WHERE host_id=? ORDER BY port_number", (host_id,)
        ).fetchall()


def get_recommendations_for_host(host_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM recommendations WHERE host_id=?", (host_id,)
        ).fetchall()


def get_open_ports_for_scan(scan_id: int):
    with get_conn() as conn:
        return conn.execute(
            """SELECT p.* FROM ports p JOIN hosts h ON p.host_id = h.id
               WHERE h.scan_id=? AND p.state='open'""",
            (scan_id,),
        ).fetchall()


# ---------------------------------------------------------------------------
# SNMP CRUD
# ---------------------------------------------------------------------------
def insert_snmp_info(host_id: int, info: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO snmp_info (host_id, sys_descr, sys_name, sys_uptime,
               sys_contact, sys_location, community_used, queried_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (host_id, info.get("sys_descr"), info.get("sys_name"), info.get("sys_uptime"),
             info.get("sys_contact"), info.get("sys_location"), info.get("community_used"),
             now_iso()),
        )
        return cur.lastrowid


def insert_interface(host_id: int, iface: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO interfaces (host_id, if_index, if_descr, if_type,
               if_speed_mbps, if_admin_status, if_oper_status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (host_id, iface.get("if_index"), iface.get("if_descr"), iface.get("if_type"),
             iface.get("if_speed_mbps"), iface.get("if_admin_status"), iface.get("if_oper_status")),
        )
        return cur.lastrowid


def get_snmp_info(host_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM snmp_info WHERE host_id=? ORDER BY id DESC LIMIT 1", (host_id,)
        ).fetchone()


def get_interfaces(host_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM interfaces WHERE host_id=? ORDER BY if_index", (host_id,)
        ).fetchall()


# ---------------------------------------------------------------------------
# CVE cache CRUD
# ---------------------------------------------------------------------------
def get_cached_cves(service_name: str, service_version: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM cve_cache WHERE service_name=? AND service_version=?",
            (service_name, service_version),
        ).fetchall()


def cache_cve(service_name: str, service_version: str, cve: dict):
    with get_conn() as conn:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO cve_cache
                   (service_name, service_version, cve_id, description, severity,
                    cvss_score, source, cached_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (service_name, service_version, cve["cve_id"], cve.get("description"),
                 cve.get("severity"), cve.get("cvss_score"), cve.get("source", "offline"),
                 now_iso()),
            )
        except Exception as exc:
            # INSERT OR IGNORE already handles the expected case (duplicate
            # cache entry); anything reaching here is a genuine, unexpected
            # DB error and worth a log line, though we still don't want a
            # cache-write hiccup to break the CVE lookup response itself.
            logger.warning("Failed to cache CVE %s for %s %s: %s", cve.get("cve_id"), service_name, service_version, exc)
