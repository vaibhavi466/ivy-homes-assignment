const STORAGE_PREFIX = 'ivy.saved-listings'

export function getSavedListingsStorageKey(
    email: string,
) {
    return `${STORAGE_PREFIX}:${email
        .trim()
        .toLowerCase()}`
}

function normalizeIds(value: unknown) {
    if (!Array.isArray(value)) {
        return []
    }

    return Array.from(
        new Set(
            value
                .filter(
                    (item): item is string =>
                        typeof item === 'string',
                )
                .map((item) => item.trim())
                .filter(Boolean),
        ),
    )
}

export function loadSavedListingIds(
    email: string,
) {
    const rawValue = localStorage.getItem(
        getSavedListingsStorageKey(email),
    )

    if (!rawValue) {
        return []
    }

    try {
        return normalizeIds(
            JSON.parse(rawValue),
        )
    } catch {
        return []
    }
}

export function saveSavedListingIds(
    email: string,
    listingIds: readonly string[],
) {
    const normalizedIds = normalizeIds(
        listingIds,
    )

    localStorage.setItem(
        getSavedListingsStorageKey(email),
        JSON.stringify(normalizedIds),
    )
}