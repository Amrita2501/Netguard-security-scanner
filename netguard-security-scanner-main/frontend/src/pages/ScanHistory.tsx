import { useEffect, useState } from 'react'
import { FiTrash2, FiClock, FiDownload } from 'react-icons/fi'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'
import client, { API_BASE_URL } from '../api/client'
import { Scan } from '../types'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import EmptyState from '../components/Common/EmptyState'

const STATUS_STYLES: Record<string, string> = {
  completed: 'bg-emerald-100 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  running: 'bg-amber-100 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400',
  failed: 'bg-red-100 dark:bg-red-500/10 text-red-600 dark:text-red-400',
}

export default function ScanHistory() {
  const [scans, setScans] = useState<Scan[]>([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    client.get('/scans').then((res) => setScans(res.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleDelete = async (id: number) => {
    if (!confirm(`Delete scan #${id} and all associated host data?`)) return
    await client.delete(`/scans/${id}`)
    toast.success('Scan deleted')
    load()
  }

  const downloadReport = async (id: number, format: 'pdf' | 'csv' | 'json') => {
    const token = localStorage.getItem('netscan_token')
    const res = await fetch(`${API_BASE_URL}/reports/${id}/${format}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `scan_${id}_report.${format}`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  if (loading) return <LoadingSpinner label="Loading scan history…" />

  return (
    <div className="card overflow-x-auto">
      {scans.length === 0 ? (
        <EmptyState icon={FiClock} title="No scans yet" description="Your scan history will appear here once you run your first scan." />
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-400 uppercase border-b border-slate-200 dark:border-slate-800">
              <th className="px-4 py-3 font-medium">ID</th>
              <th className="px-4 py-3 font-medium">Target</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Profile</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Live / Total</th>
              <th className="px-4 py-3 font-medium">Duration</th>
              <th className="px-4 py-3 font-medium">Started</th>
              <th className="px-4 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {scans.map((s) => (
              <tr key={s.id} className="border-b border-slate-100 dark:border-slate-800/60 hover:bg-slate-50 dark:hover:bg-slate-800/40">
                <td className="px-4 py-3 font-mono text-slate-500">#{s.id}</td>
                <td className="px-4 py-3 font-mono font-medium">{s.target}</td>
                <td className="px-4 py-3 capitalize text-slate-600 dark:text-slate-300">{s.scan_type}</td>
                <td className="px-4 py-3 capitalize text-slate-600 dark:text-slate-300">{s.profile}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${STATUS_STYLES[s.status]}`}>{s.status}</span>
                </td>
                <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{s.live_hosts} / {s.total_hosts}</td>
                <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{s.duration_seconds ? `${s.duration_seconds}s` : '—'}</td>
                <td className="px-4 py-3 text-slate-500 text-xs">{new Date(s.started_at).toLocaleString()}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1.5">
                    {s.status === 'completed' && (
                      <>
                        <button onClick={() => downloadReport(s.id, 'pdf')} title="Download PDF" aria-label={`Download PDF report for scan ${s.id}`} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500">
                          <FiDownload className="w-4 h-4" />
                        </button>
                        <Link to="/reports" className="text-xs text-brand-500 hover:underline px-1">Reports</Link>
                      </>
                    )}
                    <button onClick={() => handleDelete(s.id)} title="Delete" aria-label={`Delete scan ${s.id}`} className="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 text-red-500">
                      <FiTrash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
