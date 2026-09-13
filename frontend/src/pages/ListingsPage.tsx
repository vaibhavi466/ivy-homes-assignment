import {
    useEffect,
    useMemo,
    useState,
} from 'react'

import { getApiErrorMessage } from '../api/errors'
import { ListingCard } from '../components/ListingCard'
import {
    getListings,
    getLiveListings,
} from '../services/listings'
import type { ApiCollectionResponse } from '../types/api'
import type { Listing } from '../types/listing'

const PAGE_SIZE = 50

export function ListingsPage() {
    const [offset, setOffset] = useState(0)

    const [page, setPage] =
        useState<ApiCollectionResponse<Listing> | null>(
            null,
        )

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
                const response = await getListings({
                    offset,
                    limit: PAGE_SIZE,
                })

                if (!cancelled) {
                    setPage(response)
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
    }, [offset, retryKey])

    const liveListings = useMemo(
        () =>
            page
                ? getLiveListings(page.results)
                : [],
        [page],
    )

    const pageNumber =
        Math.floor(offset / PAGE_SIZE) + 1

    function goToPreviousPage() {
        setOffset((current) =>
            Math.max(
                0,
                current - PAGE_SIZE,
            ),
        )
    }

    function goToNextPage() {
        if (!page?.has_more) {
            return
        }

        setOffset(
            (current) =>
                current + page.results.length,
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
                        Browse active sale listings
                        from the verified API dataset.
                    </p>
                </div>

                {page && !isLoading && (
                    <div className="page-status">
                        <strong>
                            Page {pageNumber}
                        </strong>

                        <span>
                            {liveListings.length}{' '}
                            active listings in this batch
                        </span>
                    </div>
                )}
            </div>

            {isLoading && (
                <div
                    className="state-card"
                    role="status"
                >
                    Loading listings…
                </div>
            )}

            {!isLoading && error && (
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
            )}

            {!isLoading &&
                !error &&
                page &&
                liveListings.length === 0 && (
                    <div className="state-card">
                        <h2>
                            No active listings on
                            this page
                        </h2>

                        <p>
                            This API batch contains
                            only inactive records.
                        </p>
                    </div>
                )}

            {!isLoading &&
                !error &&
                liveListings.length > 0 && (
                    <div className="listing-grid">
                        {liveListings.map(
                            (listing) => (
                                <ListingCard
                                    key={
                                        listing.listing_id
                                    }
                                    listing={listing}
                                />
                            ),
                        )}
                    </div>
                )}

            {!isLoading &&
                !error &&
                page && (
                    <div className="pagination">
                        <button
                            type="button"
                            disabled={offset === 0}
                            onClick={
                                goToPreviousPage
                            }
                        >
                            Previous
                        </button>

                        <span>
                            Page {pageNumber}
                        </span>

                        <button
                            type="button"
                            disabled={!page.has_more}
                            onClick={goToNextPage}
                        >
                            Next
                        </button>
                    </div>
                )}
        </section>
    )
}