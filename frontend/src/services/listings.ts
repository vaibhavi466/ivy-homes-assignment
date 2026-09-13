import { protectedRequest } from '../api/protectedClient'
import { endpoints } from '../api/endpoints'
import { buildQueryString } from '../api/query'
import type { ApiCollectionResponse } from '../types/api'
import type { Listing } from '../types/listing'

const MAX_LISTING_PAGE_SIZE = 50

let allListingsPromise: Promise<Listing[]> | null = null

export interface ListingPageParams {
  offset?: number
  limit?: number
}

function normalizeOffset(offset: number | undefined) {
  if (offset === undefined || !Number.isFinite(offset)) {
    return 0
  }

  return Math.max(0, Math.trunc(offset))
}

function normalizeLimit(limit: number | undefined) {
  if (limit === undefined || !Number.isFinite(limit)) {
    return MAX_LISTING_PAGE_SIZE
  }

  return Math.min(
    MAX_LISTING_PAGE_SIZE,
    Math.max(1, Math.trunc(limit)),
  )
}

export async function getListings(
  params: ListingPageParams = {},
) {
  const query = buildQueryString({
    offset: normalizeOffset(params.offset),
    limit: normalizeLimit(params.limit),
  })

  return protectedRequest<ApiCollectionResponse<Listing>>(
    `${endpoints.listings}${query}`,
  )
}

export async function getListingById(id: string) {
  const listingId = id.trim()

  if (!listingId) {
    throw new Error('Listing ID is required')
  }

  return protectedRequest<Listing>(
    endpoints.listing(listingId),
  )
}

export async function getAllListings() {
  const listings: Listing[] = []
  const seenIds = new Set<string>()

  let offset = 0

  while (true) {
    const page = await getListings({
      offset,
      limit: MAX_LISTING_PAGE_SIZE,
    })

    for (const listing of page.results) {
      if (!seenIds.has(listing.listing_id)) {
        seenIds.add(listing.listing_id)
        listings.push(listing)
      }
    }

    if (!page.has_more) {
      break
    }

    if (page.results.length === 0) {
      throw new Error(
        'Listings API reported more records but returned an empty page',
      )
    }

    offset += page.results.length
  }

  return listings
}

export function getAllListingsCached() {
  if (!allListingsPromise) {
    allListingsPromise = getAllListings().catch(
      (error: unknown) => {
        allListingsPromise = null

        throw error
      },
    )
  }

  return allListingsPromise
}

export function getLiveListings(
  listings: readonly Listing[],
) {
  return listings.filter((listing) => listing.is_live)
}
