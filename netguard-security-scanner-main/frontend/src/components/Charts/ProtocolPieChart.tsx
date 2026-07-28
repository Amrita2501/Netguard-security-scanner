import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const COLORS = ['#3366ff', '#22c55e', '#f97316', '#ef4444', '#a855f7', '#06b6d4', '#eab308', '#64748b']

interface Props {
  data: { name: string; value: number }[]
}

export default function ProtocolPieChart({ data }: Props) {
  if (!data.length) {
    return <div className="flex items-center justify-center h-64 text-sm text-slate-400">No service data yet</div>
  }
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={2}>
          {data.map((_, idx) => (
            <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip contentStyle={{ borderRadius: 12, border: 'none', fontSize: 12 }} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  )
}
