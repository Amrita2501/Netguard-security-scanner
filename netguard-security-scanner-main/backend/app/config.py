"""
Application-wide configuration.

Every tunable value is read from an environment variable (with a sensible
default for local/demo use), following the 12-factor app pattern rather
than hardcoding values that differ between dev/staging/production. A local
`.env` file (see `.env.example`) is loaded automatically via `python-dotenv`
if present; real environment variables always take precedence over it.
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()  # no-op if .env doesn't exist - safe to call unconditionally

logger = logging.getLogger("netguard")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("NETGUARD_DATA_DIR", os.path.join(BASE_DIR, "data"))
DB_PATH = os.path.join(DATA_DIR, "netscan.db")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Server / CORS
# ---------------------------------------------------------------------------
# Comma-separated list of allowed frontend origins, e.g.
# "http://localhost:5173,https://netguard.example.com"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "NETGUARD_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

LOG_LEVEL = os.environ.get("NETGUARD_LOG_LEVEL", "INFO").upper()

# ---------------------------------------------------------------------------
# Scan tuning
# ---------------------------------------------------------------------------
# Common "well known" ports scanned by default for a fast sweep.
# A "deep scan" flag (see ScanRequest) expands this to 1-65535.
DEFAULT_PORT_RANGE = os.environ.get(
    "NETGUARD_DEFAULT_PORT_RANGE",
    "21,22,23,25,53,80,110,139,143,443,445,993,995,1433,1521,3306,3389,5432,5900,6379,8080,8443,27017",
)
DEEP_PORT_RANGE = os.environ.get("NETGUARD_DEEP_PORT_RANGE", "1-65535")

# Nmap arguments used per scan profile.
NMAP_ARGS_FAST = os.environ.get(
    "NETGUARD_NMAP_ARGS_FAST", "-sV -O --osscan-guess -T4 --max-retries 1 --host-timeout 30s"
)
NMAP_ARGS_DEEP = os.environ.get(
    "NETGUARD_NMAP_ARGS_DEEP", "-sV -O --osscan-guess -T4 --version-intensity 5"
)

# Default SNMPv2c community string used when polling network devices.
SNMP_COMMUNITY = os.environ.get("NETGUARD_SNMP_COMMUNITY", "public")

# ---------------------------------------------------------------------------
# Auth (portfolio-grade, NOT for production use)
# ---------------------------------------------------------------------------
# A single local demo account, stored as a plain JSON credential file.
# This satisfies the "simple login / store user locally" requirement
# without pulling in a full identity provider for a portfolio project.
AUTH_FILE = os.path.join(DATA_DIR, "users.json")

_DEFAULT_INSECURE_SECRET = "netscan-demo-secret-change-me"
SESSION_SECRET = os.environ.get("NETGUARD_SESSION_SECRET", _DEFAULT_INSECURE_SECRET)
TOKEN_TTL_SECONDS = int(os.environ.get("NETGUARD_TOKEN_TTL_SECONDS", 60 * 60 * 8))  # 8 hour session

if SESSION_SECRET == _DEFAULT_INSECURE_SECRET:
    logger.warning(
        "NETGUARD_SESSION_SECRET is not set - using the built-in insecure default. "
        "This is fine for local/demo use, but set NETGUARD_SESSION_SECRET to a random "
        "value before deploying anywhere reachable by other people."
    )

# ---------------------------------------------------------------------------
# Risk engine
# ---------------------------------------------------------------------------
RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
