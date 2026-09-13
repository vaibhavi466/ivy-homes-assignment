import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import { getApiErrorMessage } from '../api/errors'
import {
  getAllListingsCached,
} from '../services/listings'
import type { Listing } from '../types/listing'
import {
  computeListingAnalytics,
} from '../utils/analytics'
import {
  formatPrice,
} from '../utils/listing'

const TOP_LOCALITY_COUNT = 10

function formatMedianPrice(
  value: number | null,
) {
  return value === null
    ? 'Not available'
    : formatPrice(value)
}

function formatPricePerSqft(
  value: number | null,
) {
  if (value === null) {
    return 'Not available'
  }

  return `${formatPrice(
    value,
  )} / sq ft`
}

interface AnalyticsRowProps {
  label: string
  count: number
  maximumCount: number
  medianPrice: number | null
  medianPricePerSqft:
    number | null
}

function AnalyticsRow({
  label,
  count,
  maximumCount,
  medianPrice,
  medianPricePerSqft,
}: AnalyticsRowProps) {
  const percentage =
    maximumCount > 0
      ? Math.max(
          3,
          (count /
            maximumCount) *
            100,
        )
      : 0

  return (
    <div className="analytics-row">
      <div className="analytics-row-heading">
        <strong>
          {label}
        </strong>

        <span>
          {count.toLocaleString(
            'en-IN',
          )}{' '}
          listings
        </span>
      </div>

      <div
        className="analytics-bar-track"
        aria-hidden="true"
      >
        <div
          className="analytics-bar"
          style={{
            width: `${percentage}%`,
          }}
        />
      </div>

      <div className="analytics-row-metrics">
        <span>
          Median price:{' '}
          <strong>
            {formatMedianPrice(
              medianPrice,
            )}
          </strong>
        </span>

        <span>
          Median PPSF:{' '}
          <strong>
            {formatPricePerSqft(
              medianPricePerSqft,
            )}
          </strong>
        </span>
      </div>
    </div>
  )
}

export function InsightsPage() {
  const [listings, setListings] =
    useState<Listing[]>([])

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

    async function loadAnalyticsData() {
      setIsLoading(true)
      setError(null)

      try {
        const response =
          await getAllListingsCached()

        if (!cancelled) {
          setListings(
            response,
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
          setIsLoading(false)
        }
      }
    }

    void loadAnalyticsData()

    return () => {
      cancelled = true
    }
  }, [retryKey])

  const analytics =
    useMemo(
      () =>
        computeListingAnalytics(
          listings,
        ),
      [listings],
    )

  const topLocalities =
    analytics.localityGroups.slice(
      0,
      TOP_LOCALITY_COUNT,
    )

  const maximumLocalityCount =
    topLocalities[0]?.count ??
    0

  const maximumBedroomCount =
    Math.max(
      0,
      ...analytics.bedroomGroups.map(
        (group) =>
          group.count,
      ),
    )

  if (isLoading) {
    return (
      <section className="insights-page">
        <div
          className="state-card"
          role="status"
        >
          Computing insights from the
          complete listing dataset…
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="insights-page">
        <div
          className="state-card error-state"
          role="alert"
        >
          <h2>
            Could not compute insights
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
    <section className="insights-page">
      <div className="page-heading">
        <div>
          <p className="page-eyebrow">
            Market intelligence
          </p>

          <h1>Insights</h1>

          <p className="page-description">
            Client-computed analytics
            from the complete
            retrievable sale-listing
            dataset.
          </p>
        </div>
      </div>

      <div className="analytics-provenance">
        <strong>
          Client-computed fallback
        </strong>

        <p>
          The documented analytics
          summary endpoint is not
          available, so this screen
          derives its metrics from all
          retrievable listing pages,
          stopping on
          {' '}
          <code>
            has_more=false
          </code>
          . Known sale-area unit
          anomalies are normalized
          before price-per-square-foot
          calculations.
        </p>
      </div>

      <div className="analytics-summary-grid">
        <article className="analytics-summary-card">
          <span>
            Retrieved records
          </span>

          <strong>
            {analytics.totalRecords.toLocaleString(
              'en-IN',
            )}
          </strong>

          <small>
            Complete collection
          </small>
        </article>

        <article className="analytics-summary-card">
          <span>
            Active listings
          </span>

          <strong>
            {analytics.activeListings.toLocaleString(
              'en-IN',
            )}
          </strong>

          <small>
            Currently live
          </small>
        </article>

        <article className="analytics-summary-card">
          <span>
            Median asking price
          </span>

          <strong>
            {formatMedianPrice(
              analytics.medianPrice,
            )}
          </strong>

          <small>
            Active listings
          </small>
        </article>

        <article className="analytics-summary-card">
          <span>
            Median price / sq ft
          </span>

          <strong>
            {formatPricePerSqft(
              analytics.medianPricePerSqft,
            )}
          </strong>

          <small>
            Valid normalized
            carpet areas
          </small>
        </article>
      </div>

      <section className="analytics-panel">
        <div className="analytics-panel-heading">
          <div>
            <p className="page-eyebrow">
              Location
            </p>

            <h2>
              Top localities
            </h2>
          </div>

          <span>
            Ranked by active
            listing count
          </span>
        </div>

        <div className="analytics-list">
          {topLocalities.map(
            (group) => (
              <AnalyticsRow
                key={
                  group.label
                }
                label={
                  group.label
                }
                count={
                  group.count
                }
                maximumCount={
                  maximumLocalityCount
                }
                medianPrice={
                  group.medianPrice
                }
                medianPricePerSqft={
                  group.medianPricePerSqft
                }
              />
            ),
          )}
        </div>
      </section>

      <section className="analytics-panel">
        <div className="analytics-panel-heading">
          <div>
            <p className="page-eyebrow">
              Configuration
            </p>

            <h2>
              BHK distribution
            </h2>
          </div>

          <span>
            Active listing
            breakdown
          </span>
        </div>

        <div className="analytics-list">
          {analytics.bedroomGroups.map(
            (group) => (
              <AnalyticsRow
                key={
                  group.label
                }
                label={
                  group.label
                }
                count={
                  group.count
                }
                maximumCount={
                  maximumBedroomCount
                }
                medianPrice={
                  group.medianPrice
                }
                medianPricePerSqft={
                  group.medianPricePerSqft
                }
              />
            ),
          )}
        </div>
      </section>

      <section className="analytics-quality-panel">
        <div>
          <strong>
            {analytics.inactiveListings.toLocaleString(
              'en-IN',
            )}
          </strong>

          <span>
            inactive records excluded
            from market aggregates
          </span>
        </div>

        <div>
          <strong>
            {analytics.localityGroups.length.toLocaleString(
              'en-IN',
            )}
          </strong>

          <span>
            localities represented
            among active listings
          </span>
        </div>

        <div>
          <strong>
            {analytics.bedroomGroups.length.toLocaleString(
              'en-IN',
            )}
          </strong>

          <span>
            BHK groups represented
          </span>
        </div>
      </section>
    </section>
  )
}
