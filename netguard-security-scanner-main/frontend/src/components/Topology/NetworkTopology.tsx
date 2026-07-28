import { useMemo, useRef, useState, useCallback, WheelEvent, MouseEvent as ReactMouseEvent } from 'react'
import { Topology, RiskLevel } from '../../types'

const RISK_COLORS: Record<RiskLevel, string> = {
  LOW: '#22c55e',
  MEDIUM: '#eab308',
  HIGH: '#f97316',
  CRITICAL: '#ef4444',
}
const VLAN_HUB_COLOR = '#8b5cf6'

interface LayoutNode {
  id: string
  x: number
  y: number
  label: string
  type: 'network' | 'vlan' | 'host'
  status?: string
  risk_level?: RiskLevel
  os_family?: string
  hostname?: string | null
  vlan_name?: string
}

const WIDTH = 900
const HEIGHT = 560

function buildRadialLayout(topology: Topology): LayoutNode[] {
  const centerX = WIDTH / 2
  const centerY = HEIGHT / 2
  const vlanNodes = topology.nodes.filter((n) => n.type === 'vlan')
  const vlanRadius = Math.min(WIDTH, HEIGHT) / 2 - 190

  const layout: LayoutNode[] = []

  topology.nodes.forEach((n) => {
    if (n.type === 'network') {
      layout.push({ ...n, x: centerX, y: centerY })
      return
    }
    if (n.type === 'vlan') {
      const idx = vlanNodes.findIndex((v) => v.id === n.id)
      const angle = (idx / Math.max(vlanNodes.length, 1)) * Math.PI * 2 - Math.PI / 2
      layout.push({
        ...n,
        x: centerX + vlanRadius * Math.cos(angle),
        y: centerY + vlanRadius * Math.sin(angle),
      })
    }
  })

  // Place hosts in a small satellite ring around their parent VLAN hub.
  vlanNodes.forEach((vlanNode) => {
    const hubLayout = layout.find((l) => l.id === vlanNode.id)!
    const hostEdges = topology.edges.filter((e) => e.source === vlanNode.id)
    const hostSatelliteRadius = 95
    hostEdges.forEach((edge, idx) => {
      const hostNode = topology.nodes.find((n) => n.id === edge.target)
      if (!hostNode) return
      const angle = (idx / Math.max(hostEdges.length, 1)) * Math.PI * 2
      layout.push({
        ...hostNode,
        x: hubLayout.x + hostSatelliteRadius * Math.cos(angle),
        y: hubLayout.y + hostSatelliteRadius * Math.sin(angle),
      })
    })
  })

  return layout
}

