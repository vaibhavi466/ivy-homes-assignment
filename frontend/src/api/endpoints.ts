export const endpoints = {
  health: '/health',

  listings: '/v1/listings',

  listing: (id: string) =>
    `/v1/listings/${encodeURIComponent(id)}`,
} as const
