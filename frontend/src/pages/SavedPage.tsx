import {
  useEffect,
  useState,
} from 'react'

import { ListingCard } from '../components/ListingCard'
import { useSavedListings } from '../saved/SavedListingsContext'
import { getListingById } from '../services/listings'
import type { Listing } from '../types/listing'

export function SavedPage() {
  const { savedListingIds } =
    useSavedListings()

  const [listings, setListings] =
    useState<Listing[]>([])

  const [failedCount, setFailedCount] =
    useState(0)

  const [isLoading, setIsLoading] =
    useState(false)

  const [retryKey, setRetryKey] =
    useState(0)

  useEffect(() => {
    let cancelled = false

    async function loadSavedListings() {
      if (
        savedListingIds.length === 0
      ) {
        setListings([])
        setFailedCount(0)
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setFailedCount(0)

      const results =
        await Promise.allSettled(
          savedListingIds.map(
            (listingId) =>
              getListingById(
                listingId,
              ),
          ),
        )

      if (cancelled) {
        return
      }

      const loadedListings:
        Listing[] = []

      let failures = 0

      for (const result of results) {
        if (
          result.status ===
          'fulfilled'
        ) {
          loadedListings.push(
            result.value,
          )
        } else {
          failures += 1
        }
      }

      setListings(
        loadedListings,
      )

      setFailedCount(failures)
      setIsLoading(false)
    }

    void loadSavedListings()

    return () => {
      cancelled = true
    }
  }, [
    savedListingIds,
    retryKey,
  ])

  return (
    <section className="listings-page">
      <div className="page-heading">
        <div>
          <p className="page-eyebrow">
            Your shortlist
          </p>

          <h1>Saved Listings</h1>

          <p className="page-description">
            Listings saved for this
            signed-in demo account.
          </p>
        </div>

        <div className="page-status">
          <strong>
            {savedListingIds.length}{' '}
            saved
          </strong>

          <span>
            Stored locally for your
            account
          </span>
        </div>
      </div>

      {isLoading && (
        <div
          className="state-card"
          role="status"
        >
          Loading saved listings…
        </div>
      )}

      {!isLoading &&
        savedListingIds.length === 0 && (
          <div className="state-card">
            <h2>
              No saved listings yet
            </h2>

            <p>
              Save properties from the
              Listings or Detail screen
              to build your shortlist.
            </p>
          </div>
        )}

      {!isLoading &&
        failedCount > 0 && (
          <div
            className="saved-warning"
            role="status"
          >
            <span>
              {failedCount}{' '}
              saved{' '}
              {failedCount === 1
                ? 'listing could'
                : 'listings could'}{' '}
              not be loaded.
            </span>

            <button
              type="button"
              onClick={() =>
                setRetryKey(
                  (current) =>
                    current + 1,
                )
              }
            >
              Retry
            </button>
          </div>
        )}

      {!isLoading &&
        listings.length > 0 && (
          <div className="listing-grid">
            {listings.map(
              (listing) => (
                <ListingCard
                  key={
                    listing.listing_id
                  }
                  listing={listing}
                />
              ),
            )}
          </div>
        )}
    </section>
  )
}
