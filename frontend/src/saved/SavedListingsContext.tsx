import {
    createContext,
    type ReactNode,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from 'react'

import { useAuth } from '../auth/AuthContext'
import {
    getSavedListingsStorageKey,
    loadSavedListingIds,
    saveSavedListingIds,
} from '../services/savedListings'

interface SavedListingsContextValue {
    savedListingIds: string[]
    savedCount: number

    isSaved: (
        listingId: string,
    ) => boolean

    toggleSaved: (
        listingId: string,
    ) => void
}

const SavedListingsContext =
    createContext<
        SavedListingsContextValue | undefined
    >(undefined)

interface SavedListingsProviderProps {
    children: ReactNode
}

export function SavedListingsProvider({
    children,
}: SavedListingsProviderProps) {
    const { session } = useAuth()

    const email =
        session?.user.email ?? null

    const [savedListingIds, setSavedListingIds] =
        useState<string[]>(() =>
            email ? loadSavedListingIds(email) : [],
        )

    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setSavedListingIds(
            email ? loadSavedListingIds(email) : [],
        )
    }, [email])

    useEffect(() => {
        if (!email) {
            return
        }

        const currentEmail = email

        const storageKey =
            getSavedListingsStorageKey(currentEmail)

        function handleStorage(
            event: StorageEvent,
        ) {
            if (
                event.storageArea !==
                localStorage ||
                event.key !== storageKey
            ) {
                return
            }

            setSavedListingIds(
                loadSavedListingIds(currentEmail),
            )
        }

        window.addEventListener(
            'storage',
            handleStorage,
        )

        return () => {
            window.removeEventListener(
                'storage',
                handleStorage,
            )
        }
    }, [email])

    const savedSet = useMemo(
        () =>
            new Set(savedListingIds),
        [savedListingIds],
    )

    const isSaved = useCallback(
        (listingId: string) =>
            savedSet.has(listingId),
        [savedSet],
    )

    const toggleSaved = useCallback(
        (listingId: string) => {
            if (!email) {
                return
            }

            const normalizedId =
                listingId.trim()

            if (!normalizedId) {
                return
            }

            setSavedListingIds(
                (current) => {
                    const next =
                        current.includes(
                            normalizedId,
                        )
                            ? current.filter(
                                (id) =>
                                    id !==
                                    normalizedId,
                            )
                            : [
                                normalizedId,
                                ...current,
                            ]

                    saveSavedListingIds(
                        email,
                        next,
                    )

                    return next
                },
            )
        },
        [email],
    )

    const value =
        useMemo<SavedListingsContextValue>(
            () => ({
                savedListingIds,
                savedCount:
                    savedListingIds.length,
                isSaved,
                toggleSaved,
            }),
            [
                savedListingIds,
                isSaved,
                toggleSaved,
            ],
        )

    return (
        <SavedListingsContext.Provider
            value={value}
        >
            {children}
        </SavedListingsContext.Provider>
    )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useSavedListings() {
    const context = useContext(
        SavedListingsContext,
    )

    if (!context) {
        throw new Error(
            'useSavedListings must be used within SavedListingsProvider',
        )
    }

    return context
}