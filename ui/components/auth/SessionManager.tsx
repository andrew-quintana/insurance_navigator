"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase-client'
import { User } from '@supabase/supabase-js'

interface Session {
  access_token: string
  user: User
}

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signOut: () => Promise<void>
  refreshSession: () => Promise<boolean>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: React.ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get initial session from localStorage token
    const getInitialSession = async () => {
      try {
        const token = localStorage.getItem('token')
        
        if (token) {
          // Verify token with backend
          const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
          const response = await fetch(`${apiBaseUrl}/auth/user`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (response.ok) {
            const userData = await response.json()
            setUser(userData)
            setSession({ access_token: token, user: userData })
          } else {
            // Token is invalid, clear it
            localStorage.removeItem('token')
            setUser(null)
            setSession(null)
          }
        } else {
          setUser(null)
          setSession(null)
        }
      } catch (error) {
        console.error('Session check failed:', error)
        localStorage.removeItem('token')
        setUser(null)
        setSession(null)
      } finally {
        setLoading(false)
      }
    }

    getInitialSession()
  }, [])

  const signOut = async () => {
    try {
      // Clear local session
      localStorage.removeItem('token')
      setUser(null)
      setSession(null)
      
      // Optionally call backend logout endpoint if needed
      const token = localStorage.getItem('token')
      if (token) {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
        await fetch(`${apiBaseUrl}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
      }
    } catch (error) {
      console.error('Sign out failed:', error)
    }
  }

  const refreshSession = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        return false
      }
      
      // Verify token with backend
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${apiBaseUrl}/auth/user`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
        setSession({ access_token: token, user: userData })
        return true
      } else {
        // Token is invalid, clear it
        localStorage.removeItem('token')
        setUser(null)
        setSession(null)
        return false
      }
    } catch (error) {
      console.error('Refresh session failed:', error)
      return false
    }
  }

  const value = {
    user,
    session,
    loading,
    signOut,
    refreshSession
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}


