import { RiskLevel } from '../../types'
import { FiAlertTriangle, FiAlertOctagon, FiAlertCircle, FiCheckCircle } from 'react-icons/fi'

const RISK_STYLES: Record<RiskLevel, { bg: string; text: string; icon: JSX.Element }> = {
  LOW: {
    bg: 'bg-emerald-100 dark:bg-emerald-500/10',
    text: 'text-emerald-700 dark:text-emerald-400',
    icon: <FiCheckCircle className="w-3.5 h-3.5" />,
  },
  MEDIUM: {
    bg: 'bg-amber-100 dark:bg-amber-500/10',
    text: 'text-amber-700 dark:text-amber-400',
    icon: <FiAlertCircle className="w-3.5 h-3.5" />,
  },
  HIGH: {
    bg: 'bg-orange-100 dark:bg-orange-500/10',
    text: 'text-orange-700 dark:text-orange-400',
    icon: <FiAlertTriangle className="w-3.5 h-3.5" />,
  },
  CRITICAL: {
    bg: 'bg-red-100 dark:bg-red-500/10',
    text: 'text-red-700 dark:text-red-400',
    icon: <FiAlertOctagon className="w-3.5 h-3.5" />,
  },
}

export default function RiskBadge({ level }: { level: RiskLevel }) {
  const style = RISK_STYLES[level] ?? RISK_STYLES.LOW
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${style.bg} ${style.text}`}>
      {style.icon}
      {level}
    </span>
  )
}
