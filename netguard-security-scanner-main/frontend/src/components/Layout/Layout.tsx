import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

const TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/scan': 'Network Scan',
  '/hosts': 'Discovered Hosts',
  '/topology': 'Network Topology',
  '/history': 'Scan History',
  '/reports': 'Reports',
  '/settings': 'Settings',
  '/about': 'About',
}

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const title = TITLES[location.pathname] ?? (location.pathname.startsWith('/hosts/') ? 'Host Details' : 'NetGuard')

  return (
    <div className="flex min-h-screen">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 min-w-0">
        <Topbar onMenuClick={() => setSidebarOpen(true)} title={title} />
        <main className="p-4 lg:p-6 max-w-[1600px] mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
