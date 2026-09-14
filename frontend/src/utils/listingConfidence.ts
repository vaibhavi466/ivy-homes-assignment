import type { Listing } from '../types/listing'
import {
  getNormalizedCarpetArea,
  isCarpetAreaNormalized,
  isSuperBuiltUpAreaNormalized,
} from './listing'
import {
  isCorruptListing,
  isFakeListing,
} from './listingQuality'

export type ConfidenceLevel =
  | 'verified'
  | 'normalized'
  | 'warning'

export interface ConfidenceItem {
  level: ConfidenceLevel
  title: string
  description: string
}

export interface ListingConfidence {
  items: ConfidenceItem[]
  hasWarning: boolean
}

function getActivityItem(
  listing: Listing,
): ConfidenceItem {
  if (listing.is_live) {
    return {
      level: 'verified',
      title: 'Active listing',
      description:
        'This record is currently marked live in the source dataset.',
    }
  }

  return {
    level: 'warning',
    title: 'Inactive listing',
    description:
      'This record is retrievable but is currently marked inactive in the source dataset.',
  }
}

function getQualityItem(
  listing: Listing,
): ConfidenceItem {
  if (
    isCorruptListing(
      listing.listing_id,
    )
  ) {
    return {
      level: 'warning',
      title: 'Data-quality warning',
      description:
        'This listing was identified during the verified dataset audit as describing an impossible property.',
    }
  }

  if (
    isFakeListing(
      listing.listing_id,
    )
  ) {
    return {
      level: 'warning',
      title: 'Authenticity warning',
      description:
        'This listing was identified during the verified dataset audit as deliberately non-genuine.',
    }
  }

  return {
    level: 'verified',
    title: 'Quality checks passed',
    description:
      'This record is not among the listings identified as corrupt or deliberately non-genuine during the verified dataset audit.',
  }
}

function getAreaItem(
  listing: Listing,
): ConfidenceItem {
  const carpetArea =
    getNormalizedCarpetArea(listing)

  if (carpetArea === null) {
    return {
      level: 'warning',
      title: 'Carpet area unavailable',
      description:
        'A reliable price-per-square-foot comparison cannot be derived because this listing has no carpet-area value.',
    }
  }

  if (
    isCarpetAreaNormalized(listing) ||
    isSuperBuiltUpAreaNormalized(listing)
  ) {
    return {
      level: 'normalized',
      title: 'Area normalization applied',
      description:
        'This source belongs to the verified metric-scale area cluster, so affected area values are converted to square feet before display and market calculations.',
    }
  }

  return {
    level: 'verified',
    title: 'Area interpretation verified',
    description:
      'No source-specific area conversion is required for this listing before square-foot calculations.',
  }
}

export function getListingConfidence(
  listing: Listing,
): ListingConfidence {
  const items = [
    getActivityItem(listing),
    getQualityItem(listing),
    getAreaItem(listing),
  ]

  return {
    items,
    hasWarning: items.some(
      (item) =>
        item.level === 'warning',
    ),
  }
}
