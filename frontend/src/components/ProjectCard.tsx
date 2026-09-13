import {
  Link,
  useLocation,
} from 'react-router-dom'

import type { Project } from '../types/project'
import {
  formatProjectAreaRange,
  formatProjectPriceRange,
} from '../utils/project'

interface ProjectCardProps {
  project: Project
  verifiedListingCount: number
}

export function ProjectCard({
  project,
  verifiedListingCount,
}: ProjectCardProps) {
  const location =
    useLocation()

  const returnTo =
    `${location.pathname}${location.search}`

  const listingCountMismatch =
    project.total_listings !==
    verifiedListingCount

  return (
    <article className="listing-card">
      <div className="listing-card-header">
        <div>
          <p className="listing-source">
            {project.developer_name ??
              'Developer not specified'}
          </p>

          <h2 className="project-name">
            {project.apartment_name}
          </h2>
        </div>

        <span className="project-status-badge">
          {project.project_status ??
            'status unknown'}
        </span>
      </div>

      <p className="project-price">
        {formatProjectPriceRange(
          project,
        )}
      </p>

      <dl className="listing-facts">
        <div>
          <dt>Locality</dt>

          <dd>
            {project.locality ??
              'Not specified'}
          </dd>
        </div>

        <div>
          <dt>Area range</dt>

          <dd>
            {formatProjectAreaRange(
              project,
            )}
          </dd>
        </div>

        <div>
          <dt>Total units</dt>

          <dd>
            {project.total_units?.toLocaleString(
              'en-IN',
            ) ?? 'Not specified'}
          </dd>
        </div>

        <div>
          <dt>Live listings</dt>

          <dd>
            {verifiedListingCount}
          </dd>
        </div>
      </dl>

      {listingCountMismatch && (
        <div className="metadata-warning">
          API metadata reports{' '}
          {project.total_listings}{' '}
          listings; verified live
          association count is{' '}
          {verifiedListingCount}.
        </div>
      )}

      <div className="listing-card-footer">
        <span className="listing-id">
          {project.project_id}
        </span>

        <Link
          to={`/projects/${encodeURIComponent(
            project.project_id,
          )}`}
          state={{
            from: returnTo,
          }}
        >
          View project
        </Link>
      </div>
    </article>
  )
}
