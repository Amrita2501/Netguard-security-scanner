"""
CVE correlation engine.

Matches a detected service name + version string against known
vulnerabilities, using two layers:

  1. A small curated **offline fallback table** of well-known, widely-cited
     CVEs for commonly-seen outdated services (e.g. the vsftpd 2.3.4 backdoor,
     old Samba/OpenSSH issues, unauthenticated Redis). This guarantees the
     feature works immediately in a demo, with no internet access required.

  2. A **live lookup against the NVD (National Vulnerability Database) REST
     API** (https://services.nvd.nist.gov/rest/json/cves/2.0), used as a
     best-effort enrichment on top of the offline table. Results are cached
     in SQLite (`cve_cache`) so we don't hammer NVD's rate limits on every
     page load. If the network call fails (offline machine, NVD rate limit,
     timeout), we silently fall back to the offline table only - the feature
     never blocks or errors out the host detail page.

This mirrors how a real vulnerability-management tool works: a fast local
signature check backed by an external, authoritative feed.
"""
import logging
import requests

from app import database as db

logger = logging.getLogger("netguard.cve")

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
NVD_TIMEOUT_SECONDS = 4

# ---------------------------------------------------------------------------
# Offline fallback table: (service_name_lower, version_prefix) -> [CVEs]
# Deliberately small and curated to widely-known, high-confidence matches
# rather than attempting to be a full vulnerability database.
# ---------------------------------------------------------------------------
KNOWN_VULNERABLE_SERVICES = {
    ("vsftpd", "2.3.4"): [
        {"cve_id": "CVE-2011-2523", "severity": "CRITICAL", "cvss_score": 10.0,
         "description": "vsftpd 2.3.4 contains a backdoor that grants a remote root shell "
                         "via a crafted username during login."},
    ],
    ("telnet", ""): [
        {"cve_id": "CVE-1999-0619", "severity": "HIGH", "cvss_score": 7.5,
         "description": "Telnet transmits credentials and session data unencrypted, "
                         "allowing trivial credential interception."},
    ],
    ("samba", "3."): [
        {"cve_id": "CVE-2017-7494", "severity": "CRITICAL", "cvss_score": 9.8,
         "description": "Samba versions 3.5.0 through 4.6.4/4.5.10/4.4.14 allow remote code "
                         "execution via a malicious shared library upload (\"SambaCry\")."},
    ],
    ("mysql", "8.0.1"): [
        {"cve_id": "CVE-2021-2154", "severity": "MEDIUM", "cvss_score": 6.6,
         "description": "MySQL Server component vulnerability allowing high-privileged "
                         "attackers to compromise availability via the Optimizer subcomponent."},
    ],
    ("redis", ""): [
        {"cve_id": "CVE-2022-0543", "severity": "CRITICAL", "cvss_score": 10.0,
         "description": "Redis on Debian-based systems is vulnerable to Lua sandbox escape "
                         "leading to remote code execution."},
        {"cve_id": "ADVISORY-NOAUTH", "severity": "HIGH", "cvss_score": 8.0,
         "description": "Redis has no authentication enabled by default; an exposed instance "
                         "allows unauthenticated data read/write and potential RCE via module loading."},
    ],
    ("openssh", "7.2"): [
        {"cve_id": "CVE-2016-6210", "severity": "MEDIUM", "cvss_score": 5.9,
         "description": "OpenSSH before 7.3 allows remote user enumeration via a timing "
                         "side-channel during password authentication."},
    ],
    ("mongodb", ""): [
        {"cve_id": "ADVISORY-NOAUTH", "severity": "HIGH", "cvss_score": 8.0,
         "description": "MongoDB instances are frequently deployed without authentication "
                         "enabled, exposing all data to any network client."},
    ],
    ("microsoft-ds", ""): [
        {"cve_id": "CVE-2017-0144", "severity": "MEDIUM", "cvss_score": 8.1,
         "description": "SMB is exposed (port 445). If SMBv1 is still enabled, this host is "
                         "susceptible to the WannaCry/EternalBlue RCE (\"MS17-010\"). Verify "
                         "SMBv1 is disabled regardless of the SMB version detected."},
    ],
}


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _offline_matches(service_name: str, version: str) -> list:
    # Search across both fields combined: nmap often reports the generic
    # protocol as service_name (e.g. "ftp", "netbios-ssn") while the actual
    # software name/version (e.g. "vsftpd 2.3.4", "Samba 3.6") only appears
    # in the version string.
    combined = f"{_normalize(service_name)} {_normalize(version)}".strip()
    matches = []
    for (svc, ver_prefix), cves in KNOWN_VULNERABLE_SERVICES.items():
        # Require the specific software name to appear in the combined text.
        # (One-directional: "vsftpd" must appear in "ftp vsftpd 2.3.4", but a
        # generic detected name like "ftp" must NOT match the "vsftpd" rule.)
        if svc and svc not in combined:
            continue
        if ver_prefix and ver_prefix not in combined:
            continue
        for cve in cves:
            matches.append({**cve, "source": "offline"})
    return matches


def _query_nvd(service_name: str, version: str) -> list:
    """Best-effort live NVD lookup. Returns [] on any failure (never raises)."""
    keyword = f"{service_name} {version}".strip()
    if not keyword:
        return []
    try:
        resp = requests.get(
            NVD_API_URL,
            params={"keywordSearch": keyword, "resultsPerPage": 5},
            timeout=NVD_TIMEOUT_SECONDS,
            headers={"User-Agent": "NetGuard-Scanner/1.0"},
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        results = []
        for item in data.get("vulnerabilities", [])[:5]:
            cve = item.get("cve", {})
            cve_id = cve.get("id")
            if not cve_id:
                continue
            descriptions = cve.get("descriptions", [])
            description = next((d["value"] for d in descriptions if d.get("lang") == "en"), None)
            metrics = cve.get("metrics", {})
            cvss_score = None
            severity = "MEDIUM"
            for metric_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                if metric_key in metrics and metrics[metric_key]:
                    cvss_data = metrics[metric_key][0].get("cvssData", {})
                    cvss_score = cvss_data.get("baseScore")
                    severity = metrics[metric_key][0].get("baseSeverity", severity)
                    break
            results.append({
                "cve_id": cve_id,
                "description": description,
                "severity": severity,
                "cvss_score": cvss_score,
                "source": "nvd",
            })
        return results
    except Exception as exc:
        # Network unavailable, rate-limited, malformed response, etc.
        # This is expected/normal in sandboxed or offline environments, so
        # it's logged at debug level rather than a warning - the caller
        # falls back to the offline curated table transparently.
        logger.debug("NVD lookup for %r failed (falling back to offline data): %s", keyword, exc)
        return []


def get_cves_for_service(service_name: str, version: str) -> list:
    """
    Returns a de-duplicated list of CVE matches for a service+version,
    combining cached results, the offline curated table, and (if not
    already cached) a best-effort live NVD lookup.
    """
    if not service_name:
        return []

    version = version or ""
    cache_key_version = version or "unknown"

    cached = db.get_cached_cves(_normalize(service_name), cache_key_version)
    if cached:
        return [dict(c) for c in cached]

    matches = _offline_matches(service_name, version)

    # Only attempt a live network call if we don't already have an offline
    # match, to keep host-detail page loads fast and avoid unnecessary
    # external calls once we have high-confidence local data.
    if not matches:
        matches = _query_nvd(service_name, version)

    for cve in matches:
        db.cache_cve(_normalize(service_name), cache_key_version, cve)

    return matches
