import { HostStatus } from '../../types'

export default function StatusBadge({ status }: { status: HostStatus }) {
  const online = status === 'online'
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold
      ${online
        ? 'bg-brand-100 dark:bg-brand-500/10 text-brand-700 dark:text-brand-400'
        : 'bg-slate-100 dark:bg-slate-700/40 text-slate-500 dark:text-slate-400'}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${online ? 'bg-brand-500 animate-pulseSlow' : 'bg-slate-400'}`} />
      {online ? 'Online' : 'Offline'}
    </span>
  )
}
