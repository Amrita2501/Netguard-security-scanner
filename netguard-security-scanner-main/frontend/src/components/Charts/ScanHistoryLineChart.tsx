import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

interface Props {
  data: { scan_id: number; date: string; live_hosts: number; duration: number | null }[]
}

export default function ScanHistoryLineChart({ data }: Props) {
  if (!data.length) {
    return <div className="flex items-center justify-center h-64 text-sm text-slate-400">No scan history yet</div>
  }
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 8, right: 12, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.15} vertical={false} />
        <XAxis dataKey="date" fontSize={11} tickLine={false} axisLine={false} />
        <YAxis fontSize={11} tickLine={false} axisLine={false} allowDecimals={false} />
        <Tooltip contentStyle={{ borderRadius: 12, border: 'none', fontSize: 12 }} />
        <Line type="monotone" dataKey="live_hosts" name="Live Hosts" stroke="#3366ff" strokeWidth={2.5} dot={{ r: 3 }} />
        <Line type="monotone" dataKey="duration" name="Duration (s)" stroke="#22c55e" strokeWidth={2.5} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}
