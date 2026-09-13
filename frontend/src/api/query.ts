export type QueryValue =
  | string
  | number
  | boolean
  | null
  | undefined

export type QueryParams = Record<
  string,
  QueryValue | QueryValue[]
>

export function buildQueryString(params: QueryParams = {}) {
  const searchParams = new URLSearchParams()

  for (const [key, rawValue] of Object.entries(params)) {
    if (rawValue === undefined || rawValue === null || rawValue === '') {
      continue
    }

    const values = Array.isArray(rawValue)
      ? rawValue
      : [rawValue]

    for (const value of values) {
      if (value === undefined || value === null || value === '') {
        continue
      }

      searchParams.append(key, String(value))
    }
  }

  const query = searchParams.toString()

  return query ? `?${query}` : ''
}
