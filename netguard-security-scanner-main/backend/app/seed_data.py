"""
Seeds the database with a realistic, fully-formed sample scan on first run,
so the dashboard, charts, host table, topology and reports are all
populated and demoable even before the user runs a real scan (which
requires `nmap` installed locally and running the app on an actual LAN).
"""
from app import database as db
from app.risk_engine import analyze_host

SAMPLE_HOSTS = [
    {"ip": "192.168.1.1", "hostname": "gateway.local", "mac": "AC:22:0B:11:22:33",
     "vendor": "TP-Link Technologies", "os": "Linux 5.x (embedded)", "family": "Linux", "conf": 88,
     "latency": 1.2, "vlan_id": 10, "vlan_name": "Management", "ports": [
        {"port_number": 53, "protocol": "tcp", "service_name": "domain", "state": "open", "version": "dnsmasq 2.85"},
        {"port_number": 80, "protocol": "tcp", "service_name": "http", "state": "open", "version": "lighttpd 1.4.55"},
        {"port_number": 443, "protocol": "tcp", "service_name": "https", "state": "open", "version": "lighttpd 1.4.55"},
     ]},
    {"ip": "192.168.1.10", "hostname": "fileserver.local", "mac": "00:1A:2B:33:44:55",
     "vendor": "Synology Inc.", "os": "Linux 4.x (Synology DSM)", "family": "Linux", "conf": 91,
     "latency": 3.4, "vlan_id": 20, "vlan_name": "Servers", "ports": [
        {"port_number": 22, "protocol": "tcp", "service_name": "ssh", "state": "open", "version": "OpenSSH 8.9"},
        {"port_number": 139, "protocol": "tcp", "service_name": "netbios-ssn", "state": "open", "version": "Samba 4.15"},
        {"port_number": 445, "protocol": "tcp", "service_name": "microsoft-ds", "state": "open", "version": "Samba 4.15"},
        {"port_number": 5000, "protocol": "tcp", "service_name": "http", "state": "open", "version": "Synology DSM"},
     ]},
    {"ip": "192.168.1.15", "hostname": "DESKTOP-9F2K1L", "mac": "3C:52:82:AA:BB:CC",
     "vendor": "Dell Inc.", "os": "Microsoft Windows 11", "family": "Windows", "conf": 95,
     "latency": 0.8, "vlan_id": 30, "vlan_name": "Workstations", "ports": [
        {"port_number": 135, "protocol": "tcp", "service_name": "msrpc", "state": "open", "version": "Microsoft Windows RPC"},
        {"port_number": 445, "protocol": "tcp", "service_name": "microsoft-ds", "state": "open", "version": "Windows 11"},
        {"port_number": 3389, "protocol": "tcp", "service_name": "ms-wbt-server", "state": "open", "version": "Microsoft Terminal Services"},
     ]},
    {"ip": "192.168.1.22", "hostname": "legacy-nas.local", "mac": "00:11:22:33:44:66",
     "vendor": "QNAP Systems", "os": "Linux 3.x", "family": "Linux", "conf": 70,
     "latency": 5.1, "vlan_id": 99, "vlan_name": "Legacy", "ports": [
        {"port_number": 21, "protocol": "tcp", "service_name": "ftp", "state": "open", "version": "vsftpd 2.3.4"},
        {"port_number": 23, "protocol": "tcp", "service_name": "telnet", "state": "open", "version": "BusyBox telnetd"},
        {"port_number": 139, "protocol": "tcp", "service_name": "netbios-ssn", "state": "open", "version": "Samba 3.6"},
        {"port_number": 445, "protocol": "tcp", "service_name": "microsoft-ds", "state": "open", "version": "Samba 3.6"},
     ]},
    {"ip": "192.168.1.30", "hostname": "db-server-01", "mac": "B8:27:EB:12:34:56",
     "vendor": "Raspberry Pi Foundation", "os": "Linux 6.x", "family": "Linux", "conf": 84,
     "latency": 2.0, "vlan_id": 20, "vlan_name": "Servers", "ports": [
        {"port_number": 22, "protocol": "tcp", "service_name": "ssh", "state": "open", "version": "OpenSSH 9.2"},
        {"port_number": 3306, "protocol": "tcp", "service_name": "mysql", "state": "open", "version": "MySQL 8.0.34"},
        {"port_number": 6379, "protocol": "tcp", "service_name": "redis", "state": "open", "version": "Redis 7.0.11"},
     ]},
    {"ip": "192.168.1.42", "hostname": "MacBook-Pro.local", "mac": "F4:5C:89:AB:CD:EF",
     "vendor": "Apple, Inc.", "os": "Apple macOS 14 (Sonoma)", "family": "macOS", "conf": 93,
     "latency": 0.5, "vlan_id": 30, "vlan_name": "Workstations", "ports": [
        {"port_number": 22, "protocol": "tcp", "service_name": "ssh", "state": "open", "version": "OpenSSH 9.6"},
        {"port_number": 5000, "protocol": "tcp", "service_name": "airplay", "state": "open", "version": "AirPlay"},
     ]},
    {"ip": "192.168.1.55", "hostname": None, "mac": "8C:85:90:11:AA:BB",
     "vendor": "Espressif Inc.", "os": None, "family": "Unknown", "conf": None,
     "latency": 12.4, "vlan_id": 40, "vlan_name": "IoT / Guest", "ports": [
        {"port_number": 80, "protocol": "tcp", "service_name": "http", "state": "open", "version": "ESP-IDF httpd"},
     ]},
    {"ip": "192.168.1.60", "hostname": "printer-office.local", "mac": "00:26:AB:22:33:99",
     "vendor": "Hewlett Packard", "os": "Embedded (HP JetDirect)", "family": "Unknown", "conf": 55,
     "latency": 4.3, "vlan_id": 10, "vlan_name": "Management", "ports": [
        {"port_number": 80, "protocol": "tcp", "service_name": "http", "state": "open", "version": "HP JetDirect httpd"},
        {"port_number": 515, "protocol": "tcp", "service_name": "printer", "state": "open", "version": "LPD"},
        {"port_number": 9100, "protocol": "tcp", "service_name": "jetdirect", "state": "open", "version": "-"},
     ]},
    {"ip": "192.168.1.70", "hostname": "guest-phone", "mac": "A0:B1:C2:D3:E4:F5",
     "vendor": "Samsung Electronics", "os": "Android 14", "family": "Unknown", "conf": 60,
     "latency": 6.7, "vlan_id": 40, "vlan_name": "IoT / Guest", "ports": []},
    {"ip": "192.168.1.99", "hostname": None, "mac": None, "vendor": None, "os": None,
     "family": "Unknown", "conf": None, "latency": None, "vlan_id": 99, "vlan_name": "Legacy",
     "ports": [], "offline": True},
]

