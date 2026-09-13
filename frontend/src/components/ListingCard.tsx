import { Link } from 'react-router-dom'

import type { Listing } from '../types/listing'
import {
  formatArea,
  formatPrice,
  getNormalizedCarpetArea,
  getNormalizedSuperBuiltUpArea,
} from '../utils/listing'

interface ListingCardProps {
  listing: Listing
}

export function ListingCard({
  listing,
}: ListingCardProps) {
  const carpetArea =
    getNormalizedCarpetArea(listing)

  const superBuiltUpArea =
    getNormalizedSuperBuiltUpArea(listing)

  return (
    <article className="listing-card">
      <div className="listing-card-header">
        <div>
          <p className="listing-source">
            {listing.website}
          </p>

          <h2>
            {formatPrice(listing.price)}
          </h2>
        </div>

        <span className="listing-live-badge">
          Active
        </span>
      </div>

      <dl className="listing-facts">
        <div>
          <dt>Locality</dt>
          <dd>
            {listing.locality ??
              'Not specified'}
          </dd>
        </div>

        <div>
          <dt>BHK</dt>
          <dd>
            {listing.bedroom === null
              ? 'Not specified'
              : `${listing.bedroom} BHK`}
          </dd>
        </div>

        <div>
          <dt>Property type</dt>
          <dd>
            {listing.property_type ??
              'Not specified'}
          </dd>
        </div>

        <div>
          <dt>Furnishing</dt>
          <dd>
            {listing.furnishing ??
              'Not specified'}
          </dd>
        </div>

        <div>
          <dt>Carpet area</dt>
          <dd>{formatArea(carpetArea)}</dd>
        </div>

        <div>
          <dt>Built-up area</dt>
          <dd>
            {formatArea(
              superBuiltUpArea,
            )}
          </dd>
        </div>
      </dl>

      <div className="listing-card-footer">
        <span className="listing-id">
          {listing.listing_id}
        </span>

        <Link
          to={`/listings/${encodeURIComponent(
            listing.listing_id,
          )}`}
        >
          View details
        </Link>
      </div>
    </article>
  )
}