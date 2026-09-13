import { ApiError } from './client'

function getMessageFromPayload(payload: unknown): string | null {
  if (typeof payload === 'string') {
    return payload
  }

  if (!payload || typeof payload !== 'object') {
    return null
  }

  if ('message' in payload && typeof payload.message === 'string') {
    return payload.message
  }

  if ('detail' in payload && typeof payload.detail === 'string') {
    return payload.detail
  }

  if ('error' in payload && typeof payload.error === 'string') {
    return payload.error
  }

  return null
}

export function getApiErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return (
      getMessageFromPayload(error.payload) ??
      `Request failed (${error.status})`
    )
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'An unexpected error occurred'
}
