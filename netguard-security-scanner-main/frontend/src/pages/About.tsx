import { FiShield, FiGithub } from 'react-icons/fi'

export default function About() {
  return (
    <div className="max-w-2xl space-y-6">
      <div className="card p-8 text-center">
        <div className="w-16 h-16 rounded-2xl bg-brand-500 flex items-center justify-center mx-auto mb-4">
          <FiShield className="text-white w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">NetGuard</h2>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Enterprise Network Discovery & Security Scanner</p>
        <p className="text-xs text-slate-400 mt-3">Version 1.0.0</p>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 dark:text-white mb-2">About this Project</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
          NetGuard is a full-stack network discovery and security assessment platform built with FastAPI,
          Nmap, and React. It performs host discovery, port and service enumeration, OS fingerprinting, and
          automated risk scoring with actionable remediation guidance — packaged in a modern, dark-mode
          dashboard suitable for a network engineering / security portfolio.
        </p>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-800 dark:text-white mb-3">Tech Stack</h3>
        <div className="flex flex-wrap gap-2">
          {['FastAPI', 'Python 3.12', 'python-nmap', 'SQLite', 'ReportLab', 'React', 'TypeScript', 'Vite', 'TailwindCSS', 'Recharts'].map((t) => (
            <span key={t} className="text-xs px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium">
              {t}
            </span>
          ))}
        </div>
      </div>

      <div className="card p-6 flex items-center justify-between">
        <div>
          <p className="font-medium text-sm text-slate-800 dark:text-white">Source Code</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">See the README for full setup instructions</p>
        </div>
        <FiGithub className="w-5 h-5 text-slate-400" />
      </div>
    </div>
  )
}
