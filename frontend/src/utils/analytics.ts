import type { Listing } from '../types/listing'
import {
  getNormalizedCarpetArea,
} from './listing'

export interface ListingAnalyticsGroup {
  label: string
  count: number
  medianPrice: number | null
  medianPricePerSqft: number | null
}

export interface ListingAnalytics {
  totalRecords: number
  activeListings: number
  inactiveListings: number

  medianPrice: number | null

  medianPricePerSqft:
    number | null

  localityGroups:
    ListingAnalyticsGroup[]

  bedroomGroups:
    ListingAnalyticsGroup[]
}

function median(
  values: readonly number[],
) {
  if (values.length === 0) {
    return null
  }

  const sorted =
    [...values].sort(
      (left, right) =>
        left - right,
    )

  const middle =
    Math.floor(
      sorted.length / 2,
    )

  if (
    sorted.length % 2 === 0
  ) {
    return (
      (
        sorted[middle - 1] +
        sorted[middle]
      ) / 2
    )
  }

  return sorted[middle]
}

function getPricePerSqft(
  listing: Listing,
) {
  const area =
    getNormalizedCarpetArea(
      listing,
    )

  if (
    area === null ||
    area <= 0 ||
    !Number.isFinite(area) ||
    listing.price <= 0 ||
    !Number.isFinite(
      listing.price,
    )
  ) {
    return null
  }

  return listing.price / area
}

function buildGroup(
  label: string,
  listings: readonly Listing[],
): ListingAnalyticsGroup {
  const prices =
    listings
      .map(
        (listing) =>
          listing.price,
      )
      .filter(
        (price) =>
          Number.isFinite(price) &&
          price > 0,
      )

  const pricePerSqft =
    listings
      .map(getPricePerSqft)
      .filter(
        (
          value,
        ): value is number =>
          value !== null,
      )

  return {
    label,
    count: listings.length,
    medianPrice:
      median(prices),
    medianPricePerSqft:
      median(pricePerSqft),
  }
}

function groupByLocality(
  listings: readonly Listing[],
) {
  const grouped =
    new Map<
      string,
      Listing[]
    >()

  for (
    const listing of listings
  ) {
    const locality =
      listing.locality
        ?.trim()
        .toLowerCase() ||
      'unknown'

    const group =
      grouped.get(locality)

    if (group) {
      group.push(listing)
    } else {
      grouped.set(
        locality,
        [listing],
      )
    }
  }

  return Array.from(
    grouped.entries(),
    ([label, group]) =>
      buildGroup(
        label,
        group,
      ),
  ).sort(
    (left, right) =>
      right.count -
      left.count,
  )
}

function groupByBedroom(
  listings: readonly Listing[],
) {
  const grouped =
    new Map<
      string,
      Listing[]
    >()

  for (
    const listing of listings
  ) {
    const label =
      listing.bedroom === null
        ? 'Unknown'
        : `${listing.bedroom} BHK`

    const group =
      grouped.get(label)

    if (group) {
      group.push(listing)
    } else {
      grouped.set(
        label,
        [listing],
      )
    }
  }

  return Array.from(
    grouped.entries(),
    ([label, group]) =>
      buildGroup(
        label,
        group,
      ),
  ).sort(
    (left, right) => {
      const leftNumber =
        Number.parseInt(
          left.label,
          10,
        )

      const rightNumber =
        Number.parseInt(
          right.label,
          10,
        )

      if (
        Number.isNaN(
          leftNumber,
        )
      ) {
        return 1
      }

      if (
        Number.isNaN(
          rightNumber,
        )
      ) {
        return -1
      }

      return (
        leftNumber -
        rightNumber
      )
    },
  )
}

export function computeListingAnalytics(
  listings: readonly Listing[],
): ListingAnalytics {
  const activeListings =
    listings.filter(
      (listing) =>
        listing.is_live,
    )

  const prices =
    activeListings
      .map(
        (listing) =>
          listing.price,
      )
      .filter(
        (price) =>
          Number.isFinite(price) &&
          price > 0,
      )

  const pricePerSqft =
    activeListings
      .map(getPricePerSqft)
      .filter(
        (
          value,
        ): value is number =>
          value !== null,
      )

  return {
    totalRecords:
      listings.length,

    activeListings:
      activeListings.length,

    inactiveListings:
      listings.length -
      activeListings.length,

    medianPrice:
      median(prices),

    medianPricePerSqft:
      median(pricePerSqft),

    localityGroups:
      groupByLocality(
        activeListings,
      ),

    bedroomGroups:
      groupByBedroom(
        activeListings,
      ),
  }
}
