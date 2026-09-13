import type {
  AuthSession,
  AuthTokens,
  AuthUser,
} from '../types/auth'

const SESSION_STORAGE_KEY =
  'ivy.auth.session'

export const AUTH_SESSION_CHANGE_EVENT =
  'ivy:auth-session-change'

function notifySessionChange() {
  window.dispatchEvent(
    new Event(
      AUTH_SESSION_CHANGE_EVENT,
    ),
  )
}

function isRecord(
  value: unknown,
): value is Record<
  string,
  unknown
> {
  return (
    typeof value === 'object' &&
    value !== null
  )
}

function isValidSession(
  value: unknown,
): value is AuthSession {
  if (!isRecord(value)) {
    return false
  }

  const tokens = value.tokens
  const user = value.user

  if (
    !isRecord(tokens) ||
    !isRecord(user)
  ) {
    return false
  }

  return (
    typeof tokens.accessToken ===
      'string' &&
    tokens.accessToken.length > 0 &&

    typeof tokens.refreshToken ===
      'string' &&
    tokens.refreshToken.length > 0 &&

    typeof tokens.tokenType ===
      'string' &&

    typeof tokens.expiresIn ===
      'number' &&
    Number.isFinite(
      tokens.expiresIn,
    ) &&

    typeof user.email ===
      'string' &&
    user.email.length > 0 &&

    typeof value.expiresAt ===
      'number' &&
    Number.isFinite(
      value.expiresAt,
    )
  )
}

export function createSession(
  tokens: AuthTokens,
  user: AuthUser,
): AuthSession {
  return {
    tokens,
    user,

    expiresAt:
      Date.now() +
      tokens.expiresIn * 1000,
  }
}

export function saveSession(
  session: AuthSession,
) {
  localStorage.setItem(
    SESSION_STORAGE_KEY,
    JSON.stringify(session),
  )

  notifySessionChange()
}

export function loadSession():
  AuthSession | null {
  const rawSession =
    localStorage.getItem(
      SESSION_STORAGE_KEY,
    )

  if (!rawSession) {
    return null
  }

  try {
    const parsed: unknown =
      JSON.parse(rawSession)

    if (
      !isValidSession(parsed)
    ) {
      clearSession()
      return null
    }

    return parsed
  } catch {
    clearSession()

    return null
  }
}

export function clearSession() {
  localStorage.removeItem(
    SESSION_STORAGE_KEY,
  )

  notifySessionChange()
}

export function isSessionExpired(
  session: AuthSession,
  bufferSeconds = 30,
) {
  return (
    Date.now() >=
    session.expiresAt -
      bufferSeconds * 1000
  )
}
