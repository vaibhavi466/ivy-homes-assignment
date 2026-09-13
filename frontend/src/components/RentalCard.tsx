import {
  Link,
  useLocation,
} from 'react-router-dom'

import type { Rental } from '../types/rental'
import {
  formatMonthlyRent,
  formatRentalArea,
  formatRentalMoney,
} from '../utils/rental'

interface RentalCardProps {
  rental: Rental
}

export function RentalCard({
  rental,
}: RentalCardProps) {
  const location =
    useLocation()

  const returnTo =
    `${location.pathname}${location.search}`

  return (
    <article className="listing-card">
      <div className="listing-card-header">
        <div>
          <p className="listing-source">
            {rental.website}
          </p>

          <h2>
            {formatMonthlyRent(
              rental.price,
            )}
          </h2>
        </div>

        <span
          className={
            rental.is_live
              ? 'listing-live-badge'
              : 'listing-inactive-badge'
          }
        >
          {rental.is_live
            ? 'Active'
            : 'Inactive'}
        </span>
      </div>

      <h3 className="rental-title">
        {rental.title}
      </h3>

      <dl className="listing-facts">
        <div>
          <dt>Locality</dt>
          <dd>
            {rental.locality ??
              'Not specified'}
          </dd>
        </div>

        <div>
          <dt>BHK</dt>
          <dd>
            {rental.bedroom === null
              ? 'Not specified'
              : `${rental.bedroom} BHK`}
          </dd>
        </div>

        <div>
          <dt>Furnishing</dt>
          <dd>
            {rental.furnishing ??
              'Not specified'}
          </dd>
        </div>

        <div>
          <dt>Carpet area</dt>
          <dd>
            {formatRentalArea(
              rental.carpet_area,
            )}
          </dd>
        </div>

        <div>
          <dt>Deposit</dt>
          <dd>
            {formatRentalMoney(
              rental.deposit,
            )}
          </dd>
        </div>

        <div>
          <dt>Maintenance</dt>
          <dd>
            {formatRentalMoney(
              rental.maintenance,
            )}
          </dd>
        </div>
      </dl>

      <div className="listing-card-footer">
        <span className="listing-id">
          {rental.listing_id}
        </span>

        <Link
          to={`/rentals/${encodeURIComponent(
            rental.listing_id,
          )}`}
          state={{
            from: returnTo,
          }}
        >
          View details
        </Link>
      </div>
    </article>
  )
}
