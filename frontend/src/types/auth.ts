export interface AuthUser {
  email: string

  [key: string]: unknown
}

export interface AuthTokens {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  refresh_url: string
  user: AuthUser
}

export interface RefreshResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number

  [key: string]: unknown
}

export interface AuthSession {
  tokens: AuthTokens
  user: AuthUser
  expiresAt: number
}
