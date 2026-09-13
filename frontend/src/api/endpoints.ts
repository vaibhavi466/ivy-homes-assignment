export const endpoints = {
  health: '/health',

  login: '/auth/login',
  refresh: '/auth/refresh',
  logout: '/auth/logout',

  listings: '/v1/listings',

  listing: (id: string) =>
    `/v1/listings/${encodeURIComponent(id)}`,

  rentals: '/v1/rentals',

  rental: (id: string) =>
    `/v1/rentals/${encodeURIComponent(id)}`,
} as const
