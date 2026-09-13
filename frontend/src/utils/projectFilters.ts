import type { Project } from '../types/project'
import {
  normalizeProjectPrice,
} from './project'

export type ProjectSort =
  | 'name'
  | 'price-min-asc'
  | 'price-min-desc'
  | 'price-max-asc'
  | 'price-max-desc'
  | 'launch-newest'
  | 'launch-oldest'
  | 'units-desc'
  | 'units-asc'

export interface ProjectFilters {
  search: string
  locality: string
  status: string
  developer: string
  minBudget: string
  maxBudget: string
  sort: ProjectSort
}

export const DEFAULT_PROJECT_FILTERS:
  ProjectFilters = {
    search: '',
    locality: '',
    status: '',
    developer: '',
    minBudget: '',
    maxBudget: '',
    sort: 'name',
  }

function normalizeText(
  value: string | null | undefined,
) {
  return value
    ?.trim()
    .toLowerCase() ?? ''
}

function parseAmount(
  value: string,
) {
  if (!value.trim()) {
    return null
  }

  const parsed =
    Number(value)

  return Number.isFinite(parsed)
    ? parsed
    : null
}

function compareNullableNumbers(
  left: number | null,
  right: number | null,
  direction: 'asc' | 'desc',
) {
  if (
    left === null &&
    right === null
  ) {
    return 0
  }

  if (left === null) {
    return 1
  }

  if (right === null) {
    return -1
  }

  return direction === 'asc'
    ? left - right
    : right - left
}

export function filterAndSortProjects(
  projects: readonly Project[],
  filters: ProjectFilters,
) {
  const search =
    normalizeText(
      filters.search,
    )

  const locality =
    normalizeText(
      filters.locality,
    )

  const status =
    normalizeText(
      filters.status,
    )

  const developer =
    normalizeText(
      filters.developer,
    )

  const minBudget =
    parseAmount(
      filters.minBudget,
    )

  const maxBudget =
    parseAmount(
      filters.maxBudget,
    )

  const filtered =
    projects.filter(
      (project) => {
        if (
          locality &&
          normalizeText(
            project.locality,
          ) !== locality
        ) {
          return false
        }

        if (
          status &&
          normalizeText(
            project.project_status,
          ) !== status
        ) {
          return false
        }

        if (
          developer &&
          normalizeText(
            project.developer_name,
          ) !== developer
        ) {
          return false
        }

        const minimumPrice =
          normalizeProjectPrice(
            project.price_min,
          )

        const maximumPrice =
          normalizeProjectPrice(
            project.price_max,
          )

        if (
          minBudget !== null &&
          maximumPrice !== null &&
          maximumPrice <
            minBudget
        ) {
          return false
        }

        if (
          maxBudget !== null &&
          minimumPrice !== null &&
          minimumPrice >
            maxBudget
        ) {
          return false
        }

        if (search) {
          const searchableText = [
            project.project_id,
            project.apartment_name,
            project.developer_name,
            project.locality,
            project.project_status,
            project.rera_number,
            ...project.amenities,
          ]
            .filter(Boolean)
            .join(' ')
            .toLowerCase()

          if (
            !searchableText.includes(
              search,
            )
          ) {
            return false
          }
        }

        return true
      },
    )

  return [...filtered].sort(
    (left, right) => {
      switch (
        filters.sort
      ) {
        case 'price-min-asc':
          return compareNullableNumbers(
            normalizeProjectPrice(
              left.price_min,
            ),
            normalizeProjectPrice(
              right.price_min,
            ),
            'asc',
          )

        case 'price-min-desc':
          return compareNullableNumbers(
            normalizeProjectPrice(
              left.price_min,
            ),
            normalizeProjectPrice(
              right.price_min,
            ),
            'desc',
          )

        case 'price-max-asc':
          return compareNullableNumbers(
            normalizeProjectPrice(
              left.price_max,
            ),
            normalizeProjectPrice(
              right.price_max,
            ),
            'asc',
          )

        case 'price-max-desc':
          return compareNullableNumbers(
            normalizeProjectPrice(
              left.price_max,
            ),
            normalizeProjectPrice(
              right.price_max,
            ),
            'desc',
          )

        case 'launch-newest':
          return (
            right.launch_date ?? ''
          ).localeCompare(
            left.launch_date ?? '',
          )

        case 'launch-oldest':
          return (
            left.launch_date ?? ''
          ).localeCompare(
            right.launch_date ?? '',
          )

        case 'units-desc':
          return compareNullableNumbers(
            left.total_units,
            right.total_units,
            'desc',
          )

        case 'units-asc':
          return compareNullableNumbers(
            left.total_units,
            right.total_units,
            'asc',
          )

        case 'name':
        default:
          return left.apartment_name.localeCompare(
            right.apartment_name,
          )
      }
    },
  )
}

export function getUniqueProjectValues(
  projects: readonly Project[],
  selector: (
    project: Project,
  ) => string | null,
) {
  return Array.from(
    new Set(
      projects
        .map(selector)
        .filter(
          (
            value,
          ): value is string =>
            Boolean(value),
        ),
    ),
  ).sort(
    (left, right) =>
      left.localeCompare(
        right,
      ),
  )
}
