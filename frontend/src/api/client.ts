import type { ApiErrorPayload } from '../types/api'

const DEFAULT_BASE_URL = 'https://solve.ivy.homes'

const baseUrl = (
  import.meta.env.VITE_IVY_BASE_URL ?? DEFAULT_BASE_URL
).replace(/\/+$/, '')

export class ApiError extends Error {
  status: number
  payload: ApiErrorPayload

  constructor(
    message: string,
    status: number,
    payload: ApiErrorPayload,
  ) {
    super(message)

    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

type ApiRequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown
}

function buildUrl(path: string) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`

  return `${baseUrl}${normalizedPath}`
}

async function parseResponse(response: Response): Promise<ApiErrorPayload> {
  if (response.status === 204) {
    return null
  }

  const contentType = response.headers.get('content-type') ?? ''

  if (contentType.includes('application/json')) {
    return response.json()
  }

  const text = await response.text()

  return text || null
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const {
    body,
    headers,
    ...requestOptions
  } = options

  const requestHeaders = new Headers(headers)

  requestHeaders.set('Accept', 'application/json')

  if (body !== undefined) {
    requestHeaders.set('Content-Type', 'application/json')
  }

  const response = await fetch(buildUrl(path), {
    ...requestOptions,
    headers: requestHeaders,
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  const payload = await parseResponse(response)

  if (!response.ok) {
    throw new ApiError(
      `API request failed with status ${response.status}`,
      response.status,
      payload,
    )
  }

  return payload as T
}
