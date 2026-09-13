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
        <nav
          className="app-nav"
          aria-label="Primary navigation"
        >
          <NavLink to="/listings">
            Listings
          </NavLink>

          <NavLink to="/saved">
            Saved

            {savedCount > 0 && (
              <span className="nav-count">
                {savedCount}
              </span>
            )}
          </NavLink>

          <NavLink to="/rentals">
            Rentals
          </NavLink>

          <NavLink to="/projects">
            Projects
          </NavLink>

          <NavLink to="/insights">
            Insights
          </NavLink>
        </nav>

        <div className="app-account">
          <span>
            {session?.user.email}
          </span>

          <button
            type="button"
            onClick={handleLogout}
          >
            Log out
          </button>
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
