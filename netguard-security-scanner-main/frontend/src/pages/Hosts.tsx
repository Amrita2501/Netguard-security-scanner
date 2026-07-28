import { useEffect, useMemo, useState } from 'react'
import { FiSearch, FiServer } from 'react-icons/fi'
import { Link } from 'react-router-dom'
import client from '../api/client'
import { Host, RiskLevel } from '../types'
import RiskBadge from '../components/Badges/RiskBadge'
import StatusBadge from '../components/Badges/StatusBadge'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import EmptyState from '../components/Common/EmptyState'

const RISK_FILTERS: (RiskLevel | 'ALL')[] = ['ALL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

export default function Hosts() {
  const [hosts, setHosts] = useState<Host[]>([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [riskFilter, setRiskFilter] = useState<RiskLevel | 'ALL'>('ALL')

  useEffect(() => {
    client.get('/hosts/latest').then((res) => setHosts(res.data)).finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return hosts.filter((h) => {
      const matchesRisk = riskFilter === 'ALL' || h.risk_level === riskFilter
      if (!matchesRisk) return false
      if (!q) return true
      const servicesMatch = h.ports.some((p) => p.service_name?.toLowerCase().includes(q) || String(p.port_number).includes(q))
      return (
        h.ip_address.toLowerCase().includes(q) ||
        (h.hostname ?? '').toLowerCase().includes(q) ||
        (h.mac_address ?? '').toLowerCase().includes(q) ||
        (h.os_name ?? '').toLowerCase().includes(q) ||
        (h.vendor ?? '').toLowerCase().includes(q) ||
        servicesMatch
      )
    })
  }, [hosts, query, riskFilter])

  if (loading) return <LoadingSpinner label="Loading hosts…" />

  return (
    <div className="space-y-4">
      <div className="card p-4 flex flex-col sm:flex-row gap-3 sm:items-center">
        <div className="relative flex-1">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
          <input
            className="input-field pl-9"
            placeholder="Search by hostname, IP, MAC, OS, vendor, port, or service…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {RISK_FILTERS.map((r) => (
            <button
              key={r}
              onClick={() => setRiskFilter(r)}
              className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors
                ${riskFilter === r
                  ? 'bg-brand-500 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'}`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <div className="card overflow-x-auto">
        {filtered.length === 0 ? (
          <EmptyState icon={FiServer} title="No hosts match your filters" description="Try clearing your search or risk filter, or run a new scan." />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-400 uppercase border-b border-slate-200 dark:border-slate-800">
                <th className="px-4 py-3 font-medium">IP Address</th>
                <th className="px-4 py-3 font-medium">Hostname</th>
                <th className="px-4 py-3 font-medium">Vendor</th>
                <th className="px-4 py-3 font-medium">OS</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Open Ports</th>
                <th className="px-4 py-3 font-medium">Risk</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((h) => (
                <tr key={h.id} className="border-b border-slate-100 dark:border-slate-800/60 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                  <td className="px-4 py-3">
                    <Link to={`/hosts/${h.id}`} className="font-mono font-medium text-brand-600 dark:text-brand-400 hover:underline">
                      {h.ip_address}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{h.hostname ?? '—'}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{h.vendor ?? '—'}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{h.os_name ?? 'Unknown'}</td>
                  <td className="px-4 py-3"><StatusBadge status={h.status} /></td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{h.ports.filter(p => p.state === 'open').length}</td>
                  <td className="px-4 py-3"><RiskBadge level={h.risk_level} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
