import { IconType } from 'react-icons'

interface StatCardProps {
  label: string
  value: string | number
  icon: IconType
  accent: 'brand' | 'emerald' | 'red' | 'amber' | 'slate'
  suffix?: string
}

const ACCENT_STYLES: Record<string, string> = {
  brand: 'bg-brand-500/10 text-brand-500',
  emerald: 'bg-emerald-500/10 text-emerald-500',
  red: 'bg-red-500/10 text-red-500',
  amber: 'bg-amber-500/10 text-amber-500',
  slate: 'bg-slate-500/10 text-slate-500',
}

export default function StatCard({ label, value, icon: Icon, accent, suffix }: StatCardProps) {
  return (
    <div className="card p-5 flex items-center justify-between animate-fadeIn hover:shadow-lg transition-shadow">
      <div>
        <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold mt-1.5 text-slate-900 dark:text-white">
          {value}
          {suffix && <span className="text-sm font-medium text-slate-400 ml-1">{suffix}</span>}
        </p>
      </div>
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${ACCENT_STYLES[accent]}`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  )
}
