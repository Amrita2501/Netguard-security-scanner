"""
SNMP polling module.

Queries SNMPv2c-enabled network devices (routers, switches, managed APs) for
system identity (sysDescr/sysName/sysUptime/sysContact/sysLocation) and
interface tables (IF-MIB: ifDescr/ifType/ifSpeed/ifOperStatus/ifAdminStatus),
which is the kind of data a real Cisco switch/router exposes over SNMP.

Uses `puresnmp` (pure-Python, asyncio-based, no compiled C dependency and no
net-snmp system package required) rather than the classic `pysnmp` hlapi,
which no longer supports modern Python out of the box.

Most consumer/home-network devices do NOT have SNMP enabled, so every call
here is wrapped with a short timeout and fails soft (returns None) - this is
expected and normal, not an error condition, on networks without managed
switches/routers.
"""
import asyncio
import logging
from typing import Optional

from puresnmp import Client, V2C, PyWrapper
from puresnmp.exc import Timeout as SnmpTimeout

logger = logging.getLogger("netguard.snmp")

SNMP_PORT = 161
SNMP_TIMEOUT_SECONDS = 1.5

# Standard MIB-II OIDs (RFC1213 / IF-MIB) - present on virtually every
# SNMP-speaking device, including Cisco IOS/IOS-XE switches and routers.
OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"
OID_SYS_UPTIME = "1.3.6.1.2.1.1.3.0"
OID_SYS_CONTACT = "1.3.6.1.2.1.1.4.0"
OID_SYS_NAME = "1.3.6.1.2.1.1.5.0"
OID_SYS_LOCATION = "1.3.6.1.2.1.1.6.0"

OID_IF_DESCR = "1.3.6.1.2.1.2.2.1.2"
OID_IF_TYPE = "1.3.6.1.2.1.2.2.1.3"
OID_IF_SPEED = "1.3.6.1.2.1.2.2.1.5"
OID_IF_ADMIN_STATUS = "1.3.6.1.2.1.2.2.1.7"
OID_IF_OPER_STATUS = "1.3.6.1.2.1.2.2.1.8"

IF_TYPE_NAMES = {
    1: "other", 6: "ethernetCsmacd", 24: "softwareLoopback",
    131: "tunnel", 135: "l2vlan", 136: "l3ipvlan", 161: "ieee8023adLag",
    71: "ieee80211", 53: "propVirtual", 209: "bridge",
}
IF_STATUS_NAMES = {1: "up", 2: "down", 3: "testing", 4: "unknown", 5: "dormant",
                    6: "notPresent", 7: "lowerLayerDown"}


def _decode(value) -> str:
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="replace")
        except Exception:
            return value.hex()
    return str(value)


async def _query_device_async(ip: str, community: str) -> Optional[dict]:
    client = PyWrapper(Client(ip, V2C(community), port=SNMP_PORT))

    async def get(oid):
        return await asyncio.wait_for(client.get(oid), timeout=SNMP_TIMEOUT_SECONDS)

    try:
        sys_descr = _decode(await get(OID_SYS_DESCR))
    except (asyncio.TimeoutError, SnmpTimeout, OSError, Exception) as exc:
        # No SNMP response at all -> device doesn't speak SNMP (or wrong community).
        logger.debug("SNMP probe to %s got no response (%s) - skipping", ip, exc.__class__.__name__)
        return None

    async def safe_get(oid, default=None):
        try:
            return _decode(await get(oid))
        except Exception:
            return default

    sys_name = await safe_get(OID_SYS_NAME)
    sys_uptime = await safe_get(OID_SYS_UPTIME)
    sys_contact = await safe_get(OID_SYS_CONTACT)
    sys_location = await safe_get(OID_SYS_LOCATION)

    interfaces = []
    try:
        descr_map, type_map, speed_map, admin_map, oper_map = {}, {}, {}, {}, {}

        async def walk_into(oid, target_map):
            async for row in client.walk(oid):
                idx = row.oid.split(".")[-1]
                target_map[idx] = row.value

        await asyncio.wait_for(walk_into(OID_IF_DESCR, descr_map), timeout=SNMP_TIMEOUT_SECONDS * 2)
        await asyncio.wait_for(walk_into(OID_IF_TYPE, type_map), timeout=SNMP_TIMEOUT_SECONDS * 2)
        await asyncio.wait_for(walk_into(OID_IF_SPEED, speed_map), timeout=SNMP_TIMEOUT_SECONDS * 2)
        await asyncio.wait_for(walk_into(OID_IF_ADMIN_STATUS, admin_map), timeout=SNMP_TIMEOUT_SECONDS * 2)
        await asyncio.wait_for(walk_into(OID_IF_OPER_STATUS, oper_map), timeout=SNMP_TIMEOUT_SECONDS * 2)

        for idx, descr in descr_map.items():
            if_type = int(type_map.get(idx, 1)) if idx in type_map else 1
            speed = int(speed_map.get(idx, 0)) if idx in speed_map else 0
            admin = int(admin_map.get(idx, 4)) if idx in admin_map else 4
            oper = int(oper_map.get(idx, 4)) if idx in oper_map else 4
            interfaces.append({
                "if_index": int(idx),
                "if_descr": _decode(descr),
                "if_type": IF_TYPE_NAMES.get(if_type, f"type-{if_type}"),
                "if_speed_mbps": round(speed / 1_000_000, 1) if speed else None,
                "if_admin_status": IF_STATUS_NAMES.get(admin, "unknown"),
                "if_oper_status": IF_STATUS_NAMES.get(oper, "unknown"),
            })
        interfaces.sort(key=lambda i: i["if_index"])
    except Exception as exc:
        # Interface table walk failed/partial - still return what we have on
        # sysDescr etc. Worth a warning (not debug) since the device DID
        # respond to SNMP, so a failed interface walk is more likely a real
        # issue (e.g. non-standard MIB) than an absent agent.
        logger.warning("SNMP interface table walk for %s failed partway: %s", ip, exc)

    return {
        "sys_descr": sys_descr,
        "sys_name": sys_name,
        "sys_uptime": sys_uptime,
        "sys_contact": sys_contact,
        "sys_location": sys_location,
        "community_used": community,
        "interfaces": interfaces,
    }


def query_device(ip: str, community: str = "public") -> Optional[dict]:
    """
    Synchronous entry point (safe to call from the scanner's background
    thread, which is not the FastAPI event loop thread).
    Returns None if the device does not respond to SNMP.
    """
    try:
        return asyncio.run(_query_device_async(ip, community))
    except Exception as exc:
        logger.warning("Unexpected error running SNMP probe against %s: %s", ip, exc)
        return None
