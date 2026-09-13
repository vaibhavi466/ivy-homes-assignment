import type { Listing } from '../types/listing'
import type { Project } from '../types/project'
import {
  formatArea,
  formatPrice,
} from './listing'

const CRORE_IN_INR =
  10_000_000

const LAKH_IN_INR =
  100_000

export function normalizeProjectPrice(
  value: number | null,
) {
  if (
    value === null ||
    !Number.isFinite(value)
  ) {
    return null
  }

  /*
   * Verified mixed-unit encoding:
   *
   * value < 10  -> crore
   * value >= 10 -> lakh
   */
  return value < 10
    ? value * CRORE_IN_INR
    : value * LAKH_IN_INR
}

export function formatProjectPrice(
  value: number | null,
) {
  const normalized =
    normalizeProjectPrice(value)

  if (normalized === null) {
    return 'Not available'
  }

  return formatPrice(
    normalized,
  )
}

export function formatProjectPriceRange(
  project: Project,
) {
  const minimum =
    normalizeProjectPrice(
      project.price_min,
    )

  const maximum =
    normalizeProjectPrice(
      project.price_max,
    )

  if (
    minimum === null &&
    maximum === null
  ) {
    return 'Price not available'
  }

  if (minimum === null) {
    return `Up to ${formatPrice(
      maximum!,
    )}`
  }

  if (maximum === null) {
    return `From ${formatPrice(
      minimum,
    )}`
  }

  return `${formatPrice(
    minimum,
  )} – ${formatPrice(
    maximum,
  )}`
}

export function formatProjectAreaRange(
  project: Project,
) {
  const minimum =
    project.min_area_sqft

  const maximum =
    project.max_area_sqft

  if (
    minimum === null &&
    maximum === null
  ) {
    return 'Not available'
  }

  if (minimum === null) {
    return `Up to ${formatArea(
      maximum,
    )}`
  }

  if (maximum === null) {
    return `From ${formatArea(
      minimum,
    )}`
  }

  return `${Math.round(
    minimum,
  ).toLocaleString(
    'en-IN',
  )} – ${Math.round(
    maximum,
  ).toLocaleString(
    'en-IN',
  )} sq ft`
}

export function formatProjectDate(
  value: string | null,
) {
  if (!value) {
    return 'Not specified'
  }

  const match =
    /^(\d{4})-(\d{2})-(\d{2})$/.exec(
      value,
    )

  if (!match) {
    return value
  }

  const [, year, month, day] =
    match

  const date =
    new Date(
      Date.UTC(
        Number(year),
        Number(month) - 1,
        Number(day),
      ),
    )

  return new Intl.DateTimeFormat(
    'en-IN',
    {
      dateStyle: 'medium',
      timeZone: 'UTC',
    },
  ).format(date)
}

export function buildLiveListingCountByProject(
  listings: readonly Listing[],
) {
  const counts =
    new Map<string, number>()

  for (
    const listing of listings
  ) {
    if (
      !listing.is_live ||
      !listing.project_id
    ) {
      continue
    }

    counts.set(
      listing.project_id,
      (counts.get(
        listing.project_id,
      ) ?? 0) + 1,
    )
  }

  return counts
}
