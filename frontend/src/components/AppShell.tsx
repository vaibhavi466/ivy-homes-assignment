import {
  NavLink,
  Outlet,
  useNavigate,
} from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { useSavedListings } from '../saved/SavedListingsContext'

export function AppShell() {
  const { session, logout } = useAuth()
  const { savedCount } = useSavedListings()
  const navigate = useNavigate()

  const userEmail = session?.user.email ?? ''
  const userInitial =
    userEmail.charAt(0).toUpperCase() || 'U'

  async function handleLogout() {
    try {
      await logout()
    } finally {
      navigate('/login', {
        replace: true,
      })
    }
  }

  return (
    <>
      <a
        className="skip-link"
        href="#main-content"
      >
        Skip to main content
      </a>

      <header className="app-header">
        <div className="app-header-inner">
          <NavLink
            className="app-brand"
            to="/listings"
            aria-label="Ivy Homes property intelligence"
          >
            <span
              className="app-brand-mark"
              aria-hidden="true"
            >
              I
            </span>

            <span className="app-brand-copy">
              <strong>Ivy Homes</strong>
              <span>Property Intelligence</span>
            </span>
          </NavLink>

          <nav
            className="app-nav"
            aria-label="Primary navigation"
          >
            <NavLink to="/listings">
              Listings
            </NavLink>

            <NavLink to="/rentals">
              Rentals
            </NavLink>

            <NavLink to="/projects">
              Projects
            </NavLink>

            <NavLink to="/saved">
              Saved

              {savedCount > 0 && (
                <span className="nav-count">
                  {savedCount}
                </span>
              )}
            </NavLink>

            <NavLink to="/insights">
              Insights
            </NavLink>
          </nav>

          <div className="app-account">
            <div className="account-identity">
              <span
                className="account-avatar"
                aria-hidden="true"
              >
                {userInitial}
              </span>

              <span className="account-copy">
                <span className="account-label">
                  Signed in
                </span>

                <span className="account-email">
                  {userEmail}
                </span>
              </span>
            </div>

            <button
              type="button"
              className="logout-button"
              onClick={handleLogout}
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <main
        id="main-content"
        tabIndex={-1}
      >
        <Outlet />
      </main>
    </>
  )
}
