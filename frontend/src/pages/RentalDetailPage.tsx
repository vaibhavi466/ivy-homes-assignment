import {
  useEffect,
  useState,
} from 'react'

import {
  Link,
  useLocation,
  useParams,
} from 'react-router-dom'

import { getApiErrorMessage } from '../api/errors'
import { DetailField } from '../components/DetailField'
import { getRentalById } from '../services/rentals'
import type { Rental } from '../types/rental'
import {
  formatMonthlyRent,
  formatRentalArea,
  formatRentalMoney,
  formatRentalPostedAt,
} from '../utils/rental'
import {
  getSafeExternalUrl,
} from '../utils/url'

interface RentalDetailLocationState {
  from?: string
}

export function RentalDetailPage() {
  const { id } =
    useParams()

  const location =
    useLocation()

  const state =
    location.state as
      | RentalDetailLocationState
      | null

  const backTo =
    state?.from &&
    state.from.startsWith(
      '/rentals',
    ) &&
    !state.from.startsWith(
      '//',
    )
      ? state.from
      : '/rentals'

  const [rental, setRental] =
    useState<Rental | null>(
      null,
    )

  const [error, setError] =
    useState<string | null>(
      null,
    )

  const [isLoading, setIsLoading] =
    useState(true)

  const [retryKey, setRetryKey] =
    useState(0)

  useEffect(() => {
    let cancelled = false

    async function loadRental() {
      if (!id) {
        setError(
          'Rental ID is missing',
        )

        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const response =
          await getRentalById(
            id,
          )

        if (!cancelled) {
          setRental(response)
        }
      } catch (
        requestError
      ) {
        if (!cancelled) {
          setRental(null)

          setError(
            getApiErrorMessage(
              requestError,
            ),
          )
        }
      } finally {
        if (!cancelled) {
          setIsLoading(
            false,
          )
        }
      }
    }

    void loadRental()

    return () => {
      cancelled = true
    }
  }, [id, retryKey])

  if (isLoading) {
    return (
      <section className="detail-page">
        <div
          className="state-card"
          role="status"
        >
          Loading rental…
        </div>
      </section>
    )
  }

  if (
    error ||
    !rental
  ) {
    return (
      <section className="detail-page">
        <Link
          className="back-link"
          to={backTo}
        >
          ← Back to rentals
        </Link>

        <div
          className="state-card error-state"
          role="alert"
        >
          <h2>
            Could not load rental
          </h2>

          <p>
            {error ??
              'Rental was not found.'}
          </p>

          <button
            type="button"
            onClick={() =>
              setRetryKey(
                (current) =>
                  current + 1,
              )
            }
          >
            Try again
          </button>
        </div>
      </section>
    )
  }

  const sourceUrl =
    getSafeExternalUrl(
      rental.listing_url,
    )

  return (
    <section className="detail-page">
      <Link
        className="back-link"
        to={backTo}
      >
        ← Back to rentals
      </Link>

      <div className="detail-header">
        <div>
          <p className="page-eyebrow">
            {rental.website}
          </p>

          <h1>
            {formatMonthlyRent(
              rental.price,
            )}
          </h1>

          <p className="detail-id">
            {rental.listing_id}
          </p>
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

      <h2 className="rental-detail-title">
        {rental.title}
      </h2>

      {!rental.is_live && (
        <div className="listing-warning">
          This rental is no longer
          active in the source dataset.
        </div>
      )}

      <dl className="detail-grid">
        <DetailField
          label="Monthly rent"
          value={
            formatMonthlyRent(
              rental.price,
            )
          }
        />

        <DetailField
          label="Deposit"
          value={
            formatRentalMoney(
              rental.deposit,
            )
          }
        />

        <DetailField
          label="Maintenance"
          value={
            formatRentalMoney(
              rental.maintenance,
            )
          }
        />

        <DetailField
          label="Locality"
          value={
            rental.locality ??
            'Not specified'
          }
        />

        <DetailField
          label="Apartment"
          value={
            rental.apartment_name ??
            'Not specified'
          }
        />

        <DetailField
          label="Property type"
          value={
            rental.property_type ??
            'Not specified'
          }
        />

        <DetailField
          label="BHK"
          value={
            rental.bedroom === null
              ? 'Not specified'
              : `${rental.bedroom} BHK`
          }
        />

        <DetailField
          label="Bathrooms"
          value={
            rental.bathroom ??
            'Not specified'
          }
        />

        <DetailField
          label="Carpet area"
          value={
            formatRentalArea(
              rental.carpet_area,
            )
          }
        />

        <DetailField
          label="Built-up area"
          value={
            formatRentalArea(
              rental.super_builtup_area,
            )
          }
        />

        <DetailField
          label="Floor"
          value={
            rental.floor === null
              ? 'Not specified'
              : `${rental.floor} of ${rental.total_floors ?? '?'}`
          }
        />

        <DetailField
          label="Furnishing"
          value={
            rental.furnishing ??
            'Not specified'
          }
        />

        <DetailField
          label="Facing"
          value={
            rental.facing_direction ??
            'Not specified'
          }
        />

        <DetailField
          label="Posted"
          value={
            formatRentalPostedAt(
              rental.posted_at,
            )
          }
        />
      </dl>

      {rental.description && (
        <section className="rental-description">
          <h2>Description</h2>

          <p>
            {rental.description}
          </p>
        </section>
      )}

      {sourceUrl && (
        <a
          className="source-link"
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
        >
          View original listing ↗
        </a>
      )}
    </section>
  )
}
