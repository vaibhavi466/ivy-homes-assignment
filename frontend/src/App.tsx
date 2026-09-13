import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { AppShell } from './components/AppShell'

import { InsightsPage } from './pages/InsightsPage'
import { ListingDetailPage } from './pages/ListingDetailPage'
import { ListingsPage } from './pages/ListingsPage'
import { LoginPage } from './pages/LoginPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { RentalDetailPage } from './pages/RentalDetailPage'
import { RentalsPage } from './pages/RentalsPage'
import { SavedPage } from './pages/SavedPage'

import { SavedListingsProvider } from './saved/SavedListingsContext'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <SavedListingsProvider>
          <Routes>
            <Route
              path="/login"
              element={<LoginPage />}
            />

            <Route element={<ProtectedRoute />}>
              <Route element={<AppShell />}>
                <Route
                  path="/"
                  element={
                    <Navigate
                      to="/listings"
                      replace
                    />
                  }
                />

                <Route
                  path="/listings"
                  element={<ListingsPage />}
                />

                <Route
                  path="/listings/:id"
                  element={<ListingDetailPage />}
                />

                <Route
                  path="/saved"
                  element={<SavedPage />}
                />

                <Route
                  path="/rentals"
                  element={<RentalsPage />}
                />

                <Route
                  path="/rentals/:id"
                  element={<RentalDetailPage />}
                />

                <Route
                  path="/projects"
                  element={<ProjectsPage />}
                />

                <Route
                  path="/insights"
                  element={<InsightsPage />}
                />
              </Route>
            </Route>

            <Route
              path="*"
              element={
                <Navigate
                  to="/listings"
                  replace
                />
              }
            />
          </Routes>
        </SavedListingsProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App