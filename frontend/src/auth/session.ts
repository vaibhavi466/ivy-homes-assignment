import type {
  AuthSession,
  AuthTokens,
  AuthUser,
} from '../types/auth'

const SESSION_STORAGE_KEY = 'ivy.auth.session'

export const AUTH_SESSION_CHANGE_EVENT =
  'ivy:auth-session-change'

function notifySessionChange() {
  window.dispatchEvent(
    new Event(AUTH_SESSION_CHANGE_EVENT),
  )
}

export function createSession(
  tokens: AuthTokens,
  user: AuthUser,
): AuthSession {
  return {
    tokens,
    user,
    expiresAt: Date.now() + tokens.expiresIn * 1000,
  }
}

export function saveSession(session: AuthSession) {
  localStorage.setItem(
    SESSION_STORAGE_KEY,
    JSON.stringify(session),
  )

  notifySessionChange()
}

export function loadSession(): AuthSession | null {
  const rawSession = localStorage.getItem(
    SESSION_STORAGE_KEY,
  )

  if (!rawSession) {
    return null
  }

  try {
    return JSON.parse(rawSession) as AuthSession
  } catch {
    clearSession()

    return null
  }
}

export function clearSession() {
  localStorage.removeItem(SESSION_STORAGE_KEY)

  notifySessionChange()
}

export function isSessionExpired(
  session: AuthSession,
  bufferSeconds = 30,
) {
  return (
    Date.now() >=
    session.expiresAt - bufferSeconds * 1000
  )
}
