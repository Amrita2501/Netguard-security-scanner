"""
Pydantic schemas for request validation and API response models.

Wiring these into each endpoint's `response_model=` (see main.py) buys us
three things for free: automatic response validation, accurate OpenAPI/
Swagger docs at /docs, and a single source of truth for the API's shape
that both the FastAPI backend and future API consumers can rely on.
"""
import re
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

# Allow-list for scan targets: IPv4/IPv6 addresses, CIDR subnets, IP ranges
# (e.g. "192.168.1.1-50"), and hostnames - but no whitespace or shell/nmap
# flag characters. `python-nmap` forwards this string to the `nmap` CLI via
# `shlex.split()`, so without this check a value like "127.0.0.1 --script
# vuln" would be split into two separate nmap arguments, letting a caller
# smuggle in extra nmap flags. Rejecting whitespace and a leading "-"
# closes that off while still accepting every target format the app
# actually supports (see the Usage Guide in README.md).
_TARGET_RE = re.compile(r"^(?!-)[A-Za-z0-9.:/_-]+$")

RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
ScanStatus = Literal["running", "completed", "failed"]
ScanProfile = Literal["fast", "deep"]


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)


class LoginResponse(BaseModel):
    token: str
    username: str
    full_name: str


# ---------------------------------------------------------------------------
# Scans
# ---------------------------------------------------------------------------
class ScanRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=200,
                         description="IP, IP range (a-b) or CIDR subnet, e.g. 192.168.1.0/24")
    profile: ScanProfile = Field("fast", description="fast (top ports) | deep (all 65535 ports)")

    @field_validator("target")
    @classmethod
    def target_must_be_well_formed(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("target must not be blank")
        if not _TARGET_RE.match(stripped):
            raise ValueError(
                "target must be a valid IP, IP range, CIDR subnet, or hostname "
                "(letters, digits, '.', ':', '/', '-', '_' only - no spaces)"
            )
        return stripped


class ScanCreatedResponse(BaseModel):
    scan_id: int
    status: str = "running"


class ScanOut(BaseModel):
    id: int
    target: str
    scan_type: str
    profile: str
    status: ScanStatus
    started_at: str
    finished_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    total_hosts: int = 0
    live_hosts: int = 0
    error_message: Optional[str] = None


class ScanProgressOut(BaseModel):
    phase: str
    current: Optional[int] = None
    total: Optional[int] = None
    percent: float = 0
    current_host: Optional[str] = None
    error: Optional[str] = None


class DeleteResponse(BaseModel):
    deleted: bool = True


# ---------------------------------------------------------------------------
# Hosts / ports / recommendations
# ---------------------------------------------------------------------------
class PortOut(BaseModel):
    port_number: int
    protocol: str
    service_name: Optional[str] = None
    state: Optional[str] = None
    version: Optional[str] = None
    banner: Optional[str] = None


class RecommendationOut(BaseModel):
    port_number: Optional[int] = None
    severity: str
    title: str
    description: str


class HostOut(BaseModel):
    id: int
    ip_address: str
    hostname: Optional[str] = None
    mac_address: Optional[str] = None
    vendor: Optional[str] = None
    os_name: Optional[str] = None
    os_family: Optional[str] = None
    os_confidence: Optional[int] = None
    status: str
    latency_ms: Optional[float] = None
    last_seen: Optional[str] = None
    risk_score: int = 0
    risk_level: str = "LOW"
    vlan_id: Optional[int] = None
    vlan_name: Optional[str] = None
    ports: List[PortOut] = []


class HostDetailOut(HostOut):
    recommendations: List[RecommendationOut] = []


# ---------------------------------------------------------------------------
# SNMP
# ---------------------------------------------------------------------------
class InterfaceOut(BaseModel):
    id: int
    host_id: int
    if_index: Optional[int] = None
    if_descr: Optional[str] = None
    if_type: Optional[str] = None
    if_speed_mbps: Optional[float] = None
    if_admin_status: Optional[str] = None
    if_oper_status: Optional[str] = None


class SnmpInfoOut(BaseModel):
    id: int
    host_id: int
    sys_descr: Optional[str] = None
    sys_name: Optional[str] = None
    sys_uptime: Optional[str] = None
    sys_contact: Optional[str] = None
    sys_location: Optional[str] = None
    community_used: Optional[str] = None
    queried_at: str


class SnmpResponseOut(BaseModel):
    available: bool
    info: Optional[SnmpInfoOut] = None
    interfaces: List[InterfaceOut] = []


# ---------------------------------------------------------------------------
# CVE correlation
# ---------------------------------------------------------------------------
class CveOut(BaseModel):
    cve_id: str
    description: Optional[str] = None
    severity: str
    cvss_score: Optional[float] = None
    source: str = "offline"


class CveFindingOut(BaseModel):
    port_number: int
    service_name: str
    version: Optional[str] = None
    cves: List[CveOut] = []


class CveResponseOut(BaseModel):
    host_id: int
    findings: List[CveFindingOut] = []


# ---------------------------------------------------------------------------
# Topology
# ---------------------------------------------------------------------------
class TopologyNodeOut(BaseModel):
    id: str
    label: str
    type: Literal["network", "vlan", "host"]
    hostname: Optional[str] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None
    os_family: Optional[str] = None
    vlan_name: Optional[str] = None


class TopologyEdgeOut(BaseModel):
    source: str
    target: str


class TopologyOut(BaseModel):
    nodes: List[TopologyNodeOut]
    edges: List[TopologyEdgeOut]


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class RiskDistributionOut(BaseModel):
    LOW: int = 0
    MEDIUM: int = 0
    HIGH: int = 0
    CRITICAL: int = 0


class DashboardSummaryOut(BaseModel):
    total_devices: int
    live_hosts: int
    offline_hosts: int
    total_open_ports: int
    high_risk_devices: int
    scan_duration: Optional[float] = None
    last_scan_target: Optional[str] = None
    last_scan_at: Optional[str] = None
    risk_distribution: RiskDistributionOut


class ProtocolCountOut(BaseModel):
    name: str
    value: int


class TopPortCountOut(BaseModel):
    port: str
    count: int


class ScanHistoryPointOut(BaseModel):
    scan_id: int
    date: str
    live_hosts: int
    duration: Optional[float] = None


class DashboardChartsOut(BaseModel):
    protocol_distribution: List[ProtocolCountOut]
    top_open_ports: List[TopPortCountOut]
    scan_history: List[ScanHistoryPointOut]
    host_status: List[ProtocolCountOut]


# ---------------------------------------------------------------------------
# Generic error envelope (see main.py exception handlers)
# ---------------------------------------------------------------------------
class ErrorResponse(BaseModel):
    detail: str
