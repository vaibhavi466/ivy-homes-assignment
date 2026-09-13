import type { Listing } from '../types/listing'
import {
  getNormalizedCarpetArea,
} from './listing'

export type ListingSort =
  | 'price-asc'
  | 'price-desc'
  | 'bedroom-asc'
  | 'bedroom-desc'
  | 'area-asc'
  | 'area-desc'
  | 'newest'
  | 'oldest'

export interface ListingFilters {
  search: string
  locality: string
  bedroom: string
  propertyType: string
  furnishing: string
  minPrice: string
  maxPrice: string
  sort: ListingSort
}

export const DEFAULT_LISTING_FILTERS: ListingFilters = {
  search: '',
  locality: '',
  bedroom: '',
  propertyType: '',
  furnishing: '',
  minPrice: '',
  maxPrice: '',
  sort: 'newest',
}

function normalizeText(value: string | null | undefined) {
  return value?.trim().toLowerCase() ?? ''
}

function parsePrice(value: string) {
  if (!value.trim()) {
    return null
  }

  const parsed = Number(value)

  return Number.isFinite(parsed)
    ? parsed
    : null
}

function compareNullableNumbers(
  left: number | null,
  right: number | null,
  direction: 'asc' | 'desc',
) {
  if (left === null && right === null) {
    return 0
  }

  if (left === null) {
    return 1
  }

  if (right === null) {
    return -1
  }

  return direction === 'asc'
    ? left - right
    : right - left
}

export function filterAndSortListings(
  listings: readonly Listing[],
  filters: ListingFilters,
) {
  const search = normalizeText(filters.search)

  const locality = normalizeText(
    filters.locality,
  )

  const propertyType = normalizeText(
    filters.propertyType,
  )

  const furnishing = normalizeText(
    filters.furnishing,
  )

  const bedroom = filters.bedroom
    ? Number(filters.bedroom)
    : null

  const minPrice = parsePrice(
    filters.minPrice,
  )

  const maxPrice = parsePrice(
    filters.maxPrice,
  )

  const filtered = listings.filter(
    (listing) => {
      if (
        locality &&
        normalizeText(listing.locality) !==
          locality
      ) {
        return false
      }

      if (
        bedroom !== null &&
        listing.bedroom !== bedroom
      ) {
        return false
      }

      if (
        propertyType &&
        normalizeText(
          listing.property_type,
        ) !== propertyType
      ) {
        return false
      }

      if (
        furnishing &&
        normalizeText(
          listing.furnishing,
        ) !== furnishing
      ) {
        return false
      }

      if (
        minPrice !== null &&
        listing.price < minPrice
      ) {
        return false
      }

      if (
        maxPrice !== null &&
        listing.price > maxPrice
      ) {
        return false
      }

      if (search) {
        const searchableText = [
          listing.listing_id,
          listing.locality,
          listing.property_type,
          listing.furnishing,
          listing.project_id,
          listing.website,
          listing.bedroom === null
            ? ''
            : `${listing.bedroom} bhk`,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()

        if (!searchableText.includes(search)) {
          return false
        }
      }

      return true
    },
  )

  return [...filtered].sort(
    (left, right) => {
      switch (filters.sort) {
        case 'price-asc':
          return left.price - right.price

        case 'price-desc':
          return right.price - left.price

        case 'bedroom-asc':
          return compareNullableNumbers(
            left.bedroom,
            right.bedroom,
            'asc',
          )

        case 'bedroom-desc':
          return compareNullableNumbers(
            left.bedroom,
            right.bedroom,
            'desc',
          )

        case 'area-asc':
          return compareNullableNumbers(
            getNormalizedCarpetArea(left),
            getNormalizedCarpetArea(right),
            'asc',
          )

        case 'area-desc':
          return compareNullableNumbers(
            getNormalizedCarpetArea(left),
            getNormalizedCarpetArea(right),
            'desc',
          )

        case 'oldest':
          return left.posted_at.localeCompare(
            right.posted_at,
          )

        case 'newest':
        default:
          return right.posted_at.localeCompare(
            left.posted_at,
          )
      }
    },
  )
}

export function getUniqueStringValues(
  listings: readonly Listing[],
  selector: (
    listing: Listing,
  ) => string | null,
) {
  return Array.from(
    new Set(
      listings
        .map(selector)
        .filter(
          (value): value is string =>
            Boolean(value),
        ),
    ),
  ).sort((left, right) =>
    left.localeCompare(right),
  )
}
