import type { Listing } from '../types/listing'

const SQ_METRES_TO_SQ_FEET = 10.7639

function isMagichomes(listing: Listing) {
    return listing.website.toLowerCase() === 'magichomes'
}

export function getNormalizedCarpetArea(
    listing: Listing,
) {
    const area = listing.carpet_area

    if (area === null) {
        return null
    }

    if (
        isMagichomes(listing) &&
        area < 300
    ) {
        return area * SQ_METRES_TO_SQ_FEET
    }

    return area
}

export function getNormalizedSuperBuiltUpArea(
    listing: Listing,
) {
    const area = listing.super_built_up_area

    if (area === null) {
        return null
    }

    if (
        isMagichomes(listing) &&
        area < 400
    ) {
        return area * SQ_METRES_TO_SQ_FEET
    }

    return area
}

export function formatPrice(price: number) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0,
    }).format(price)
}

export function formatArea(
    area: number | null,
) {
    if (area === null) {
        return 'Not available'
    }

    return `${Math.round(area).toLocaleString('en-IN')} sq ft`
}

export function formatPostedAt(
    postedAt: string,
) {
    /*
     * Verified listing timestamps are timezone-naive.
     * Avoid new Date(...), which would invent a timezone
     * interpretation and may shift the displayed value.
     */
    return postedAt
        .replace('T', ' ')
        .replace(/:\d{2}$/, '')
}