# One simulated Cisco switch with SNMP enabled, so the SNMP / interfaces UI
# has something realistic to show without requiring real managed hardware.
SAMPLE_SNMP_DEVICE = {
    "ip": "192.168.1.2", "hostname": "core-switch-01", "mac": "00:1B:D5:11:22:33",
    "vendor": "Cisco Systems", "os": "Cisco IOS", "family": "Linux", "conf": 97,
    "latency": 0.9, "vlan_id": 10, "vlan_name": "Management",
    "ports": [
        {"port_number": 22, "protocol": "tcp", "service_name": "ssh", "state": "open", "version": "Cisco SSH 1.99"},
        {"port_number": 23, "protocol": "tcp", "service_name": "telnet", "state": "open", "version": "Cisco telnetd"},
        {"port_number": 161, "protocol": "udp", "service_name": "snmp", "state": "open", "version": "SNMPv2c"},
    ],
    "snmp": {
        "sys_descr": "Cisco IOS Software, Catalyst 2960 Software (C2960-LANBASEK9-M), Version 15.0(2)SE11",
        "sys_name": "core-switch-01",
        "sys_uptime": "14 days, 6:56:07",
        "sys_contact": "netadmin@example.com",
        "sys_location": "Server Room Rack 3",
        "community_used": "public",
    },
    "interfaces": [
        {"if_index": 1, "if_descr": "GigabitEthernet0/1", "if_type": "ethernetCsmacd",
         "if_speed_mbps": 1000.0, "if_admin_status": "up", "if_oper_status": "up"},
        {"if_index": 2, "if_descr": "GigabitEthernet0/2", "if_type": "ethernetCsmacd",
         "if_speed_mbps": 1000.0, "if_admin_status": "up", "if_oper_status": "down"},
        {"if_index": 3, "if_descr": "GigabitEthernet0/3", "if_type": "ethernetCsmacd",
         "if_speed_mbps": 100.0, "if_admin_status": "up", "if_oper_status": "up"},
        {"if_index": 4, "if_descr": "Vlan1", "if_type": "l3ipvlan",
         "if_speed_mbps": 1000.0, "if_admin_status": "up", "if_oper_status": "up"},
    ],
}


