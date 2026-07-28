"""
Security Risk Analysis Engine.

Given the set of open ports/services discovered on a host, this module
computes a numeric risk score, buckets it into LOW/MEDIUM/HIGH/CRITICAL,
and generates human-readable remediation recommendations.

The rule set below models widely-accepted network security guidance
(disable clear-text protocols, restrict database/management exposure,
etc.) rather than a single CVE, so it stays meaningful even as specific
service versions change.
"""
from typing import List, Dict, Tuple

# Each rule: port -> (score contribution, severity, title, description)
PORT_RULES: Dict[int, Tuple[int, str, str, str]] = {
    21: (25, "HIGH", "FTP exposed (port 21)",
         "FTP transmits credentials and data in clear text. Disable FTP or migrate to SFTP/FTPS."),
    23: (35, "CRITICAL", "Telnet exposed (port 23)",
         "Telnet sends everything unencrypted, including passwords. Disable Telnet and use SSH instead."),
    25: (10, "LOW", "SMTP exposed (port 25)",
         "Ensure the mail relay is not open (open relay) and is authenticated and rate-limited."),
    53: (5, "LOW", "DNS exposed (port 53)",
         "Restrict recursive DNS queries to trusted clients to prevent DNS amplification abuse."),
    69: (25, "HIGH", "TFTP exposed (port 69)",
         "TFTP has no authentication. Restrict to management VLANs or disable if unused."),
    110: (15, "MEDIUM", "POP3 exposed (port 110)",
          "Use POP3S (995) with TLS instead of unencrypted POP3."),
    135: (15, "MEDIUM", "MS-RPC exposed (port 135)",
          "Restrict RPC endpoint mapper exposure to the internal network only."),
    139: (20, "MEDIUM", "NetBIOS exposed (port 139)",
          "Legacy NetBIOS session service should be disabled if SMB direct-hosting (445) is used instead."),
    143: (15, "MEDIUM", "IMAP exposed (port 143)",
          "Use IMAPS (993) with TLS instead of unencrypted IMAP."),
    445: (20, "MEDIUM", "SMB exposed (port 445)",
          "Restrict SMB to trusted subnets and ensure SMBv1 is disabled to mitigate lateral-movement risk."),
    512: (20, "MEDIUM", "rexec exposed (port 512)", "Disable legacy r-services; use SSH instead."),
    513: (20, "MEDIUM", "rlogin exposed (port 513)", "Disable legacy r-services; use SSH instead."),
    514: (20, "MEDIUM", "rsh exposed (port 514)", "Disable legacy r-services; use SSH instead."),
    1433: (30, "CRITICAL", "MSSQL exposed (port 1433)",
           "Database exposed to the network. Restrict access to application servers only via firewall rules."),
    1521: (30, "CRITICAL", "Oracle DB exposed (port 1521)",
           "Database exposed to the network. Restrict access to trusted application hosts only."),
    2049: (15, "MEDIUM", "NFS exposed (port 2049)",
           "Restrict NFS exports to specific trusted hosts and disable root-squash bypass."),
    3306: (30, "CRITICAL", "MySQL exposed (port 3306)",
           "Restrict MySQL access to trusted application hosts; never expose directly to the internet."),
    3389: (18, "MEDIUM", "RDP exposed (port 3389)",
           "Restrict RDP with a VPN or bastion host, enable Network Level Authentication and MFA."),
    5432: (30, "CRITICAL", "PostgreSQL exposed (port 5432)",
           "Restrict PostgreSQL access to trusted application hosts; enforce SSL and strong auth."),
    5900: (20, "MEDIUM", "VNC exposed (port 5900)",
           "VNC often uses weak authentication. Tunnel over SSH/VPN and set a strong password."),
    6379: (28, "HIGH", "Redis exposed (port 6379)",
           "Redis has no auth by default. Bind to localhost or enable `requirepass` / ACLs and a firewall."),
    8080: (8, "LOW", "Alt-HTTP exposed (port 8080)",
           "Confirm this admin/proxy interface requires authentication and is not intended to be public."),
    9200: (25, "HIGH", "Elasticsearch exposed (port 9200)",
           "Elasticsearch commonly ships without auth. Enable security features and restrict network access."),
    27017: (28, "HIGH", "MongoDB exposed (port 27017)",
            "MongoDB can be unauthenticated by default. Enable access control and bind to trusted IPs only."),
}

# Bonus signal: an OS reported with low confidence or "Unknown" slightly raises
# uncertainty risk, since it may indicate an unmanaged / unpatched device.
OS_UNKNOWN_PENALTY = 5


def score_to_level(score: int) -> str:
    if score >= 70:
        return "CRITICAL"
    if score >= 40:
        return "HIGH"
    if score >= 15:
        return "MEDIUM"
    return "LOW"


def analyze_host(open_ports: List[dict], os_family: str) -> Tuple[int, str, List[dict]]:
    """
    Returns (risk_score, risk_level, recommendations[]) for a host given
    its list of open ports (each a dict with at least 'port_number').
    """
    score = 0
    recommendations = []
    seen_ports = set()

    for p in open_ports:
        port_num = p.get("port_number")
        if port_num in seen_ports:
            continue
        seen_ports.add(port_num)

        rule = PORT_RULES.get(port_num)
        if rule:
            contribution, severity, title, description = rule
            score += contribution
            recommendations.append({
                "port_number": port_num,
                "severity": severity,
                "title": title,
                "description": description,
            })
        else:
            # Unlisted but open port still contributes a small baseline risk
            # for unnecessary attack surface.
            score += 2

    if not os_family or os_family.lower() == "unknown":
        score += OS_UNKNOWN_PENALTY

    # Many simultaneously open, unrelated services increases lateral-movement risk.
    if len(seen_ports) >= 8:
        score += 10

    score = min(score, 100)
    level = score_to_level(score)
    return score, level, recommendations
