import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  AUTH_SESSION_CHANGE_EVENT,
  loadSession,
} from './session'
import {
  login as loginRequest,
  logout as logoutRequest,
} from '../services/auth'
import type { AuthSession } from '../types/auth'

interface AuthContextValue {
  session: AuthSession | null
  isAuthenticated: boolean

  login: (
    email: string,
    password: string,
  ) => Promise<void>

  logout: () => Promise<void>
}

const AuthContext =
  createContext<AuthContextValue | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({
  children,
}: AuthProviderProps) {
  const [session, setSession] =
    useState<AuthSession | null>(() => loadSession())

  useEffect(() => {
    function syncSession() {
      setSession(loadSession())
    }

    window.addEventListener(
      AUTH_SESSION_CHANGE_EVENT,
      syncSession,
    )

    window.addEventListener(
      'storage',
      syncSession,
    )

    return () => {
      window.removeEventListener(
        AUTH_SESSION_CHANGE_EVENT,
        syncSession,
      )

      window.removeEventListener(
        'storage',
        syncSession,
      )
    }
  }, [])

  const login = useCallback(
    async (
      email: string,
      password: string,
    ) => {
      const nextSession = await loginRequest({
        email,
        password,
      })

      setSession(nextSession)
    },
    [],
  )

  const logout = useCallback(async () => {
    try {
      await logoutRequest(session)
    } finally {
      setSession(null)
    }
  }, [session])

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      isAuthenticated: session !== null,
      login,
      logout,
    }),
    [session, login, logout],
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error(
      'useAuth must be used within AuthProvider',
    )
  }

  return context
}
