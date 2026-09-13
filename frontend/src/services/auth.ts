import {
  authenticatedRequest,
  ivyRequest,
} from '../api/authenticatedClient'
import { endpoints } from '../api/endpoints'
import {
  clearSession,
  createSession,
  saveSession,
} from '../auth/session'
import type {
  AuthSession,
  LoginResponse,
  RefreshResponse,
} from '../types/auth'

interface LoginCredentials {
  email: string
  password: string
}

function createTokens(
  response: LoginResponse | RefreshResponse,
  previousRefreshToken?: string,
) {
  const refreshToken =
    'refresh_token' in response &&
    response.refresh_token
      ? response.refresh_token
      : previousRefreshToken

  if (!refreshToken) {
    throw new Error(
      'Authentication response did not contain a refresh token',
    )
  }

  return {
    accessToken: response.access_token,
    refreshToken,
    tokenType: response.token_type,
    expiresIn: response.expires_in,
  }
}

export async function login(
  credentials: LoginCredentials,
): Promise<AuthSession> {
  const response = await ivyRequest<LoginResponse>(
    endpoints.login,
    {
      method: 'POST',
      body: credentials,
    },
  )

  const session = createSession(
    createTokens(response),
    response.user,
  )

  saveSession(session)

  return session
}

export async function refreshSession(
  session: AuthSession,
): Promise<AuthSession> {
  const response = await ivyRequest<RefreshResponse>(
    endpoints.refresh,
    {
      method: 'POST',
      body: {
        refresh_token: session.tokens.refreshToken,
      },
    },
  )

  const refreshedSession = createSession(
    createTokens(
      response,
      session.tokens.refreshToken,
    ),
    session.user,
  )

  saveSession(refreshedSession)

  return refreshedSession
}

export async function logout(
  session: AuthSession | null,
) {
  try {
    if (session) {
      await authenticatedRequest(
        endpoints.logout,
        session.tokens.accessToken,
        {
          method: 'POST',
        },
      )
    }
  } finally {
    /*
     * Verified backend behaviour:
     * logout does not revoke the stateless token.
     * Local credential removal is therefore mandatory.
     */
    clearSession()
  }
}
