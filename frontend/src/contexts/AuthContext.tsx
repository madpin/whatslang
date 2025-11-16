import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import type { User, LoginRequest, RegisterRequest } from '@/types/user'
import * as api from '@/services/api'

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Load token and user on mount
  useEffect(() => {
    const loadAuth = async () => {
      const storedToken = localStorage.getItem('auth_token')
      
      if (storedToken) {
        setToken(storedToken)
        try {
          const currentUser = await api.getCurrentUser()
          setUser(currentUser)
        } catch (error) {
          // Token is invalid, clear it
          localStorage.removeItem('auth_token')
          setToken(null)
        }
      }
      
      setIsLoading(false)
    }

    loadAuth()
  }, [])

  const login = async (credentials: LoginRequest) => {
    const response = await api.login(credentials)
    const { access_token } = response
    
    localStorage.setItem('auth_token', access_token)
    setToken(access_token)
    
    // Fetch user info
    const currentUser = await api.getCurrentUser()
    setUser(currentUser)
  }

  const register = async (data: RegisterRequest) => {
    await api.register(data)
    // After registration, automatically log in
    await login({ email: data.email, password: data.password })
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setToken(null)
    setUser(null)
    api.logout()
  }

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isLoading,
    login,
    register,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

