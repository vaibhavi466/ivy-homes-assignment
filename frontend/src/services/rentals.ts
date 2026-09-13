import { endpoints } from '../api/endpoints'
import { protectedRequest } from '../api/protectedClient'
import { buildQueryString } from '../api/query'
import type { ApiCollectionResponse } from '../types/api'
import type { Rental } from '../types/rental'

const MAX_RENTAL_PAGE_SIZE = 50

let allRentalsPromise: Promise<Rental[]> | null = null

export interface RentalPageParams {
  offset?: number
  limit?: number
}

function normalizeOffset(
  offset: number | undefined,
) {
  if (
    offset === undefined ||
    !Number.isFinite(offset)
  ) {
    return 0
  }

  return Math.max(
    0,
    Math.trunc(offset),
  )
}

function normalizeLimit(
  limit: number | undefined,
) {
  if (
    limit === undefined ||
    !Number.isFinite(limit)
  ) {
    return MAX_RENTAL_PAGE_SIZE
  }

  return Math.min(
    MAX_RENTAL_PAGE_SIZE,
    Math.max(
      1,
      Math.trunc(limit),
    ),
  )
}

export async function getRentals(
  params: RentalPageParams = {},
) {
  const query = buildQueryString({
    offset: normalizeOffset(
      params.offset,
    ),

    limit: normalizeLimit(
      params.limit,
    ),
  })

  return protectedRequest<
    ApiCollectionResponse<Rental>
  >(`${endpoints.rentals}${query}`)
}

export async function getRentalById(
  id: string,
) {
  const rentalId = id.trim()

  if (!rentalId) {
    throw new Error(
      'Rental ID is required',
    )
  }

  return protectedRequest<Rental>(
    endpoints.rental(rentalId),
  )
}

export async function getAllRentals() {
  const rentals: Rental[] = []

  const seenIds =
    new Set<string>()

  let offset = 0

  while (true) {
    const page = await getRentals({
      offset,
      limit: MAX_RENTAL_PAGE_SIZE,
    })

    for (
      const rental of page.results
    ) {
      if (
        !seenIds.has(
          rental.listing_id,
        )
      ) {
        seenIds.add(
          rental.listing_id,
        )

        rentals.push(rental)
      }
    }

    if (!page.has_more) {
      break
    }

    if (
      page.results.length === 0
    ) {
      throw new Error(
        'Rentals API reported more records but returned an empty page',
      )
    }

    offset +=
      page.results.length
  }

  return rentals
}

export function getAllRentalsCached() {
  if (!allRentalsPromise) {
    allRentalsPromise =
      getAllRentals().catch(
        (error: unknown) => {
          allRentalsPromise = null
          throw error
        },
      )
  }

  return allRentalsPromise
}

export function getLiveRentals(
  rentals: readonly Rental[],
) {
  return rentals.filter(
    (rental) =>
      rental.is_live,
  )
}
