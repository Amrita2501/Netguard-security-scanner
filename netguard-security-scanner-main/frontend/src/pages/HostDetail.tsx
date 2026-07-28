import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { FiArrowLeft, FiCpu, FiWifi, FiHash, FiClock, FiShare2, FiShield, FiAlertOctagon } from 'react-icons/fi'
import client from '../api/client'
import { Host, SnmpResponse, CveResponse } from '../types'
import RiskBadge from '../components/Badges/RiskBadge'
import StatusBadge from '../components/Badges/StatusBadge'
import LoadingSpinner from '../components/Common/LoadingSpinner'

const SEVERITY_COLORS: Record<string, string> = {
  LOW: 'text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-500/10',
  MEDIUM: 'text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-500/10',
  HIGH: 'text-orange-600 dark:text-orange-400 bg-orange-100 dark:bg-orange-500/10',
  CRITICAL: 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-500/10',
}

export default function HostDetail() {
  const { id } = useParams()
  const [host, setHost] = useState<Host | null>(null)
  const [snmp, setSnmp] = useState<SnmpResponse | null>(null)
  const [cves, setCves] = useState<CveResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [cvesLoading, setCvesLoading] = useState(true)

  useEffect(() => {
    client.get(`/hosts/${id}`).then((res) => setHost(res.data)).finally(() => setLoading(false))
    client.get(`/hosts/${id}/snmp`).then((res) => setSnmp(res.data)).catch(() => setSnmp(null))
    client.get(`/hosts/${id}/cves`).then((res) => setCves(res.data)).catch(() => setCves(null)).finally(() => setCvesLoading(false))
  }, [id])

  if (loading) return <LoadingSpinner label="Loading host details…" />
  if (!host) return <p className="text-slate-500">Host not found.</p>

  const openPorts = host.ports.filter((p) => p.state === 'open')

  return (
    <div className="space-y-6">
      <Link to="/hosts" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-brand-500">
        <FiArrowLeft className="w-4 h-4" /> Back to hosts
      </Link>

      <div className="card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold font-mono text-slate-900 dark:text-white">{host.ip_address}</h2>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">{host.hostname ?? 'No hostname resolved'}</p>
          </div>
          <div className="flex gap-2">
            <StatusBadge status={host.status} />
            <RiskBadge level={host.risk_level} />
            {host.vlan_name && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-violet-100 dark:bg-violet-500/10 text-violet-600 dark:text-violet-400">
                VLAN {host.vlan_id} · {host.vlan_name}
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
          <InfoStat icon={FiHash} label="MAC Address" value={host.mac_address ?? '—'} mono />
          <InfoStat icon={FiCpu} label="Vendor" value={host.vendor ?? 'Unknown'} />
          <InfoStat icon={FiWifi} label="Latency" value={host.latency_ms ? `${host.latency_ms} ms` : '—'} />
          <InfoStat icon={FiClock} label="Last Seen" value={host.last_seen ? new Date(host.last_seen).toLocaleString() : '—'} />
        </div>

        <div className="mt-6 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
          <p className="text-xs uppercase tracking-wide text-slate-400 font-medium mb-1">Operating System (Nmap fingerprint)</p>
          <div className="flex items-center gap-3">
            <p className="font-semibold text-slate-800 dark:text-white">{host.os_name ?? 'Unknown'}</p>
            {host.os_confidence != null && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-brand-100 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 font-medium">
                {host.os_confidence}% confidence
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 dark:text-white mb-4">Open Ports & Services ({openPorts.length})</h3>
        {openPorts.length === 0 ? (
          <p className="text-sm text-slate-400">No open ports detected on this host.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-400 uppercase border-b border-slate-200 dark:border-slate-800">
                  <th className="py-2 pr-4 font-medium">Port</th>
                  <th className="py-2 pr-4 font-medium">Protocol</th>
                  <th className="py-2 pr-4 font-medium">Service</th>
                  <th className="py-2 pr-4 font-medium">State</th>
                  <th className="py-2 pr-4 font-medium">Version</th>
                </tr>
              </thead>
              <tbody>
                {openPorts.map((p) => (
                  <tr key={p.id} className="border-b border-slate-100 dark:border-slate-800/60">
                    <td className="py-2.5 pr-4 font-mono font-medium">{p.port_number}</td>
                    <td className="py-2.5 pr-4 uppercase text-xs text-slate-500">{p.protocol}</td>
                    <td className="py-2.5 pr-4">{p.service_name ?? '—'}</td>
                    <td className="py-2.5 pr-4">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                        {p.state}
                      </span>
                    </td>
                    <td className="py-2.5 pr-4 text-slate-500 dark:text-slate-400">{p.version ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {snmp?.available && snmp.info && (
        <div className="card p-6">
          <h3 className="font-semibold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
            <FiShare2 className="w-4 h-4" /> SNMP Device Info
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-5">
            <InfoStat icon={FiCpu} label="System Name" value={snmp.info.sys_name ?? '—'} />
            <InfoStat icon={FiClock} label="Uptime" value={snmp.info.sys_uptime ?? '—'} />
            <InfoStat icon={FiHash} label="Community" value={snmp.info.community_used ?? '—'} mono />
            <InfoStat icon={FiWifi} label="Location" value={snmp.info.sys_location ?? '—'} />
            <InfoStat icon={FiCpu} label="Contact" value={snmp.info.sys_contact ?? '—'} />
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 mb-5">
            <p className="text-xs uppercase tracking-wide text-slate-400 font-medium mb-1">System Description</p>
            <p className="text-sm text-slate-700 dark:text-slate-200 font-mono break-words">{snmp.info.sys_descr}</p>
          </div>

          {snmp.interfaces.length > 0 && (
            <>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Interfaces ({snmp.interfaces.length})
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-slate-400 uppercase border-b border-slate-200 dark:border-slate-800">
                      <th className="py-2 pr-4 font-medium">Interface</th>
                      <th className="py-2 pr-4 font-medium">Type</th>
                      <th className="py-2 pr-4 font-medium">Speed</th>
                      <th className="py-2 pr-4 font-medium">Admin</th>
                      <th className="py-2 pr-4 font-medium">Operational</th>
                    </tr>
                  </thead>
                  <tbody>
                    {snmp.interfaces.map((iface) => (
                      <tr key={iface.id} className="border-b border-slate-100 dark:border-slate-800/60">
                        <td className="py-2.5 pr-4 font-medium">{iface.if_descr}</td>
                        <td className="py-2.5 pr-4 text-slate-500 dark:text-slate-400">{iface.if_type}</td>
                        <td className="py-2.5 pr-4 text-slate-500 dark:text-slate-400">
                          {iface.if_speed_mbps ? `${iface.if_speed_mbps} Mbps` : '—'}
                        </td>
                        <td className="py-2.5 pr-4">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${iface.if_admin_status === 'up' ? 'bg-emerald-100 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' : 'bg-slate-100 dark:bg-slate-700 text-slate-500'}`}>
                            {iface.if_admin_status}
                          </span>
                        </td>
                        <td className="py-2.5 pr-4">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${iface.if_oper_status === 'up' ? 'bg-emerald-100 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' : 'bg-slate-100 dark:bg-slate-700 text-slate-500'}`}>
                            {iface.if_oper_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <FiAlertOctagon className="w-4 h-4" /> Known Vulnerabilities (CVE)
        </h3>
        {cvesLoading ? (
          <LoadingSpinner label="Checking for known vulnerabilities…" />
        ) : !cves || cves.findings.length === 0 ? (
          <p className="text-sm text-slate-400">No known CVEs matched for the detected service versions on this host.</p>
        ) : (
          <div className="space-y-4">
            {cves.findings.map((finding) => (
              <div key={finding.port_number}>
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2">
                  Port {finding.port_number} · {finding.service_name} {finding.version && `(${finding.version})`}
                </p>
                <div className="space-y-2">
                  {finding.cves.map((cve) => (
                    <div key={cve.cve_id} className="flex gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                      <span className={`shrink-0 text-xs font-semibold px-2.5 py-1 rounded-full ${SEVERITY_COLORS[cve.severity] ?? SEVERITY_COLORS.MEDIUM}`}>
                        {cve.severity}
                      </span>
                      <div>
                        <p className="font-medium text-sm text-slate-800 dark:text-white font-mono">
                          {cve.cve_id}
                          {cve.cvss_score != null && (
                            <span className="ml-2 text-xs font-normal text-slate-400">CVSS {cve.cvss_score}</span>
                          )}
                        </p>
                        <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{cve.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {host.recommendations && host.recommendations.length > 0 && (
        <div className="card p-6">
          <h3 className="font-semibold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
            <FiShield className="w-4 h-4" /> Security Recommendations
          </h3>
          <div className="space-y-3">
            {host.recommendations.map((rec) => (
              <div key={rec.id} className="flex gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                <RiskBadge level={rec.severity} />
                <div>
                  <p className="font-medium text-sm text-slate-800 dark:text-white">{rec.title}</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{rec.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function InfoStat({ icon: Icon, label, value, mono }: { icon: any; label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start gap-2.5">
      <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center shrink-0">
        <Icon className="w-4 h-4 text-slate-500" />
      </div>
      <div>
        <p className="text-xs text-slate-400">{label}</p>
        <p className={`text-sm font-medium text-slate-800 dark:text-white ${mono ? 'font-mono' : ''}`}>{value}</p>
      </div>
    </div>
  )
}
