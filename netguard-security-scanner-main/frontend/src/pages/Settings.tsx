import { FiMoon, FiSun, FiUser, FiKey, FiTerminal } from 'react-icons/fi'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'

export default function Settings() {
  const { isDark, toggleTheme } = useTheme()
  const { user } = useAuth()

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <FiUser className="w-4 h-4" /> Profile
        </h3>
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-brand-500 text-white flex items-center justify-center text-xl font-semibold">
            {user?.full_name?.[0] ?? 'U'}
          </div>
          <div>
            <p className="font-medium text-slate-800 dark:text-white">{user?.full_name}</p>
            <p className="text-sm text-slate-500 dark:text-slate-400">@{user?.username}</p>
          </div>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 dark:text-white mb-4">Appearance</h3>
        <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
          <div className="flex items-center gap-3">
            {isDark ? <FiMoon className="w-5 h-5 text-brand-500" /> : <FiSun className="w-5 h-5 text-amber-500" />}
            <div>
              <p className="font-medium text-sm text-slate-800 dark:text-white">Dark Mode</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Toggle the professional dark interface</p>
            </div>
          </div>
          <button
            onClick={toggleTheme}
            className={`w-12 h-6.5 rounded-full relative transition-colors ${isDark ? 'bg-brand-500' : 'bg-slate-300'}`}
          >
            <span className={`absolute top-0.5 w-5.5 h-5.5 bg-white rounded-full shadow transition-transform ${isDark ? 'translate-x-6' : 'translate-x-0.5'}`} />
          </button>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <FiKey className="w-4 h-4" /> Security Note
        </h3>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          This is a portfolio/demo build. Authentication uses a single local account stored in
          <span className="font-mono mx-1">backend/data/users.json</span>
          and is not intended for production/multi-user deployment.
        </p>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <FiTerminal className="w-4 h-4" /> Keyboard Shortcuts
        </h3>
        <ul className="text-sm text-slate-500 dark:text-slate-400 space-y-1.5">
          <li><span className="font-mono bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">g d</span> — Go to Dashboard</li>
          <li><span className="font-mono bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">g s</span> — Go to Scan page</li>
          <li><span className="font-mono bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">g h</span> — Go to Hosts</li>
        </ul>
      </div>
    </div>
  )
}
