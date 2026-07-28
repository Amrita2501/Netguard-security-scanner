import { useEffect, useState } from 'react'
import { FiHardDrive, FiWifi, FiWifiOff, FiLock, FiAlertTriangle, FiClock } from 'react-icons/fi'
import client from '../api/client'
import StatCard from '../components/Cards/StatCard'
import ProtocolPieChart from '../components/Charts/ProtocolPieChart'
import TopPortsBarChart from '../components/Charts/TopPortsBarChart'
import ScanHistoryLineChart from '../components/Charts/ScanHistoryLineChart'
import RiskDistributionChart from '../components/Charts/RiskDistributionChart'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import { DashboardCharts, DashboardSummary } from '../types'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [charts, setCharts] = useState<DashboardCharts | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [summaryRes, chartsRes] = await Promise.all([
          client.get('/dashboard/summary'),
          client.get('/dashboard/charts'),
        ])
        setSummary(summaryRes.data)
        setCharts(chartsRes.data)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <LoadingSpinner label="Loading dashboard…" />
  if (!summary || !charts) return null

  const hasData = summary.total_devices > 0

  return (
    <div className="space-y-6">
      {!hasData && (
        <div className="card p-5 bg-brand-50 dark:bg-brand-500/5 border-brand-200 dark:border-brand-500/20 flex items-center justify-between flex-wrap gap-3">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            No scans yet. Run your first network scan to populate live data.
          </p>
          <Link to="/scan" className="btn-primary text-sm px-4 py-2">Start a Scan</Link>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard label="Total Devices" value={summary.total_devices} icon={FiHardDrive} accent="brand" />
        <StatCard label="Live Hosts" value={summary.live_hosts} icon={FiWifi} accent="emerald" />
        <StatCard label="Offline Hosts" value={summary.offline_hosts} icon={FiWifiOff} accent="slate" />
        <StatCard label="Open Ports" value={summary.total_open_ports} icon={FiLock} accent="amber" />
        <StatCard label="High Risk Devices" value={summary.high_risk_devices} icon={FiAlertTriangle} accent="red" />
        <StatCard
          label="Last Scan Duration"
          value={summary.scan_duration ? summary.scan_duration.toFixed(1) : '—'}
          suffix={summary.scan_duration ? 's' : ''}
          icon={FiClock}
          accent="brand"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card p-5 lg:col-span-2">
          <h3 className="font-semibold text-slate-800 dark:text-white mb-2">Scan History</h3>
          <ScanHistoryLineChart data={charts.scan_history} />
        </div>
        <div className="card p-5">
          <h3 className="font-semibold text-slate-800 dark:text-white mb-2">Risk Distribution</h3>
          <RiskDistributionChart distribution={summary.risk_distribution} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card p-5">
          <h3 className="font-semibold text-slate-800 dark:text-white mb-2">Service / Protocol Distribution</h3>
          <ProtocolPieChart data={charts.protocol_distribution} />
        </div>
        <div className="card p-5">
          <h3 className="font-semibold text-slate-800 dark:text-white mb-2">Top Open Ports</h3>
          <TopPortsBarChart data={charts.top_open_ports} />
        </div>
      </div>
    </div>
  )
}
