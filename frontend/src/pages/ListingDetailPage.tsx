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
import { ListingConfidencePanel } from '../components/ListingConfidencePanel'
import { useSavedListings } from '../saved/SavedListingsContext'
import {
  getAllListingsCached,
  getListingById,
} from '../services/listings'
import type { Listing } from '../types/listing'
import {
  formatArea,
  formatPostedAt,
  formatPrice,
  getNormalizedCarpetArea,
  getNormalizedSuperBuiltUpArea,
} from '../utils/listing'
import { isKnownUnreliableListing } from '../utils/listingQuality'
import {
  getMarketContext,
  type MarketContext,
} from '../utils/marketContext'

function formatPricePerSqFt(
  value: number,
) {
  return `${Math.round(
    value,
  ).toLocaleString('en-IN')} / sq ft`
}

function formatMarketDifference(
  value: number,
) {
  const absolute =
    Math.abs(value).toFixed(1)

  if (Math.abs(value) < 0.05) {
    return 'In line with peer median'
  }

  return value < 0
    ? `${absolute}% below peer median`
    : `${absolute}% above peer median`
}

export function ListingDetailPage() {
  const { id } = useParams()

  const {
    isSaved,
    toggleSaved,
  } = useSavedListings()

  const [listing, setListing] =
    useState<Listing | null>(null)

  const [marketContext, setMarketContext] =
    useState<MarketContext | null>(null)

  const [
    isMarketContextLoading,
    setIsMarketContextLoading,
  ] = useState(false)

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

  useEffect(() => {
    let cancelled = false

    async function loadMarketContext() {
      if (!listing) {
        setMarketContext(null)
        return
      }

      setIsMarketContextLoading(true)
      setMarketContext(null)

      try {
        const allListings =
          await getAllListingsCached()

        if (!cancelled) {
          setMarketContext(
            getMarketContext(
              listing,
              allListings,
            ),
          )
        }
      } catch {
        if (!cancelled) {
          setMarketContext(null)
        }
      } finally {
        if (!cancelled) {
          setIsMarketContextLoading(false)
        }
      }
    }

    void loadMarketContext()

    return () => {
      cancelled = true
    }
  }, [listing])

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

  const saved = isSaved(
    listing.listing_id,
  )

  const carpetArea =
    getNormalizedCarpetArea(listing)

  const superBuiltUpArea =
    getNormalizedSuperBuiltUpArea(
      listing,
    )

  const isUnreliableListing =
    isKnownUnreliableListing(
      listing.listing_id,
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

        <div className="detail-actions">
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

          <button
            className={
              saved
                ? 'save-button saved'
                : 'save-button'
            }
            type="button"
            aria-pressed={saved}
            onClick={() =>
              toggleSaved(
                listing.listing_id,
              )
            }
          >
            {saved
              ? 'Saved'
              : 'Save listing'}
          </button>
        </div>
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

      <ListingConfidencePanel
        listing={listing}
      />

      <section
        className="market-context"
        aria-labelledby="market-context-title"
      >
        <div>
          <p className="page-eyebrow">
            Market intelligence
          </p>

          <h2 id="market-context-title">
            How this listing compares
          </h2>

          <p>
            Compared with active{' '}
            {listing.bedroom !== null
              ? `${listing.bedroom} BHK `
              : ''}
            listings in{' '}
            {listing.locality ??
              'the same locality'}{' '}
            using normalized carpet area.
          </p>
        </div>

        {isMarketContextLoading && (
          <div
            className="state-card"
            role="status"
          >
            Calculating market context…
          </div>
        )}

        {!isMarketContextLoading &&
          marketContext && (
            <dl className="detail-grid">
              <DetailField
                label="Price per sq ft"
                value={formatPricePerSqFt(
                  marketContext.pricePerSqFt,
                )}
              />

              <DetailField
                label="Peer median"
                value={formatPricePerSqFt(
                  marketContext
                    .medianPricePerSqFt,
                )}
              />

              <DetailField
                label="Market position"
                value={formatMarketDifference(
                  marketContext
                    .differenceFromMedianPercent,
                )}
              />

              <DetailField
                label="Comparable listings"
                value={marketContext.comparableCount.toLocaleString(
                  'en-IN',
                )}
              />

              <DetailField
                label="Relative position"
                value={`Lower ₹/sq ft than ${Math.round(
                  marketContext
                    .lowerThanPeersPercent,
                )}% of comparable listings`}
              />
            </dl>
          )}

        {!isMarketContextLoading &&
          !marketContext && (
            <p className="market-context-unavailable">
              {isUnreliableListing
                ? 'Market comparison is withheld because this listing was flagged during the verified data-quality audit.'
                : 'Not enough comparable active listings are available to calculate reliable market context.'}
            </p>
          )}
      </section>
    </section>
  )
}