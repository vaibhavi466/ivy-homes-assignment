import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import { getApiErrorMessage } from '../api/errors'
import { ProjectCard } from '../components/ProjectCard'
import {
  getAllListingsCached,
} from '../services/listings'
import {
  getAllProjectsCached,
} from '../services/projects'
import type { Project } from '../types/project'
import {
  useBrowseUrlState,
} from '../hooks/useBrowseUrlState'
import {
  DEFAULT_PROJECT_FILTERS,
  filterAndSortProjects,
  getUniqueProjectValues,
  type ProjectFilters,
} from '../utils/projectFilters'
import {
  buildLiveListingCountByProject,
} from '../utils/project'

const CLIENT_PAGE_SIZE = 24

const PROJECT_FILTER_PARAM_NAMES: {
  [Key in keyof ProjectFilters]:
    string
} = {
  search: 'q',
  locality: 'locality',
  status: 'status',
  developer: 'developer',
  minBudget: 'min_budget',
  maxBudget: 'max_budget',
  sort: 'sort',
}

const PROJECT_VALID_VALUES = {
  sort: [
    'name',
    'price-min-asc',
    'price-min-desc',
    'price-max-asc',
    'price-max-desc',
    'launch-newest',
    'launch-oldest',
    'units-desc',
    'units-asc',
  ],
} as const

