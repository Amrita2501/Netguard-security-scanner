import { useEffect, useRef, useState, FormEvent } from 'react'
import { FiSearch, FiZap, FiCpu, FiCheckCircle, FiXCircle } from 'react-icons/fi'
import toast from 'react-hot-toast'
import client, { API_BASE_URL } from '../api/client'
import { ScanProgress } from '../types'
import { useNavigate } from 'react-router-dom'

const EXAMPLES = [
  { label: 'Single IP', value: '192.168.1.10' },
  { label: 'IP Range', value: '192.168.1.1-50' },
  { label: 'Subnet (CIDR)', value: '192.168.1.0/24' },
]

export default function ScanPage() {
  const [target, setTarget] = useState('')
  const [profile, setProfile] = useState<'fast' | 'deep'>('fast')
  const [scanId, setScanId] = useState<number | null>(null)
  const [progress, setProgress] = useState<ScanProgress | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [liveMode, setLiveMode] = useState<'websocket' | 'polling' | null>(null)
  const pollRef = useRef<number | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const navigate = useNavigate()

  const startScan = async (e: FormEvent) => {
    e.preventDefault()
    if (!target.trim()) return
    setSubmitting(true)
    try {
      const { data } = await client.post('/scans', { target: target.trim(), profile })
      setScanId(data.scan_id)
      setProgress({ phase: 'discovery', percent: 2 })
      toast.success('Scan started')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to start scan')
    } finally {
      setSubmitting(false)
    }
  }

  const startPolling = (id: number) => {
    setLiveMode('polling')
    pollRef.current = window.setInterval(async () => {
      try {
        const { data } = await client.get(`/scans/${id}/progress`)
        setProgress(data)
        if (data.phase === 'completed' || data.phase === 'failed') {
          if (pollRef.current) clearInterval(pollRef.current)
          if (data.phase === 'completed') toast.success('Scan complete')
          if (data.phase === 'failed') toast.error(`Scan failed: ${data.error ?? 'unknown error'}`)
        }
      } catch {
        if (pollRef.current) clearInterval(pollRef.current)
      }
    }, 1200)
  }

  useEffect(() => {
    if (!scanId) return

    // Prefer a real-time WebSocket connection; fall back to REST polling
    // automatically if the socket can't be established (proxies, older
    // deployments without WS support, etc).
    const token = localStorage.getItem('netscan_token')
    const wsUrl = API_BASE_URL.replace(/^http/, 'ws').replace(/\/api$/, '') + `/ws/scans/${scanId}?token=${token}`
    let fellBack = false

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      const fallbackTimer = window.setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          fellBack = true
          ws.close()
          startPolling(scanId)
        }
      }, 2500)

      ws.onopen = () => {
        window.clearTimeout(fallbackTimer)
        setLiveMode('websocket')
      }
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        setProgress(data)
        if (data.phase === 'completed') toast.success('Scan complete')
        if (data.phase === 'failed') toast.error(`Scan failed: ${data.error ?? 'unknown error'}`)
      }
      ws.onerror = () => {
        window.clearTimeout(fallbackTimer)
        if (!fellBack) {
          fellBack = true
          startPolling(scanId)
        }
      }
      ws.onclose = () => {
        window.clearTimeout(fallbackTimer)
      }
    } catch {
      startPolling(scanId)
    }

    return () => {
      wsRef.current?.close()
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [scanId])

  const isRunning = progress && progress.phase !== 'completed' && progress.phase !== 'failed'

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="card p-6">
        <h2 className="font-semibold text-slate-800 dark:text-white mb-1">Start a Network Scan</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-5">
          Scan a single IP, an IP range, or an entire subnet. Real scans require <span className="font-mono">nmap</span> installed
          locally and appropriate network access — see the setup guide.
        </p>

        <form onSubmit={startScan} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5 block">Target</label>
            <div className="relative">
              <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
              <input
                className="input-field pl-9 font-mono"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="192.168.1.0/24"
                disabled={!!isRunning}
              />
            </div>
            <div className="flex gap-2 mt-2 flex-wrap">
              {EXAMPLES.map((ex) => (
                <button
                  type="button"
                  key={ex.value}
                  onClick={() => setTarget(ex.value)}
                  className="text-xs px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                >
                  {ex.label}: <span className="font-mono">{ex.value}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5 block">Scan Profile</label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setProfile('fast')}
                disabled={!!isRunning}
                className={`flex items-center gap-2 p-3 rounded-xl border text-sm font-medium transition-colors
                  ${profile === 'fast'
                    ? 'border-brand-500 bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400'
                    : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300'}`}
              >
                <FiZap className="w-4 h-4" /> Fast (top ports)
              </button>
              <button
                type="button"
                onClick={() => setProfile('deep')}
                disabled={!!isRunning}
                className={`flex items-center gap-2 p-3 rounded-xl border text-sm font-medium transition-colors
                  ${profile === 'deep'
                    ? 'border-brand-500 bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400'
                    : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300'}`}
              >
                <FiCpu className="w-4 h-4" /> Deep (all 65535 ports)
              </button>
            </div>
          </div>

          <button type="submit" disabled={submitting || !!isRunning} className="btn-primary w-full py-2.5">
            {isRunning ? 'Scan in progress…' : 'Start Scan'}
          </button>
        </form>
      </div>

      {progress && (
        <div className="card p-6 animate-fadeIn">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-slate-800 dark:text-white capitalize">{progress.phase}</h3>
            <div className="flex items-center gap-2">
              {liveMode && (
                <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400">
                  {liveMode === 'websocket' ? 'Live' : 'Polling'}
                </span>
              )}
              {progress.phase === 'completed' && <FiCheckCircle className="text-emerald-500 w-5 h-5" />}
              {progress.phase === 'failed' && <FiXCircle className="text-red-500 w-5 h-5" />}
            </div>
          </div>
          <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden mb-2">
            <div
              className="h-full bg-brand-500 rounded-full transition-all duration-500"
              style={{ width: `${progress.percent}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400">
            <span>{progress.current_host ? `Scanning ${progress.current_host}` : 'Working…'}</span>
            <span>{progress.percent}%</span>
          </div>
          {progress.total !== undefined && progress.total > 0 && (
            <p className="text-xs text-slate-400 mt-1">{progress.current ?? 0} / {progress.total} hosts processed</p>
          )}

          {progress.phase === 'completed' && scanId && (
            <button onClick={() => navigate('/hosts')} className="btn-secondary mt-4 text-sm">
              View discovered hosts →
            </button>
          )}
        </div>
      )}
    </div>
  )
}
