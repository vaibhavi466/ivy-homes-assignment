import {
  useEffect,
  useState,
} from 'react'
import {
  Link,
  useParams,
} from 'react-router-dom'

import { getApiErrorMessage } from '../api/errors'
import { DetailField } from '../components/DetailField'
import { getListingById } from '../services/listings'
import type { Listing } from '../types/listing'
import {
  formatArea,
  formatPostedAt,
  formatPrice,
  getNormalizedCarpetArea,
  getNormalizedSuperBuiltUpArea,
} from '../utils/listing'

export function ListingDetailPage() {
  const { id } = useParams()

  const [listing, setListing] =
    useState<Listing | null>(null)

  const [error, setError] =
    useState<string | null>(null)

  const [isLoading, setIsLoading] =
    useState(true)

  const [retryKey, setRetryKey] =
    useState(0)

  useEffect(() => {
    let cancelled = false

    async function loadListing() {
      if (!id) {
        setError('Listing ID is missing')
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const response =
          await getListingById(id)

        if (!cancelled) {
          setListing(response)
        }
      } catch (requestError) {
        if (!cancelled) {
          setListing(null)

          setError(
            getApiErrorMessage(
              requestError,
            ),
          )
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    void loadListing()

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
          Loading listing…
        </div>
      </section>
    )
  }

  if (error || !listing) {
    return (
      <section className="detail-page">
        <Link
          className="back-link"
          to="/listings"
        >
          ← Back to listings
        </Link>

        <div
          className="state-card error-state"
          role="alert"
        >
          <h2>
            Could not load listing
          </h2>

          <p>
            {error ??
              'Listing was not found.'}
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

  const carpetArea =
    getNormalizedCarpetArea(listing)

  const superBuiltUpArea =
    getNormalizedSuperBuiltUpArea(
      listing,
    )

  return (
    <section className="detail-page">
      <Link
        className="back-link"
        to="/listings"
      >
        ← Back to listings
      </Link>

      <div className="detail-header">
        <div>
          <p className="page-eyebrow">
            {listing.website}
          </p>

          <h1>
            {formatPrice(listing.price)}
          </h1>

          <p className="detail-id">
            {listing.listing_id}
          </p>
        </div>

        <span
          className={
            listing.is_live
              ? 'listing-live-badge'
              : 'listing-inactive-badge'
          }
        >
          {listing.is_live
            ? 'Active'
            : 'Inactive'}
        </span>
      </div>

      {!listing.is_live && (
        <div className="listing-warning">
          This listing is no longer active
          in the source dataset.
        </div>
      )}

      <dl className="detail-grid">
        <DetailField
          label="Price"
          value={
            formatPrice(
              listing.price,
            )
          }
        />

        <DetailField
          label="Carpet area"
          value={
            formatArea(
              carpetArea,
            )
          }
        />

        <DetailField
          label="Built-up area"
          value={
            formatArea(
              superBuiltUpArea,
            )
          }
        />

        <DetailField
          label="Project"
          value={
            listing.project_id ??
            'Not specified'
          }
        />

        <DetailField
          label="Source"
          value={listing.website}
        />

        <DetailField
          label="Posted"
          value={
            formatPostedAt(
              listing.posted_at,
            )
          }
        />
      </dl>
    </section>
  )
}