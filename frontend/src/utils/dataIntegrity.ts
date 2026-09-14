import type { Listing } from '../types/listing'
import type { Project } from '../types/project'
import {
  isCarpetAreaNormalized,
  isSuperBuiltUpAreaNormalized,
} from './listing'
import {
  isCorruptListing,
  isFakeListing,
  isKnownUnreliableListing,
} from './listingQuality'
import {
  buildLiveListingCountByProject,
} from './project'

export interface DataIntegrityMetrics {
  totalListingRecords: number
  activeListingRecords: number
  inactiveListingRecords: number

  normalizedAreaRecords: number

  corruptListingRecords: number
  fakeListingRecords: number
  knownUnreliableRecords: number

  totalProjects: number
  projectCountMatches: number
  projectCountMismatches: number
  projectCountConsistencyPercent: number

  mismatchedProjectIds: string[]
}

export function computeDataIntegrity(
  listings: readonly Listing[],
  projects: readonly Project[],
): DataIntegrityMetrics {
  const activeListingRecords =
    listings.filter(
      (listing) => listing.is_live,
    ).length

  const normalizedAreaRecords =
    listings.filter(
      (listing) =>
        isCarpetAreaNormalized(listing) ||
        isSuperBuiltUpAreaNormalized(listing),
    ).length

  const corruptListingRecords =
    listings.filter(
      (listing) =>
        isCorruptListing(
          listing.listing_id,
        ),
    ).length

  const fakeListingRecords =
    listings.filter(
      (listing) =>
        isFakeListing(
          listing.listing_id,
        ),
    ).length

  const knownUnreliableRecords =
    listings.filter(
      (listing) =>
        isKnownUnreliableListing(
          listing.listing_id,
        ),
    ).length

  const liveListingCountsByProject =
    buildLiveListingCountByProject(
      listings,
    )

  const mismatchedProjectIds =
    projects
      .filter((project) => {
        const verifiedCount =
          liveListingCountsByProject.get(
            project.project_id,
          ) ?? 0

        return (
          project.total_listings !==
          verifiedCount
        )
      })
      .map(
        (project) =>
          project.project_id,
      )
      .sort()

  const projectCountMismatches =
    mismatchedProjectIds.length

  const projectCountMatches =
    projects.length -
    projectCountMismatches

  const projectCountConsistencyPercent =
    projects.length > 0
      ? (
          projectCountMatches /
          projects.length
        ) * 100
      : 0

  return {
    totalListingRecords:
      listings.length,

    activeListingRecords,

    inactiveListingRecords:
      listings.length -
      activeListingRecords,

    normalizedAreaRecords,

    corruptListingRecords,

    fakeListingRecords,

    knownUnreliableRecords,

    totalProjects:
      projects.length,

    projectCountMatches,

    projectCountMismatches,

    projectCountConsistencyPercent,

    mismatchedProjectIds,
  }
}
