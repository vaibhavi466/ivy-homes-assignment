import {
    authenticatedRequest,
} from './authenticatedClient'
import { ApiError } from './client'
import {
    clearSession,
    isSessionExpired,
    loadSession,
} from '../auth/session'
import { refreshSession } from '../services/auth'
import type { AuthSession } from '../types/auth'

type ProtectedRequestOptions =
    Omit<RequestInit, 'body'> & {
        body?: unknown
    }

let refreshPromise: Promise<AuthSession> | null = null

function authenticationRequiredError() {
    return new Error('Authentication required')
}

function isUnauthorized(error: unknown) {
    return (
        error instanceof ApiError &&
        error.status === 401
    )
}

async function getRefreshedSession(
    session: AuthSession,
) {
    if (!refreshPromise) {
        refreshPromise = refreshSession(session)
            .catch((error: unknown) => {
                clearSession()
                throw error
            })
            .finally(() => {
                refreshPromise = null
            })
    }

    return refreshPromise
}

async function getUsableSession() {
    const session = loadSession()

    if (!session) {
        throw authenticationRequiredError()
    }

    if (!isSessionExpired(session)) {
        return session
    }

    return getRefreshedSession(session)
}

export async function protectedRequest<T>(
    path: string,
    options: ProtectedRequestOptions = {},
): Promise<T> {
    let session = await getUsableSession()

    try {
        return await authenticatedRequest<T>(
            path,
            session.tokens.accessToken,
            options,
        )
    } catch (error) {
        if (!isUnauthorized(error)) {
            throw error
        }
    }

    /*
     * The token may have expired earlier than expected,
     * so refresh once after a 401 and retry the request.
     */
    const latestSession = loadSession()

    if (
        latestSession &&
        latestSession.tokens.accessToken !==
        session.tokens.accessToken &&
        !isSessionExpired(latestSession)
    ) {
        /*
         * Another request may already have refreshed
         * the session while this request was in flight.
         */
        session = latestSession
    } else {
        if (!latestSession) {
            clearSession()
            throw authenticationRequiredError()
        }

        session = await getRefreshedSession(
            latestSession,
        )
    }

    try {
        return await authenticatedRequest<T>(
            path,
            session.tokens.accessToken,
            options,
        )
    } catch (error) {
        if (isUnauthorized(error)) {
            clearSession()
        }

        throw error
    }
}