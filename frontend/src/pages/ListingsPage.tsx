import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import { getApiErrorMessage } from '../api/errors'
import { ListingCard } from '../components/ListingCard'
import {
  getAllListingsCached,
  getLiveListings,
} from '../services/listings'
import type { Listing } from '../types/listing'
import {
  DEFAULT_LISTING_FILTERS,
  filterAndSortListings,
  getUniqueStringValues,
  type ListingFilters,
} from '../utils/listingFilters'

const CLIENT_PAGE_SIZE = 24

export function ListingsPage() {
  const [listings, setListings] =
    useState<Listing[]>([])

  const [filters, setFilters] =
    useState<ListingFilters>(
      DEFAULT_LISTING_FILTERS,
    )

  const [pageIndex, setPageIndex] =
    useState(0)

  const [error, setError] =
    useState<string | null>(null)

  const [isLoading, setIsLoading] =
    useState(true)

  const [retryKey, setRetryKey] =
    useState(0)

  useEffect(() => {
    let cancelled = false

    async function loadListings() {
      setIsLoading(true)
      setError(null)

      try {
        const response =
          await getAllListingsCached()

        if (!cancelled) {
          setListings(
            getLiveListings(response),
          )
        }
      } catch (requestError) {
        if (!cancelled) {
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

    void loadListings()

    return () => {
      cancelled = true
    }
  }, [retryKey])

  const localityOptions = useMemo(
    () =>
      getUniqueStringValues(
        listings,
        (listing) =>
          listing.locality,
      ),
    [listings],
  )

  const propertyTypeOptions = useMemo(
    () =>
      getUniqueStringValues(
        listings,
        (listing) =>
          listing.property_type,
      ),
    [listings],
  )

  const furnishingOptions = useMemo(
    () =>
      getUniqueStringValues(
        listings,
        (listing) =>
          listing.furnishing,
      ),
    [listings],
  )

  const bedroomOptions = useMemo(
    () =>
      Array.from(
        new Set(
          listings
            .map(
              (listing) =>
                listing.bedroom,
            )
            .filter(
              (
                value,
              ): value is number =>
                value !== null,
            ),
        ),
      ).sort(
        (left, right) =>
          left - right,
      ),
    [listings],
  )

  const filteredListings = useMemo(
    () =>
      filterAndSortListings(
        listings,
        filters,
      ),
    [listings, filters],
  )

  const totalPages = Math.max(
    1,
    Math.ceil(
      filteredListings.length /
        CLIENT_PAGE_SIZE,
    ),
  )

  const visibleListings = useMemo(() => {
    const start =
      pageIndex * CLIENT_PAGE_SIZE

    return filteredListings.slice(
      start,
      start + CLIENT_PAGE_SIZE,
    )
  }, [
    filteredListings,
    pageIndex,
  ])

  function updateFilter<
    Key extends keyof ListingFilters,
  >(
    key: Key,
    value: ListingFilters[Key],
  ) {
    setFilters((current) => ({
      ...current,
      [key]: value,
    }))

    setPageIndex(0)
  }

  function clearFilters() {
    setFilters(
      DEFAULT_LISTING_FILTERS,
    )

    setPageIndex(0)
  }

  if (isLoading) {
    return (
      <section className="listings-page">
        <div
          className="state-card"
          role="status"
        >
          Loading the complete property
          inventory…
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="listings-page">
        <div
          className="state-card error-state"
          role="alert"
        >
          <h2>
            Could not load listings
          </h2>

          <p>{error}</p>

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

  return (
    <section className="listings-page">
      <div className="page-heading">
        <div>
          <p className="page-eyebrow">
            Property marketplace
          </p>

          <h1>Listings</h1>

          <p className="page-description">
            Search and compare active
            properties across the complete
            retrievable inventory.
          </p>
        </div>

        <div className="page-status">
          <strong>
            {filteredListings.length.toLocaleString(
              'en-IN',
            )}{' '}
            matches
          </strong>

          <span>
            {listings.length.toLocaleString(
              'en-IN',
            )}{' '}
            active listings loaded
          </span>
        </div>
      </div>

      <div className="listing-filters">
        <label className="filter-search">
          <span>Search</span>

          <input
            type="search"
            placeholder="Listing ID, locality, project…"
            value={filters.search}
            onChange={(event) =>
              updateFilter(
                'search',
                event.target.value,
              )
            }
          />
        </label>

        <label>
          <span>Locality</span>

          <select
            value={filters.locality}
            onChange={(event) =>
              updateFilter(
                'locality',
                event.target.value,
              )
            }
          >
            <option value="">
              All localities
            </option>

            {localityOptions.map(
              (locality) => (
                <option
                  key={locality}
                  value={locality}
                >
                  {locality}
                </option>
              ),
            )}
          </select>
        </label>

        <label>
          <span>BHK</span>

          <select
            value={filters.bedroom}
            onChange={(event) =>
              updateFilter(
                'bedroom',
                event.target.value,
              )
            }
          >
            <option value="">
              Any BHK
            </option>

            {bedroomOptions.map(
              (bedroom) => (
                <option
                  key={bedroom}
                  value={bedroom}
                >
                  {bedroom} BHK
                </option>
              ),
            )}
          </select>
        </label>

        <label>
          <span>Property type</span>

          <select
            value={
              filters.propertyType
            }
            onChange={(event) =>
              updateFilter(
                'propertyType',
                event.target.value,
              )
            }
          >
            <option value="">
              All types
            </option>

            {propertyTypeOptions.map(
              (propertyType) => (
                <option
                  key={propertyType}
                  value={propertyType}
                >
                  {propertyType}
                </option>
              ),
            )}
          </select>
        </label>

        <label>
          <span>Furnishing</span>

          <select
            value={
              filters.furnishing
            }
            onChange={(event) =>
              updateFilter(
                'furnishing',
                event.target.value,
              )
            }
          >
            <option value="">
              Any furnishing
            </option>

            {furnishingOptions.map(
              (furnishing) => (
                <option
                  key={furnishing}
                  value={furnishing}
                >
                  {furnishing}
                </option>
              ),
            )}
          </select>
        </label>

        <label>
          <span>Minimum price</span>

          <input
            type="number"
            min="0"
            step="100000"
            placeholder="₹ minimum"
            value={filters.minPrice}
            onChange={(event) =>
              updateFilter(
                'minPrice',
                event.target.value,
              )
            }
          />
        </label>

        <label>
          <span>Maximum price</span>

          <input
            type="number"
            min="0"
            step="100000"
            placeholder="₹ maximum"
            value={filters.maxPrice}
            onChange={(event) =>
              updateFilter(
                'maxPrice',
                event.target.value,
              )
            }
          />
        </label>

        <label>
          <span>Sort</span>

          <select
            value={filters.sort}
            onChange={(event) =>
              updateFilter(
                'sort',
                event.target
                  .value as ListingFilters['sort'],
              )
            }
          >
            <option value="newest">
              Newest first
            </option>

            <option value="oldest">
              Oldest first
            </option>

            <option value="price-asc">
              Price: low to high
            </option>

            <option value="price-desc">
              Price: high to low
            </option>

            <option value="bedroom-asc">
              BHK: low to high
            </option>

            <option value="bedroom-desc">
              BHK: high to low
            </option>

            <option value="area-asc">
              Carpet area: small to large
            </option>

            <option value="area-desc">
              Carpet area: large to small
            </option>
          </select>
        </label>

        <button
          className="clear-filters"
          type="button"
          onClick={clearFilters}
        >
          Clear filters
        </button>
      </div>

      {visibleListings.length === 0 ? (
        <div className="state-card">
          <h2>
            No matching listings
          </h2>

          <p>
            Try changing or clearing your
            filters.
          </p>
        </div>
      ) : (
        <div className="listing-grid">
          {visibleListings.map(
            (listing) => (
              <ListingCard
                key={listing.listing_id}
                listing={listing}
              />
            ),
          )}
        </div>
      )}

      {filteredListings.length > 0 && (
        <div className="pagination">
          <button
            type="button"
            disabled={pageIndex === 0}
            onClick={() =>
              setPageIndex(
                (current) =>
                  Math.max(
                    0,
                    current - 1,
                  ),
              )
            }
          >
            Previous
          </button>

          <span>
            Page {pageIndex + 1} of{' '}
            {totalPages}
          </span>

          <button
            type="button"
            disabled={
              pageIndex + 1 >=
              totalPages
            }
            onClick={() =>
              setPageIndex(
                (current) =>
                  Math.min(
                    totalPages - 1,
                    current + 1,
                  ),
              )
            }
          >
            Next
          </button>
        </div>
      )}
    </section>
  )
}