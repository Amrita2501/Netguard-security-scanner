import { createContext, useContext, useState, ReactNode } from 'react'
import client from '../api/client'

interface AuthUser {
  username: string
  full_name: string
}

interface AuthContextValue {
  user: AuthUser | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const stored = localStorage.getItem('netscan_user')
    return stored ? JSON.parse(stored) : null
  })

  const login = async (username: string, password: string) => {
    const { data } = await client.post('/auth/login', { username, password })
    localStorage.setItem('netscan_token', data.token)
    const authUser = { username: data.username, full_name: data.full_name }
    localStorage.setItem('netscan_user', JSON.stringify(authUser))
    setUser(authUser)
  }

  const logout = () => {
    localStorage.removeItem('netscan_token')
    localStorage.removeItem('netscan_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
