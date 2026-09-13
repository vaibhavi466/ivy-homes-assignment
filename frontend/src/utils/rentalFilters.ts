import type { Rental } from '../types/rental'

export type RentalSort =
  | 'newest'
  | 'oldest'
  | 'rent-asc'
  | 'rent-desc'
  | 'bedroom-asc'
  | 'bedroom-desc'
  | 'area-asc'
  | 'area-desc'

export interface RentalFilters {
  search: string
  locality: string
  bedroom: string
  propertyType: string
  furnishing: string
  minRent: string
  maxRent: string
  sort: RentalSort
}

export const DEFAULT_RENTAL_FILTERS: RentalFilters = {
  search: '',
  locality: '',
  bedroom: '',
  propertyType: '',
  furnishing: '',
  minRent: '',
  maxRent: '',
  sort: 'newest',
}

function normalizeText(
  value: string | null | undefined,
) {
  return value
    ?.trim()
    .toLowerCase() ?? ''
}

function parseAmount(
  value: string,
) {
  if (!value.trim()) {
    return null
  }

  const parsed =
    Number(value)

  return Number.isFinite(parsed)
    ? parsed
    : null
}

function compareNullableNumbers(
  left: number | null,
  right: number | null,
  direction: 'asc' | 'desc',
) {
  if (
    left === null &&
    right === null
  ) {
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

export function filterAndSortRentals(
  rentals: readonly Rental[],
  filters: RentalFilters,
) {
  const search =
    normalizeText(
      filters.search,
    )

  const locality =
    normalizeText(
      filters.locality,
    )

  const propertyType =
    normalizeText(
      filters.propertyType,
    )

  const furnishing =
    normalizeText(
      filters.furnishing,
    )

  const bedroom =
    filters.bedroom
      ? Number(
          filters.bedroom,
        )
      : null

  const minRent =
    parseAmount(
      filters.minRent,
    )

  const maxRent =
    parseAmount(
      filters.maxRent,
    )

  const filtered =
    rentals.filter(
      (rental) => {
        if (
          locality &&
          normalizeText(
            rental.locality,
          ) !== locality
        ) {
          return false
        }

        if (
          bedroom !== null &&
          rental.bedroom !==
            bedroom
        ) {
          return false
        }

        if (
          propertyType &&
          normalizeText(
            rental.property_type,
          ) !== propertyType
        ) {
          return false
        }

        if (
          furnishing &&
          normalizeText(
            rental.furnishing,
          ) !== furnishing
        ) {
          return false
        }

        if (
          minRent !== null &&
          rental.price < minRent
        ) {
          return false
        }

        if (
          maxRent !== null &&
          rental.price > maxRent
        ) {
          return false
        }

        if (search) {
          const searchableText = [
            rental.listing_id,
            rental.title,
            rental.apartment_name,
            rental.locality,
            rental.property_type,
            rental.furnishing,
            rental.website,
            rental.bedroom === null
              ? ''
              : `${rental.bedroom} bhk`,
          ]
            .filter(Boolean)
            .join(' ')
            .toLowerCase()

          if (
            !searchableText.includes(
              search,
            )
          ) {
            return false
          }
        }

        return true
      },
    )

  return [...filtered].sort(
    (left, right) => {
      switch (
        filters.sort
      ) {
        case 'rent-asc':
          return (
            left.price -
            right.price
          )

        case 'rent-desc':
          return (
            right.price -
            left.price
          )

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
            left.carpet_area,
            right.carpet_area,
            'asc',
          )

        case 'area-desc':
          return compareNullableNumbers(
            left.carpet_area,
            right.carpet_area,
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

export function getUniqueRentalValues(
  rentals: readonly Rental[],
  selector: (
    rental: Rental,
  ) => string | null,
) {
  return Array.from(
    new Set(
      rentals
        .map(selector)
        .filter(
          (
            value,
          ): value is string =>
            Boolean(value),
        ),
    ),
  ).sort(
    (left, right) =>
      left.localeCompare(
        right,
      ),
  )
}
