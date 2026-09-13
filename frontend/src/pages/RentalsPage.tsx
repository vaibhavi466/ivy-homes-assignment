import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import { getApiErrorMessage } from '../api/errors'
import { RentalCard } from '../components/RentalCard'
import {
  getAllRentalsCached,
  getLiveRentals,
} from '../services/rentals'
import type { Rental } from '../types/rental'
import {
  DEFAULT_RENTAL_FILTERS,
  filterAndSortRentals,
  getUniqueRentalValues,
  type RentalFilters,
} from '../utils/rentalFilters'

const CLIENT_PAGE_SIZE = 24

export function RentalsPage() {
  const [rentals, setRentals] =
    useState<Rental[]>([])

  const [filters, setFilters] =
    useState<RentalFilters>(
      DEFAULT_RENTAL_FILTERS,
    )

  const [pageIndex, setPageIndex] =
    useState(0)

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

    async function loadRentals() {
      setIsLoading(true)
      setError(null)

      try {
        const response =
          await getAllRentalsCached()

        if (!cancelled) {
          setRentals(
            getLiveRentals(
              response,
            ),
          )
        }
      } catch (
        requestError
      ) {
        if (!cancelled) {
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

    void loadRentals()

    return () => {
      cancelled = true
    }
  }, [retryKey])

  const localityOptions =
    useMemo(
      () =>
        getUniqueRentalValues(
          rentals,
          (rental) =>
            rental.locality,
        ),
      [rentals],
    )

  const propertyTypeOptions =
    useMemo(
      () =>
        getUniqueRentalValues(
          rentals,
          (rental) =>
            rental.property_type,
        ),
      [rentals],
    )

  const furnishingOptions =
    useMemo(
      () =>
        getUniqueRentalValues(
          rentals,
          (rental) =>
            rental.furnishing,
        ),
      [rentals],
    )

  const bedroomOptions =
    useMemo(
      () =>
        Array.from(
          new Set(
            rentals
              .map(
                (rental) =>
                  rental.bedroom,
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
      [rentals],
    )

  const filteredRentals =
    useMemo(
      () =>
        filterAndSortRentals(
          rentals,
          filters,
        ),
      [
        rentals,
        filters,
      ],
    )

  const totalPages =
    Math.max(
      1,
      Math.ceil(
        filteredRentals.length /
          CLIENT_PAGE_SIZE,
      ),
    )

  const visibleRentals =
    useMemo(() => {
      const start =
        pageIndex *
        CLIENT_PAGE_SIZE

      return filteredRentals.slice(
        start,
        start +
          CLIENT_PAGE_SIZE,
      )
    }, [
      filteredRentals,
      pageIndex,
    ])

  function updateFilter<
    Key extends keyof RentalFilters,
  >(
    key: Key,
    value: RentalFilters[Key],
  ) {
    setFilters(
      (current) => ({
        ...current,
        [key]: value,
      }),
    )

    setPageIndex(0)
  }

  function clearFilters() {
    setFilters(
      DEFAULT_RENTAL_FILTERS,
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
          Loading the complete rental
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
            Could not load rentals
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
            Rental marketplace
          </p>

          <h1>Rentals</h1>

          <p className="page-description">
            Search active rental
            properties across the
            complete retrievable
            inventory.
          </p>
        </div>

        <div className="page-status">
          <strong>
            {filteredRentals.length.toLocaleString(
              'en-IN',
            )}{' '}
            matches
          </strong>

          <span>
            {rentals.length.toLocaleString(
              'en-IN',
            )}{' '}
            active rentals loaded
          </span>
        </div>
      </div>

      <div className="listing-filters">
        <label className="filter-search">
          <span>Search</span>

          <input
            type="search"
            placeholder="ID, locality, building…"
            value={
              filters.search
            }
            onChange={(
              event,
            ) =>
              updateFilter(
                'search',
                event.target
                  .value,
              )
            }
          />
        </label>

        <label>
          <span>Locality</span>

          <select
            value={
              filters.locality
            }
            onChange={(
              event,
            ) =>
              updateFilter(
                'locality',
                event.target
                  .value,
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
            value={
              filters.bedroom
            }
            onChange={(
              event,
            ) =>
              updateFilter(
                'bedroom',
                event.target
                  .value,
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
          <span>
            Property type
          </span>

          <select
            value={
              filters.propertyType
            }
            onChange={(
              event,
            ) =>
              updateFilter(
                'propertyType',
                event.target
                  .value,
              )
            }
          >
            <option value="">
              All types
            </option>

            {propertyTypeOptions.map(
              (
                propertyType,
              ) => (
                <option
                  key={
                    propertyType
                  }
                  value={
                    propertyType
                  }
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
            onChange={(
              event,
            ) =>
              updateFilter(
                'furnishing',
                event.target
                  .value,
              )
            }
          >
            <option value="">
              Any furnishing
            </option>

            {furnishingOptions.map(
              (furnishing) => (
                <option
                  key={
                    furnishing
                  }
                  value={
                    furnishing
                  }
                >
                  {furnishing}
                </option>
              ),
            )}
          </select>
        </label>

        <label>
          <span>
            Minimum rent
          </span>

          <input
            type="number"
            min="0"
            step="1000"
            placeholder="₹ minimum"
            value={
              filters.minRent
            }
            onChange={(
              event,
            ) =>
              updateFilter(
                'minRent',
                event.target
                  .value,
              )
            }
          />
        </label>

        <label>
          <span>
            Maximum rent
          </span>

          <input
            type="number"
            min="0"
            step="1000"
            placeholder="₹ maximum"
            value={
              filters.maxRent
            }
            onChange={(
              event,
            ) =>
              updateFilter(
                'maxRent',
                event.target
                  .value,
              )
            }
          />
        </label>

        <label>
          <span>Sort</span>

          <select
            value={
              filters.sort
            }
            onChange={(
              event,
            ) =>
              updateFilter(
                'sort',
                event.target
                  .value as RentalFilters['sort'],
              )
            }
          >
            <option value="newest">
              Newest first
            </option>

            <option value="oldest">
              Oldest first
            </option>

            <option value="rent-asc">
              Rent: low to high
            </option>

            <option value="rent-desc">
              Rent: high to low
            </option>

            <option value="bedroom-asc">
              BHK: low to high
            </option>

            <option value="bedroom-desc">
              BHK: high to low
            </option>

            <option value="area-asc">
              Area: small to large
            </option>

            <option value="area-desc">
              Area: large to small
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

      {visibleRentals.length ===
      0 ? (
        <div className="state-card">
          <h2>
            No matching rentals
          </h2>

          <p>
            Try changing or
            clearing your filters.
          </p>
        </div>
      ) : (
        <div className="listing-grid">
          {visibleRentals.map(
            (rental) => (
              <RentalCard
                key={
                  rental.listing_id
                }
                rental={rental}
              />
            ),
          )}
        </div>
      )}

      {filteredRentals.length >
        0 && (
        <div className="pagination">
          <button
            type="button"
            disabled={
              pageIndex === 0
            }
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
            Page {pageIndex + 1}{' '}
            of {totalPages}
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
                    totalPages -
                      1,
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
