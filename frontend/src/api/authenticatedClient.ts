import { apiRequest } from './client'

type IvyRequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown
}

const apiKey = import.meta.env.VITE_IVY_API_KEY

if (!apiKey) {
  console.warn(
    'VITE_IVY_API_KEY is not configured. Protected API requests will fail.',
  )
}

export function ivyRequest<T>(
  path: string,
  options: IvyRequestOptions = {},
) {
  const headers = new Headers(options.headers)

  if (apiKey) {
    headers.set('X-API-Key', apiKey)
  }

  return apiRequest<T>(path, {
    ...options,
    headers,
  })
}

export function authenticatedRequest<T>(
  path: string,
  accessToken: string,
  options: IvyRequestOptions = {},
) {
  const headers = new Headers(options.headers)

  if (apiKey) {
    headers.set('X-API-Key', apiKey)
  }

  headers.set(
    'Authorization',
    `Bearer ${accessToken}`,
  )

  return apiRequest<T>(path, {
    ...options,
    headers,
  })
}
