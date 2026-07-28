import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'
import { Scan, Topology as TopologyType } from '../types'
import NetworkTopology from '../components/Topology/NetworkTopology'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import EmptyState from '../components/Common/EmptyState'
import { FiShare2 } from 'react-icons/fi'

export default function TopologyPage() {
  const [scans, setScans] = useState<Scan[]>([])
  const [scanId, setScanId] = useState<number | null>(null)
  const [topology, setTopology] = useState<TopologyType | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    client.get('/scans').then((res) => {
      const completed = res.data.filter((s: Scan) => s.status === 'completed')
      setScans(completed)
      if (completed.length) setScanId(completed[0].id)
      else setLoading(false)
    })
  }, [])

  useEffect(() => {
    if (!scanId) return
    setLoading(true)
    client.get(`/topology/${scanId}`).then((res) => setTopology(res.data)).finally(() => setLoading(false))
  }, [scanId])

  return (
    <div className="space-y-4">
      <div className="card p-4 flex flex-wrap items-center gap-3 justify-between">
        <div>
          <h2 className="font-semibold text-slate-800 dark:text-white">Interactive Network Topology</h2>
          <p className="text-xs text-slate-400">Drag nodes to rearrange, scroll to zoom, click a host for details</p>
        </div>
        {scans.length > 0 && (
          <select
            className="input-field w-auto"
            value={scanId ?? ''}
            onChange={(e) => setScanId(Number(e.target.value))}
          >
            {scans.map((s) => (
              <option key={s.id} value={s.id}>
                Scan #{s.id} — {s.target} ({s.started_at.slice(0, 10)})
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="card p-5">
        {loading ? (
          <LoadingSpinner label="Building topology…" />
        ) : !topology || topology.nodes.length <= 1 ? (
          <EmptyState icon={FiShare2} title="No topology to display" description="Run a scan first to generate a network topology graph." />
        ) : (
          <NetworkTopology topology={topology} onSelectHost={(id) => navigate(`/hosts/${id}`)} />
        )}
      </div>
    </div>
  )
}
