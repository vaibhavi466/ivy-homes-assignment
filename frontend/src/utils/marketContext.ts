import type { Listing } from '../types/listing'
import { getNormalizedCarpetArea } from './listing'
import { isKnownUnreliableListing } from './listingQuality'

const MIN_COMPARABLE_COUNT = 5

export interface MarketContext {
    pricePerSqFt: number
    medianPricePerSqFt: number
    differenceFromMedianPercent: number
    lowerThanPeersPercent: number
    comparableCount: number
}

function getPricePerSqFt(
    listing: Listing,
): number | null {
    const area =
        getNormalizedCarpetArea(listing)

    if (
        area === null ||
        !Number.isFinite(area) ||
        area <= 0 ||
        !Number.isFinite(listing.price) ||
        listing.price <= 0
    ) {
        return null
    }

    return listing.price / area
}

function getMedian(
    values: readonly number[],
): number | null {
    if (values.length === 0) {
        return null
    }

    const sorted = [...values].sort(
        (a, b) => a - b,
    )

    const middle = Math.floor(
        sorted.length / 2,
    )

    if (sorted.length % 2 === 1) {
        return sorted[middle]
    }

    return (
        sorted[middle - 1] +
        sorted[middle]
    ) / 2
}

function isComparableListing(
  candidate: Listing,
  listing: Listing,
) {
  return (
    candidate.listing_id !==
      listing.listing_id &&
    !isKnownUnreliableListing(
      candidate.listing_id,
    ) &&
    candidate.is_live &&
    candidate.locality !== null &&
    listing.locality !== null &&
    candidate.locality ===
      listing.locality &&
    candidate.bedroom !== null &&
    listing.bedroom !== null &&
    candidate.bedroom ===
      listing.bedroom
  )
}

export function getMarketContext(
    listing: Listing,
    allListings: readonly Listing[],
): MarketContext | null {
    const pricePerSqFt =
        getPricePerSqFt(listing)

    if (
        pricePerSqFt === null ||
        listing.locality === null ||
        listing.bedroom === null
    ) {
        return null
    }

    const comparablePricePerSqFt =
        allListings
            .filter((candidate) =>
                isComparableListing(
                    candidate,
                    listing,
                ),
            )
            .map(getPricePerSqFt)
            .filter(
                (value): value is number =>
                    value !== null,
            )

    if (
        comparablePricePerSqFt.length <
        MIN_COMPARABLE_COUNT
    ) {
        return null
    }

    const medianPricePerSqFt =
        getMedian(
            comparablePricePerSqFt,
        )

    if (
        medianPricePerSqFt === null ||
        medianPricePerSqFt <= 0
    ) {
        return null
    }

    const differenceFromMedianPercent =
        ((pricePerSqFt -
            medianPricePerSqFt) /
            medianPricePerSqFt) *
        100

    const moreExpensivePeers =
        comparablePricePerSqFt.filter(
            (value) =>
                value > pricePerSqFt,
        ).length

    const lowerThanPeersPercent =
        (moreExpensivePeers /
            comparablePricePerSqFt.length) *
        100

    return {
        pricePerSqFt,
        medianPricePerSqFt,
        differenceFromMedianPercent,
        lowerThanPeersPercent,
        comparableCount:
            comparablePricePerSqFt.length,
    }
}