def seed_if_empty():
    """Insert one sample completed scan if the scans table is currently empty."""
    existing = db.list_scans(limit=1)
    if existing:
        return

    # Two older historical scans first, purely so the "Scan History" line
    # chart and scan-history table have more than one data point to show.
    # These must be created BEFORE the main populated scan below so that
    # the populated scan remains the most recent (highest id) - the
    # dashboard always reads hosts from the latest completed scan.
    for target, duration, total, live in [
        ("192.168.1.0/24", 16.2, 9, 7),
        ("192.168.1.0/24", 13.9, 10, 8),
    ]:
        older_id = db.create_scan(target=target, scan_type="subnet", profile="fast")
        db.finish_scan(older_id, "completed", duration=duration, total_hosts=total, live_hosts=live)

    scan_id = db.create_scan(target="192.168.1.0/24", scan_type="subnet", profile="fast")

    live_count = 0
    for entry in SAMPLE_HOSTS:
        is_offline = entry.get("offline", False)
        status = "offline" if is_offline else "online"
        if not is_offline:
            live_count += 1

        open_ports = [p for p in entry["ports"] if p["state"] == "open"]
        score, level, recos = (0, "LOW", [])
        if not is_offline:
            score, level, recos = analyze_host(open_ports, entry["family"])

        host_id = db.insert_host(scan_id, {
            "ip_address": entry["ip"],
            "hostname": entry["hostname"],
            "mac_address": entry["mac"],
            "vendor": entry["vendor"],
            "os_name": entry["os"],
            "os_family": entry["family"],
            "os_confidence": entry["conf"],
            "status": status,
            "latency_ms": entry["latency"],
            "risk_score": score,
            "risk_level": level,
            "vlan_id": entry.get("vlan_id"),
            "vlan_name": entry.get("vlan_name"),
        })

        for p in entry["ports"]:
            db.insert_port(host_id, p)
        for r in recos:
            db.insert_recommendation(host_id, r)

    # Add the simulated Cisco switch: SNMP-managed network gear, distinct
    # from the "host discovery" devices above, so the Topology/SNMP UI has
    # something realistic to show without requiring real managed hardware.
    switch = SAMPLE_SNMP_DEVICE
    open_ports = [p for p in switch["ports"] if p["state"] == "open"]
    score, level, recos = analyze_host(open_ports, switch["family"])
    switch_host_id = db.insert_host(scan_id, {
        "ip_address": switch["ip"],
        "hostname": switch["hostname"],
        "mac_address": switch["mac"],
        "vendor": switch["vendor"],
        "os_name": switch["os"],
        "os_family": switch["family"],
        "os_confidence": switch["conf"],
        "status": "online",
        "latency_ms": switch["latency"],
        "risk_score": score,
        "risk_level": level,
        "vlan_id": switch["vlan_id"],
        "vlan_name": switch["vlan_name"],
    })
    for p in switch["ports"]:
        db.insert_port(switch_host_id, p)
    for r in recos:
        db.insert_recommendation(switch_host_id, r)
    db.insert_snmp_info(switch_host_id, switch["snmp"])
    for iface in switch["interfaces"]:
        db.insert_interface(switch_host_id, iface)
    live_count += 1

    total_hosts = len(SAMPLE_HOSTS) + 1
    db.finish_scan(scan_id, "completed", duration=14.8, total_hosts=total_hosts, live_hosts=live_count)
