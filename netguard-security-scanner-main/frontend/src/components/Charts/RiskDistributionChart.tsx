import { RiskLevel } from '../../types'

const RISK_COLORS: Record<RiskLevel, string> = {
  LOW: '#22c55e',
  MEDIUM: '#eab308',
  HIGH: '#f97316',
  CRITICAL: '#ef4444',
}

interface Props {
  distribution: Record<RiskLevel, number>
}

export default function RiskDistributionChart({ distribution }: Props) {
  const total = Object.values(distribution).reduce((a, b) => a + b, 0) || 1
  const levels: RiskLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

  return (
    <div className="space-y-4">
      {levels.map((level) => {
        const value = distribution[level] ?? 0
        const pct = Math.round((value / total) * 100)
        return (
          <div key={level}>
            <div className="flex justify-between text-xs font-medium mb-1.5">
              <span style={{ color: RISK_COLORS[level] }}>{level}</span>
              <span className="text-slate-500 dark:text-slate-400">{value} hosts</span>
            </div>
            <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${pct}%`, backgroundColor: RISK_COLORS[level] }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