export default function NetworkTopology({ topology, onSelectHost }: {
  topology: Topology
  onSelectHost?: (hostId: string) => void
}) {
  const [nodes, setNodes] = useState<LayoutNode[]>(() => buildRadialLayout(topology))
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 })
  const [draggingId, setDraggingId] = useState<string | null>(null)
  const [panning, setPanning] = useState(false)
  const lastPos = useRef({ x: 0, y: 0 })
  const svgRef = useRef<SVGSVGElement>(null)

  const edges = useMemo(() => topology.edges, [topology.edges])

  const toSvgPoint = useCallback((clientX: number, clientY: number) => {
    const svg = svgRef.current
    if (!svg) return { x: 0, y: 0 }
    const rect = svg.getBoundingClientRect()
    const x = (clientX - rect.left - transform.x) / transform.scale
    const y = (clientY - rect.top - transform.y) / transform.scale
    return { x, y }
  }, [transform])

  const handleNodeMouseDown = (id: string) => (e: ReactMouseEvent) => {
    e.stopPropagation()
    setDraggingId(id)
  }

  const handleBackgroundMouseDown = (e: ReactMouseEvent) => {
    setPanning(true)
    lastPos.current = { x: e.clientX, y: e.clientY }
  }

  const handleMouseMove = (e: ReactMouseEvent) => {
    if (draggingId) {
      const p = toSvgPoint(e.clientX, e.clientY)
      setNodes((prev) => prev.map((n) => (n.id === draggingId ? { ...n, x: p.x, y: p.y } : n)))
    } else if (panning) {
      const dx = e.clientX - lastPos.current.x
      const dy = e.clientY - lastPos.current.y
      lastPos.current = { x: e.clientX, y: e.clientY }
      setTransform((t) => ({ ...t, x: t.x + dx, y: t.y + dy }))
    }
  }

  const handleMouseUp = () => {
    setDraggingId(null)
    setPanning(false)
  }

  const handleWheel = (e: WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -0.08 : 0.08
    setTransform((t) => ({ ...t, scale: Math.min(2.5, Math.max(0.4, t.scale + delta)) }))
  }

  const nodeById = (id: string) => nodes.find((n) => n.id === id)

  return (
    <div className="relative">
      <div className="absolute top-3 right-3 z-10 flex gap-2">
        <button
          onClick={() => setTransform((t) => ({ ...t, scale: Math.min(2.5, t.scale + 0.15) }))}
          className="w-8 h-8 rounded-lg bg-panel-light dark:bg-panel-dark border border-slate-200 dark:border-slate-700 text-sm font-bold hover:bg-slate-50 dark:hover:bg-slate-800"
          aria-label="Zoom in"
        >+</button>
        <button
          onClick={() => setTransform((t) => ({ ...t, scale: Math.max(0.4, t.scale - 0.15) }))}
          className="w-8 h-8 rounded-lg bg-panel-light dark:bg-panel-dark border border-slate-200 dark:border-slate-700 text-sm font-bold hover:bg-slate-50 dark:hover:bg-slate-800"
          aria-label="Zoom out"
        >-</button>
        <button
          onClick={() => { setTransform({ x: 0, y: 0, scale: 1 }); setNodes(buildRadialLayout(topology)) }}
          className="px-3 h-8 rounded-lg bg-panel-light dark:bg-panel-dark border border-slate-200 dark:border-slate-700 text-xs font-medium hover:bg-slate-50 dark:hover:bg-slate-800"
          aria-label="Reset topology view"
        >Reset</button>
      </div>

      <svg
        ref={svgRef}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="w-full h-[520px] rounded-xl bg-slate-50 dark:bg-slate-900/40 cursor-grab active:cursor-grabbing select-none"
        onMouseDown={handleBackgroundMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.scale})`}>
          {edges.map((edge, i) => {
            const source = nodeById(edge.source)
            const target = nodeById(edge.target)
            if (!source || !target) return null
            return (
              <line
                key={i}
                x1={source.x} y1={source.y} x2={target.x} y2={target.y}
                stroke="#94a3b8" strokeWidth={1.5} strokeOpacity={0.4}
              />
            )
          })}

          {nodes.map((node) => {
            const isNetwork = node.type === 'network'
            const isVlan = node.type === 'vlan'
            const color = isNetwork ? '#3366ff' : isVlan ? VLAN_HUB_COLOR : RISK_COLORS[node.risk_level ?? 'LOW']
            const isOffline = node.status === 'offline'
            const radius = isNetwork ? 26 : isVlan ? 21 : 16
            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onMouseDown={handleNodeMouseDown(node.id)}
                onClick={() => node.type === 'host' && onSelectHost?.(node.id)}
                className="cursor-pointer"
              >
                <circle
                  r={radius}
                  fill={isOffline ? '#94a3b8' : color}
                  fillOpacity={isOffline ? 0.3 : 0.15}
                  stroke={isOffline ? '#94a3b8' : color}
                  strokeWidth={2}
                />
                <circle r={isNetwork ? 6 : isVlan ? 5 : 4} fill={isOffline ? '#94a3b8' : color} />
                <text
                  y={radius + 16}
                  textAnchor="middle"
                  fontSize={isVlan ? 10 : 11}
                  fontWeight={600}
                  fill="currentColor"
                  className="text-slate-700 dark:text-slate-200 pointer-events-none"
                >
                  {node.label}
                </text>
                {node.type === 'host' && node.hostname && (
                  <text
                    y={radius + 30}
                    textAnchor="middle"
                    fontSize={9}
                    fill="currentColor"
                    className="text-slate-400 pointer-events-none"
                  >
                    {node.hostname}
                  </text>
                )}
                {isVlan && node.vlan_name && (
                  <text
                    y={radius + 30}
                    textAnchor="middle"
                    fontSize={9}
                    fontStyle="italic"
                    fill="currentColor"
                    className="text-slate-400 pointer-events-none"
                  >
                    {node.vlan_name}
                  </text>
                )}
              </g>
            )
          })}
        </g>
      </svg>

      <div className="flex flex-wrap gap-4 mt-3 text-xs text-slate-500 dark:text-slate-400">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: VLAN_HUB_COLOR }} />
          VLAN
        </div>
        {(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as RiskLevel[]).map((level) => (
          <div key={level} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: RISK_COLORS[level] }} />
            {level}
          </div>
        ))}
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
          Offline
        </div>
        <p className="ml-auto italic">Drag nodes to rearrange &middot; scroll to zoom &middot; drag background to pan</p>
      </div>
    </div>
  )
}
