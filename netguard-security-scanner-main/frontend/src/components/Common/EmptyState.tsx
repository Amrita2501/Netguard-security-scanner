import { IconType } from 'react-icons'

export default function EmptyState({ icon: Icon, title, description }: { icon: IconType; title: string; description?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-16 text-center text-slate-500 dark:text-slate-400">
      <Icon className="w-10 h-10 mb-1 opacity-50" />
      <p className="font-medium text-slate-700 dark:text-slate-300">{title}</p>
      {description && <p className="text-sm max-w-sm">{description}</p>}
    </div>
  )
}
