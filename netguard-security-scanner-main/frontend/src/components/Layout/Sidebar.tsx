import { NavLink } from 'react-router-dom'
import {
  FiGrid, FiSearch, FiServer, FiShare2, FiClock, FiFileText,
  FiSettings, FiInfo, FiShield,
} from 'react-icons/fi'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: FiGrid, end: true },
  { to: '/scan', label: 'Network Scan', icon: FiSearch },
  { to: '/hosts', label: 'Hosts', icon: FiServer },
  { to: '/topology', label: 'Topology', icon: FiShare2 },
  { to: '/history', label: 'Scan History', icon: FiClock },
  { to: '/reports', label: 'Reports', icon: FiFileText },
  { to: '/settings', label: 'Settings', icon: FiSettings },
  { to: '/about', label: 'About', icon: FiInfo },
]

export default function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 bg-black/40 z-30 lg:hidden"
          onClick={onClose}
          role="button"
          aria-label="Close navigation menu"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Escape' || e.key === 'Enter') onClose() }}
        />
      )}
      <aside className={`fixed lg:sticky top-0 h-screen w-64 shrink-0 bg-panel-light dark:bg-panel-dark
        border-r border-slate-200 dark:border-slate-800 z-40 transition-transform duration-200
        ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <div className="h-16 flex items-center gap-2.5 px-5 border-b border-slate-200 dark:border-slate-800">
          <div className="w-9 h-9 rounded-xl bg-brand-500 flex items-center justify-center">
            <FiShield className="text-white w-5 h-5" />
          </div>
          <div>
            <p className="font-bold text-slate-900 dark:text-white leading-tight">NetGuard</p>
            <p className="text-[11px] text-slate-400 leading-tight">Enterprise Scanner</p>
          </div>
        </div>

        <nav className="p-3 flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors
                ${isActive
                  ? 'bg-brand-500 text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'}`
              }
            >
              <item.icon className="w-4.5 h-4.5 shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 w-full p-4 border-t border-slate-200 dark:border-slate-800">
          <p className="text-[11px] text-slate-400 text-center">v1.0.0 &middot; Portfolio Build</p>
        </div>
      </aside>
    </>
  )
}
