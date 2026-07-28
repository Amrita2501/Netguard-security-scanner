import { useEffect, useState } from 'react'
import { FiFileText, FiFile, FiCode, FiDownload } from 'react-icons/fi'
import toast from 'react-hot-toast'
import client, { API_BASE_URL } from '../api/client'
import { Scan } from '../types'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import EmptyState from '../components/Common/EmptyState'

const FORMATS = [
  { key: 'pdf', label: 'PDF Report', icon: FiFileText, description: 'Full findings report with charts, host & risk summary, and recommendations.' },
  { key: 'csv', label: 'CSV Export', icon: FiFile, description: 'Tabular host/port/risk data for spreadsheets.' },
  { key: 'json', label: 'JSON Export', icon: FiCode, description: 'Structured raw data for programmatic use.' },
] as const

export default function Reports() {
  const [scans, setScans] = useState<Scan[]>([])
  const [scanId, setScanId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState<string | null>(null)

  useEffect(() => {
    client.get('/scans').then((res) => {
      const completed = res.data.filter((s: Scan) => s.status === 'completed')
      setScans(completed)
      if (completed.length) setScanId(completed[0].id)
    }).finally(() => setLoading(false))
  }, [])

  const download = async (format: 'pdf' | 'csv' | 'json') => {
    if (!scanId) return
    setDownloading(format)
    try {
      const token = localStorage.getItem('netscan_token')
      const res = await fetch(`${API_BASE_URL}/reports/${scanId}/${format}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `scan_${scanId}_report.${format}`
      a.click()
      window.URL.revokeObjectURL(url)
      toast.success(`${format.toUpperCase()} report downloaded`)
    } catch {
      toast.error('Failed to generate report')
    } finally {
      setDownloading(null)
    }
  }

  if (loading) return <LoadingSpinner label="Loading reports…" />

  if (scans.length === 0) {
    return <EmptyState icon={FiFileText} title="No completed scans available" description="Run a scan first, then come back here to generate reports." />
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="card p-5">
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5 block">Select a scan</label>
        <select className="input-field" value={scanId ?? ''} onChange={(e) => setScanId(Number(e.target.value))}>
          {scans.map((s) => (
            <option key={s.id} value={s.id}>
              Scan #{s.id} — {s.target} ({s.started_at.slice(0, 10)}) — {s.live_hosts} live hosts
            </option>
          ))}
        </select>
      </div>

      <div className="grid sm:grid-cols-3 gap-4">
        {FORMATS.map((f) => (
          <div key={f.key} className="card p-5 flex flex-col">
            <div className="w-10 h-10 rounded-xl bg-brand-500/10 text-brand-500 flex items-center justify-center mb-3">
              <f.icon className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-slate-800 dark:text-white">{f.label}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex-1">{f.description}</p>
            <button
              onClick={() => download(f.key)}
              disabled={downloading === f.key}
              className="btn-secondary mt-4 text-sm flex items-center justify-center gap-1.5"
            >
              <FiDownload className="w-4 h-4" />
              {downloading === f.key ? 'Generating…' : 'Download'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
