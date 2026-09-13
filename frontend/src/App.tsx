import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import { InsightsPage } from './pages/InsightsPage'
import { ListingDetailPage } from './pages/ListingDetailPage'
import { ListingsPage } from './pages/ListingsPage'
import { LoginPage } from './pages/LoginPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { RentalsPage } from './pages/RentalsPage'
import { SavedPage } from './pages/SavedPage'

function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/listings">Listings</Link>{' '}
        <Link to="/saved">Saved</Link>{' '}
        <Link to="/rentals">Rentals</Link>{' '}
        <Link to="/projects">Projects</Link>{' '}
        <Link to="/insights">Insights</Link>
      </nav>

      <Routes>
        <Route path="/" element={<Navigate to="/listings" replace />} />

        <Route path="/login" element={<LoginPage />} />

        <Route path="/listings" element={<ListingsPage />} />

        <Route
          path="/listings/:id"
          element={<ListingDetailPage />}
        />

        <Route path="/saved" element={<SavedPage />} />

        <Route path="/rentals" element={<RentalsPage />} />

        <Route path="/projects" element={<ProjectsPage />} />

        <Route path="/insights" element={<InsightsPage />} />

        <Route path="*" element={<Navigate to="/listings" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App