import { endpoints } from '../api/endpoints'
import { protectedRequest } from '../api/protectedClient'
import { buildQueryString } from '../api/query'
import type { ApiCollectionResponse } from '../types/api'
import type { Project } from '../types/project'

const MAX_PROJECT_PAGE_SIZE = 50

let allProjectsPromise:
  Promise<Project[]> | null = null

export interface ProjectPageParams {
  offset?: number
  limit?: number
}

function normalizeOffset(
  offset: number | undefined,
) {
  if (
    offset === undefined ||
    !Number.isFinite(offset)
  ) {
    return 0
  }

  return Math.max(
    0,
    Math.trunc(offset),
  )
}

function normalizeLimit(
  limit: number | undefined,
) {
  if (
    limit === undefined ||
    !Number.isFinite(limit)
  ) {
    return MAX_PROJECT_PAGE_SIZE
  }

  return Math.min(
    MAX_PROJECT_PAGE_SIZE,
    Math.max(
      1,
      Math.trunc(limit),
    ),
  )
}

export async function getProjects(
  params: ProjectPageParams = {},
) {
  const query = buildQueryString({
    offset: normalizeOffset(
      params.offset,
    ),

    limit: normalizeLimit(
      params.limit,
    ),
  })

  return protectedRequest<
    ApiCollectionResponse<Project>
  >(`${endpoints.projects}${query}`)
}

export async function getProjectById(
  id: string,
) {
  const projectId = id.trim()

  if (!projectId) {
    throw new Error(
      'Project ID is required',
    )
  }

  return protectedRequest<Project>(
    endpoints.project(projectId),
  )
}

export async function getAllProjects() {
  const projects: Project[] = []

  const seenIds =
    new Set<string>()

  let offset = 0

  while (true) {
    const page =
      await getProjects({
        offset,
        limit:
          MAX_PROJECT_PAGE_SIZE,
      })

    for (
      const project of page.results
    ) {
      if (
        !seenIds.has(
          project.project_id,
        )
      ) {
        seenIds.add(
          project.project_id,
        )

        projects.push(project)
      }
    }

    if (!page.has_more) {
      break
    }

    if (
      page.results.length === 0
    ) {
      throw new Error(
        'Projects API reported more records but returned an empty page',
      )
    }

    offset +=
      page.results.length
  }

  return projects
}

export function getAllProjectsCached() {
  if (!allProjectsPromise) {
    allProjectsPromise =
      getAllProjects().catch(
        (error: unknown) => {
          allProjectsPromise = null

          throw error
        },
      )
  }

  return allProjectsPromise
}
