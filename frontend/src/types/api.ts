export type ApiErrorPayload =
  | Record<string, unknown>
  | unknown[]
  | string
  | null

export interface ApiCollectionResponse<T> {
  limit: number
  offset: number
  count: number
  total: number
  has_more: boolean
  results: T[]
}