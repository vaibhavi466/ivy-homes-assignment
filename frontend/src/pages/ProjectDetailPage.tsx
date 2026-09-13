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
import {
  getAllListingsCached,
} from '../services/listings'
import {
  getProjectById,
} from '../services/projects'
import type { Project } from '../types/project'
import {
  buildLiveListingCountByProject,
  formatProjectAreaRange,
  formatProjectDate,
  formatProjectPriceRange,
} from '../utils/project'
import {
  getSafeExternalUrl,
} from '../utils/url'

interface ProjectDetailLocationState {
  from?: string
}

export function ProjectDetailPage() {
  const { id } =
    useParams()

  const location =
    useLocation()

  const state =
    location.state as
      | ProjectDetailLocationState
      | null

  const backTo =
    state?.from &&
    state.from.startsWith(
      '/projects',
    ) &&
    !state.from.startsWith(
      '//',
    )
      ? state.from
      : '/projects'

  const [project, setProject] =
    useState<Project | null>(
      null,
    )

  const [
    verifiedListingCount,
    setVerifiedListingCount,
  ] = useState(0)

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

    async function loadProject() {
      if (!id) {
        setError(
          'Project ID is missing',
        )

        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const [
          projectResponse,
          listings,
        ] = await Promise.all([
          getProjectById(id),
          getAllListingsCached(),
        ])

        if (!cancelled) {
          setProject(
            projectResponse,
          )

          const counts =
            buildLiveListingCountByProject(
              listings,
            )

          setVerifiedListingCount(
            counts.get(
              projectResponse.project_id,
            ) ?? 0,
          )
        }
      } catch (
        requestError
      ) {
        if (!cancelled) {
          setProject(null)

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

    void loadProject()

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
          Loading project…
        </div>
      </section>
    )
  }

  if (
    error ||
    !project
  ) {
    return (
      <section className="detail-page">
        <Link
          className="back-link"
          to={backTo}
        >
          ← Back to projects
        </Link>

        <div
          className="state-card error-state"
          role="alert"
        >
          <h2>
            Could not load project
          </h2>

          <p>
            {error ??
              'Project was not found.'}
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

  const listingCountMismatch =
    project.total_listings !==
    verifiedListingCount

  const sourceUrl =
    getSafeExternalUrl(
      project.project_url,
    )

  return (
    <section className="detail-page">
      <Link
        className="back-link"
        to={backTo}
      >
        ← Back to projects
      </Link>

      <div className="detail-header">
        <div>
          <p className="page-eyebrow">
            {project.developer_name ??
              'Developer not specified'}
          </p>

          <h1>
            {project.apartment_name}
          </h1>

          <p className="detail-id">
            {project.project_id}
          </p>
        </div>

        <span className="project-status-badge">
          {project.project_status ??
            'status unknown'}
        </span>
      </div>

      <p className="project-detail-price">
        {formatProjectPriceRange(
          project,
        )}
      </p>

      {listingCountMismatch && (
        <div className="listing-warning">
          The API reports{' '}
          {project.total_listings}{' '}
          listings for this project,
          while the complete live
          listing dataset contains{' '}
          {verifiedListingCount}.
        </div>
      )}

      <dl className="detail-grid">
        <DetailField
          label="Locality"
          value={
            project.locality ??
            'Not specified'
          }
        />

        <DetailField
          label="Developer"
          value={
            project.developer_name ??
            'Not specified'
          }
        />

        <DetailField
          label="Price range"
          value={
            formatProjectPriceRange(
              project,
            )
          }
        />

        <DetailField
          label="Area range"
          value={
            formatProjectAreaRange(
              project,
            )
          }
        />

        <DetailField
          label="Total units"
          value={
            project.total_units?.toLocaleString(
              'en-IN',
            ) ??
            'Not specified'
          }
        />

        <DetailField
          label="Towers"
          value={
            project.total_towers ??
            'Not specified'
          }
        />

        <DetailField
          label="Floors"
          value={
            project.total_floors ??
            'Not specified'
          }
        />

        <DetailField
          label="Verified live listings"
          value={
            verifiedListingCount
          }
        />

        <DetailField
          label="Launch date"
          value={
            formatProjectDate(
              project.launch_date,
            )
          }
        />

        <DetailField
          label="Possession date"
          value={
            formatProjectDate(
              project.possession_date,
            )
          }
        />

        <DetailField
          label="RERA number"
          value={
            project.rera_number ??
            'Not specified'
          }
        />

        <DetailField
          label="Status"
          value={
            project.project_status ??
            'Not specified'
          }
        />
      </dl>

      {project.amenities.length >
        0 && (
        <section className="amenities-section">
          <h2>Amenities</h2>

          <div className="amenities-list">
            {project.amenities.map(
              (amenity) => (
                <span
                  key={amenity}
                  className="amenity-chip"
                >
                  {amenity}
                </span>
              ),
            )}
          </div>
        </section>
      )}

      {sourceUrl && (
        <a
          className="source-link"
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
        >
          View project source ↗
        </a>
      )}
    </section>
  )
}