export function ProjectsPage() {
  const [projects, setProjects] =
    useState<Project[]>([])

  const [
    listingCountByProject,
    setListingCountByProject,
  ] = useState<
    Map<string, number>
  >(
    () =>
      new Map(),
  )

  const {
    filters,
    pageIndex:
      requestedPageIndex,
    updateFilter,
    clearFilters,
    goToPage,
  } = useBrowseUrlState({
    defaults:
      DEFAULT_PROJECT_FILTERS,

    paramNames:
      PROJECT_FILTER_PARAM_NAMES,

    validValues:
      PROJECT_VALID_VALUES,
  })

  const [error, setError] =
    useState<string | null>(null)

  const [isLoading, setIsLoading] =
    useState(true)

  const [retryKey, setRetryKey] =
    useState(0)

  useEffect(() => {
    let cancelled = false

    async function loadProjects() {
      setIsLoading(true)
      setError(null)

      try {
        const [
          projectResponse,
          listingResponse,
        ] = await Promise.all([
          getAllProjectsCached(),
          getAllListingsCached(),
        ])

        if (!cancelled) {
          setProjects(
            projectResponse,
          )

          setListingCountByProject(
            buildLiveListingCountByProject(
              listingResponse,
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
          setIsLoading(false)
        }
      }
    }

    void loadProjects()

    return () => {
      cancelled = true
    }
  }, [retryKey])

  const localityOptions =
    useMemo(
      () =>
        getUniqueProjectValues(
          projects,
          (project) =>
            project.locality,
        ),
      [projects],
    )

  const statusOptions =
    useMemo(
      () =>
        getUniqueProjectValues(
          projects,
          (project) =>
            project.project_status,
        ),
      [projects],
    )

  const developerOptions =
    useMemo(
      () =>
        getUniqueProjectValues(
          projects,
          (project) =>
            project.developer_name,
        ),
      [projects],
    )

  const filteredProjects =
    useMemo(
      () =>
        filterAndSortProjects(
          projects,
          filters,
        ),
      [
        projects,
        filters,
      ],
    )

  const totalPages =
    Math.max(
      1,
      Math.ceil(
        filteredProjects.length /
          CLIENT_PAGE_SIZE,
      ),
    )

  const pageIndex =
    Math.min(
      requestedPageIndex,
      totalPages - 1,
    )

  const visibleProjects =
    useMemo(() => {
      const start =
        pageIndex *
        CLIENT_PAGE_SIZE

      return filteredProjects.slice(
        start,
        start +
          CLIENT_PAGE_SIZE,
      )
    }, [
      filteredProjects,
      pageIndex,
    ])

  const mismatchCount =
    useMemo(
      () =>
        projects.filter(
          (project) =>
            project.total_listings !==
            (
              listingCountByProject.get(
                project.project_id,
              ) ?? 0
            ),
        ).length,
      [
        projects,
        listingCountByProject,
      ],
    )



  if (isLoading) {
    return (
      <section className="listings-page">
        <div
          className="state-card"
          role="status"
        >
          Loading projects and
          verifying associated
          listings…
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
            Could not load projects
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
            Residential developments
          </p>

          <h1>Projects</h1>

          <p className="page-description">
            Explore projects with
            normalized prices and
            independently verified
            live-listing counts.
          </p>
        </div>

        <div className="page-status">
          <strong>
            {filteredProjects.length.toLocaleString(
              'en-IN',
            )}{' '}
            projects
          </strong>

          <span>
            {mismatchCount}{' '}
            listing-count metadata
            discrepancies detected
          </span>
        </div>
      </div>

      <div className="listing-filters">
        <label className="filter-search">
          <span>Search</span>

          <input
            type="search"
            placeholder="Project, developer, RERA…"
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
            value={
              filters.locality
            }
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
          <span>Status</span>

          <select
            value={
              filters.status
            }
            onChange={(event) =>
              updateFilter(
                'status',
                event.target.value,
              )
            }
          >
            <option value="">
              All statuses
            </option>

            {statusOptions.map(
              (status) => (
                <option
                  key={status}
                  value={status}
                >
                  {status}
                </option>
              ),
            )}
          </select>
        </label>

        <label>
          <span>Developer</span>

          <select
            value={
              filters.developer
            }
            onChange={(event) =>
              updateFilter(
                'developer',
                event.target.value,
              )
            }
          >
            <option value="">
              All developers
            </option>

            {developerOptions.map(
              (developer) => (
                <option
                  key={developer}
                  value={developer}
                >
                  {developer}
                </option>
              ),
            )}
          </select>
        </label>

        <label>
          <span>
            Minimum budget
          </span>

          <input
            type="number"
            min="0"
            step="100000"
            placeholder="₹ minimum"
            value={
              filters.minBudget
            }
            onChange={(event) =>
              updateFilter(
                'minBudget',
                event.target.value,
              )
            }
          />
        </label>

        <label>
          <span>
            Maximum budget
          </span>

          <input
            type="number"
            min="0"
            step="100000"
            placeholder="₹ maximum"
            value={
              filters.maxBudget
            }
            onChange={(event) =>
              updateFilter(
                'maxBudget',
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
                  .value as ProjectFilters['sort'],
              )
            }
          >
            <option value="name">
              Project name
            </option>

            <option value="price-min-asc">
              Starting price: low to high
            </option>

            <option value="price-min-desc">
              Starting price: high to low
            </option>

            <option value="price-max-asc">
              Maximum price: low to high
            </option>

            <option value="price-max-desc">
              Maximum price: high to low
            </option>

            <option value="launch-newest">
              Launch: newest first
            </option>

            <option value="launch-oldest">
              Launch: oldest first
            </option>

            <option value="units-desc">
              Units: high to low
            </option>

            <option value="units-asc">
              Units: low to high
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

      {visibleProjects.length ===
      0 ? (
        <div className="state-card">
          <h2>
            No matching projects
          </h2>

          <p>
            Try changing or clearing
            your filters.
          </p>
        </div>
      ) : (
        <div className="listing-grid">
          {visibleProjects.map(
            (project) => (
              <ProjectCard
                key={
                  project.project_id
                }
                project={project}
                verifiedListingCount={
                  listingCountByProject.get(
                    project.project_id,
                  ) ?? 0
                }
              />
            ),
          )}
        </div>
      )}

      {filteredProjects.length >
        0 && (
        <div className="pagination">
          <button
            type="button"
            disabled={
              pageIndex === 0
            }
            onClick={() =>
              goToPage(
                Math.max(
                  0,
                  pageIndex - 1,
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
              goToPage(
                Math.min(
                  totalPages - 1,
                  pageIndex + 1,
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
