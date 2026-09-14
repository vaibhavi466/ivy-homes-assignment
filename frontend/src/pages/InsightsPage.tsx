import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import { getApiErrorMessage } from '../api/errors'
import {
  getAllListingsCached,
} from '../services/listings'
import {
  getAllProjectsCached,
} from '../services/projects'
import type { Listing } from '../types/listing'
import type { Project } from '../types/project'
import {
  computeListingAnalytics,
} from '../utils/analytics'
import {
  computeDataIntegrity,
} from '../utils/dataIntegrity'
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

  const [projects, setProjects] =
    useState<Project[]>([])

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
        const [
          listingResponse,
          projectResponse,
        ] = await Promise.all([
          getAllListingsCached(),
          getAllProjectsCached(),
        ])

        if (!cancelled) {
          setListings(
            listingResponse,
          )

          setProjects(
            projectResponse,
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

  const integrity =
    useMemo(
      () =>
        computeDataIntegrity(
          listings,
          projects,
        ),
      [listings, projects],
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

      <section className="integrity-section">
        <div className="analytics-panel-heading">
          <div>
            <p className="page-eyebrow">
              Data integrity
            </p>

            <h2>
              What the API data actually contains
            </h2>
          </div>

          <span>
            Verified from complete retrievable
            datasets
          </span>
        </div>

        <p className="integrity-description">
          These observations are computed from
          the complete listings and projects
          collections rather than trusting the
          documented API assumptions.
        </p>

        <div className="integrity-grid">
          <article className="integrity-card">
            <span>
              Retrievable listings
            </span>

            <strong>
              {integrity.totalListingRecords.toLocaleString(
                'en-IN',
              )}
            </strong>

            <small>
              Complete listing collection
            </small>
          </article>

          <article className="integrity-card">
            <span>
              Inactive records returned
            </span>

            <strong>
              {integrity.inactiveListingRecords.toLocaleString(
                'en-IN',
              )}
            </strong>

            <small>
              Despite active-only documentation
            </small>
          </article>

          <article className="integrity-card">
            <span>
              Area-normalized records
            </span>

            <strong>
              {integrity.normalizedAreaRecords.toLocaleString(
                'en-IN',
              )}
            </strong>

            <small>
              Source-specific unit correction
            </small>
          </article>

          <article className="integrity-card">
            <span>
              Corrupt records
            </span>

            <strong>
              {integrity.corruptListingRecords.toLocaleString(
                'en-IN',
              )}
            </strong>

            <small>
              Impossible property data
            </small>
          </article>

          <article className="integrity-card">
            <span>
              Non-genuine records
            </span>

            <strong>
              {integrity.fakeListingRecords.toLocaleString(
                'en-IN',
              )}
            </strong>

            <small>
              Identified during dataset audit
            </small>
          </article>

          <article className="integrity-card">
            <span>
              Project count mismatches
            </span>

            <strong>
              {integrity.projectCountMismatches.toLocaleString(
                'en-IN',
              )}{' '}
              /{' '}
              {integrity.totalProjects.toLocaleString(
                'en-IN',
              )}
            </strong>

            <small>
              Reported vs verified live listings
            </small>
          </article>
        </div>

        <div className="integrity-consistency">
          <div>
            <span>
              Project metadata consistency
            </span>

            <strong>
              {integrity.projectCountConsistencyPercent.toFixed(
                1,
              )}
              %
            </strong>
          </div>

          <div
            className="integrity-progress"
            aria-label={`${integrity.projectCountConsistencyPercent.toFixed(
              1,
            )}% of project listing counts match the verified live-listing dataset`}
          >
            <div
              className="integrity-progress-value"
              style={{
                width: `${Math.min(
                  100,
                  Math.max(
                    0,
                    integrity.projectCountConsistencyPercent,
                  ),
                )}%`,
              }}
            />
          </div>

          <p>
            {integrity.projectCountMatches.toLocaleString(
              'en-IN',
            )}{' '}
            project records agree with the
            complete live-listing dataset;{' '}
            {integrity.projectCountMismatches.toLocaleString(
              'en-IN',
            )}{' '}
            do not.
          </p>
        </div>
      </section>

      <section className="integrity-impact">
        <div className="analytics-panel-heading">
          <div>
            <p className="page-eyebrow">
              Product impact
            </p>

            <h2>
              How these findings change the app
            </h2>
          </div>

          <span>
            Verified observations applied at runtime
          </span>
        </div>

        <div className="integrity-impact-grid">
          <article>
            <strong>
              {integrity.inactiveListingRecords.toLocaleString(
                'en-IN',
              )}
            </strong>

            <span>
              inactive records
            </span>

            <p>
              Excluded from market aggregates and
              treated separately from currently live
              inventory.
            </p>
          </article>

          <article>
            <strong>
              {integrity.normalizedAreaRecords.toLocaleString(
                'en-IN',
              )}
            </strong>

            <span>
              normalized-area records
            </span>

            <p>
              Converted before area display and
              price-per-square-foot calculations.
            </p>
          </article>

          <article>
            <strong>
              {integrity.knownUnreliableRecords.toLocaleString(
                'en-IN',
              )}
            </strong>

            <span>
              unreliable records
            </span>

            <p>
              Flagged in listing confidence checks
              and withheld from market comparisons.
            </p>
          </article>

          <article>
            <strong>
              {integrity.projectCountMismatches.toLocaleString(
                'en-IN',
              )}
            </strong>

            <span>
              project metadata mismatches
            </span>

            <p>
              Project pages compare reported counts
              with verified live-listing counts.
            </p>
          </article>
        </div>
      </section>

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
