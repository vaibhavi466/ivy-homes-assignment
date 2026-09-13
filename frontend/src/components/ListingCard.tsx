import { Link } from 'react-router-dom'

import type { Listing } from '../types/listing'
import {
    formatArea,
    formatPostedAt,
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
                    <dt>Carpet area</dt>
                    <dd>{formatArea(carpetArea)}</dd>
                </div>

                <div>
                    <dt>Built-up area</dt>
                    <dd>
                        {formatArea(superBuiltUpArea)}
                    </dd>
                </div>

                <div>
                    <dt>Project</dt>
                    <dd>
                        {listing.project_id ??
                            'Not specified'}
                    </dd>
                </div>

                <div>
                    <dt>Posted</dt>
                    <dd>
                        {formatPostedAt(
                            listing.posted_at,
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