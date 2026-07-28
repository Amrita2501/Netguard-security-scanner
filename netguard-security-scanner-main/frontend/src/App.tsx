import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout/Layout'
import LoadingSpinner from './components/Common/LoadingSpinner'

// Route-level code splitting: each page ships as its own chunk, loaded on
// first visit rather than bundled into the initial payload. Login is kept
// as a static import since it's the near-universal first screen.
import Login from './pages/Login'
const Dashboard = lazy(() => import('./pages/Dashboard'))
const ScanPage = lazy(() => import('./pages/ScanPage'))
const Hosts = lazy(() => import('./pages/Hosts'))
const HostDetail = lazy(() => import('./pages/HostDetail'))
const TopologyPage = lazy(() => import('./pages/Topology'))
const ScanHistory = lazy(() => import('./pages/ScanHistory'))
const Reports = lazy(() => import('./pages/Reports'))
const Settings = lazy(() => import('./pages/Settings'))
const About = lazy(() => import('./pages/About'))

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Toaster position="top-right" toastOptions={{ style: { fontSize: 14, borderRadius: 12 } }} />
          <Suspense fallback={<LoadingSpinner label="Loading…" />}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route
                element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route path="/" element={<Dashboard />} />
                <Route path="/scan" element={<ScanPage />} />
                <Route path="/hosts" element={<Hosts />} />
                <Route path="/hosts/:id" element={<HostDetail />} />
                <Route path="/topology" element={<TopologyPage />} />
                <Route path="/history" element={<ScanHistory />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/about" element={<About />} />
              </Route>
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}
