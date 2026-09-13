import {
  type FormEvent,
  useEffect,
  useState,
} from 'react'
import {
  useLocation,
  useNavigate,
} from 'react-router-dom'

import { getApiErrorMessage } from '../api/errors'
import { useAuth } from '../auth/AuthContext'

interface LoginLocationState {
  from?: string
}

function getRedirectPath(
  state: LoginLocationState | null,
) {
  const from = state?.from

  if (
    !from ||
    !from.startsWith('/') ||
    from.startsWith('//')
  ) {
    return '/listings'
  }

  return from
}

export function LoginPage() {
  const {
    isAuthenticated,
    login,
  } = useAuth()

  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] =
    useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] =
    useState(false)

  const redirectPath = getRedirectPath(
    location.state as LoginLocationState | null,
  )

  useEffect(() => {
    if (isAuthenticated) {
      navigate(redirectPath, {
        replace: true,
      })
    }
  }, [
    isAuthenticated,
    navigate,
    redirectPath,
  ])

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setError(null)
    setIsSubmitting(true)

    try {
      await login(
        email.trim(),
        password,
      )

      navigate(redirectPath, {
        replace: true,
      })
    } catch (loginError) {
      setError(
        getApiErrorMessage(loginError),
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <p className="login-eyebrow">
          Ivy Homes
        </p>

        <h1>Sign in</h1>

        <p className="login-description">
          Use one of the provided demo accounts
          to access the property dashboard.
        </p>

        <form
          className="login-form"
          onSubmit={handleSubmit}
        >
          <label>
            Email

            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              autoComplete="email"
              required
            />
          </label>

          <label>
            Password

            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              autoComplete="current-password"
              required
            />
          </label>

          {error && (
            <p
              className="login-error"
              role="alert"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? 'Signing in...'
              : 'Sign in'}
          </button>
        </form>
      </section>
    </main>
  )
}
