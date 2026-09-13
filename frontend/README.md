# Ivy Homes Property Explorer

A production-style React + TypeScript frontend for exploring the Ivy Homes assignment API.

The application is built against the API behaviour observed during a full documentation and data-quality audit. Where the runtime API differs from the documented contract, the frontend deliberately applies verified compatibility handling instead of relying on incorrect metadata or unavailable endpoints.

## Features

* Authentication with access-token refresh and protected routing
* Sale listings with full-dataset search, filtering, sorting, pagination, and detail views
* Per-user saved listings with browser persistence
* Rental search, filtering, sorting, pagination, and detail views
* Project browsing with normalized project pricing and verified live-listing counts
* Client-computed market Insights when the documented analytics endpoint is unavailable
* URL-persisted browse state across filters, sorting, pagination, refresh, Back/Forward navigation, and detail pages
* Responsive UI, keyboard navigation, visible focus states, skip navigation, safe external links, and a global error boundary
* Defensive session parsing and automatic access-token refresh

## Technology

The frontend uses React 19, TypeScript, React Router, Vite, and ESLint.

No UI framework or charting dependency is required. Market visualizations are rendered with lightweight React and CSS.

## Local Setup

Requirements:

```text
Node.js
npm
A valid Ivy Homes assignment API key
Valid demo login credentials supplied with the assignment
```

Install dependencies:

```bash
npm install
```

Create a local environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Update `.env` with the assignment API key:

```env
VITE_IVY_BASE_URL=https://solve.ivy.homes
VITE_IVY_API_KEY=your_assignment_api_key
```

Do not commit the real `.env` file.

Start the development server:

```bash
npm run dev
```

The application is normally available at:

```text
http://localhost:5173
```

Sign in using one of the demo accounts supplied with the assignment.

## Production Build

Run:

```bash
npm run build
```

Preview the production build locally:

```bash
npm run preview
```

Run the static checks with:

```bash
npm run lint
```

A successful production build is emitted to:

```text
dist/
```

The deployment host must support SPA fallback routing so direct visits to routes such as `/listings/:id`, `/rentals/:id`, and `/projects/:id` resolve to `index.html`.

## Environment Variables

`VITE_IVY_BASE_URL`

Base URL of the Ivy Homes API. The default assignment endpoint is:

```text
https://solve.ivy.homes
```

`VITE_IVY_API_KEY`

Assignment API credential used by browser requests through the required `X-API-Key` header.

Because variables prefixed with `VITE_` are compiled into the browser application, they must not be treated as server-side secrets. The application never commits the developer's local `.env` file.

## Architecture

The frontend is separated into several layers.

```text
src/
├── api/          HTTP transport, authentication headers, query helpers,
│                 error handling, and token-aware protected requests
├── auth/         session persistence, authentication context, route guards
├── saved/        per-user saved-listing state
├── services/     listings, rentals, projects, authentication, saved items
├── types/        API-domain TypeScript models
├── utils/        normalization, filtering, analytics, formatting, URL safety
├── hooks/        reusable browse-state behaviour
├── components/   application shell and reusable cards/detail fields
└── pages/        route-level application screens
```

Collection services retrieve records using `offset + limit` pagination and continue until the API returns:

```text
has_more = false
```

The frontend does not use the API's collection `total` value as a termination condition.

## Verified API Compatibility Handling

The assignment API was tested against its documented contract before the frontend was implemented.

### Authentication

Protected API calls use the verified:

```text
X-API-Key
```

header rather than relying on the documented query-parameter mechanism.

Login responses are handled using the runtime fields:

```text
access_token
refresh_token
token_type
expires_in
```

The API reports an access-token lifetime of 900 seconds. The application therefore performs refresh-token based renewal through the observed `/auth/refresh` endpoint and retries protected requests once after authentication renewal.

Logout always clears the browser session even though the observed backend token remains stateless.

### Collection Pagination

The runtime API uses:

```text
offset
limit
```

rather than page-number pagination.

The effective page limit is 50.

The application retrieves collection pages until `has_more` becomes false because the reported `total` metadata undercounts the complete retrievable datasets.

Verified retrievable collection sizes include:

```text
Sale listings: 3,500
Rentals:       1,320
Projects:        400
```

### Sale Listings

The complete listing collection contains:

```text
3,500 total listing records
2,792 active listings
708 inactive listings
```

Browsing operates on the complete retrieved dataset so counts, sorting, filtering, and client-side pagination do not depend on incorrect collection totals.

The verified detail route is:

```text
GET /v1/listings/{id}
```

Known sale-listing area-unit anomalies from the `magichomes` source are normalized from square metres to square feet before display, area sorting, and price-per-square-foot calculations.

Server-side descending sorting and some documented sort fields were observed to be unreliable, so user-facing ordering is performed client-side against the complete retrieved dataset.

### Saved Listings

The documented favourites endpoints were not available during runtime verification.

The frontend therefore provides a transparent compatibility fallback using browser storage.

Only saved listing IDs are persisted, and storage is namespaced by the authenticated user's normalized email address so demo accounts receive independent shortlists.

Listing data itself is still retrieved from the API.

### Rentals

Rental data is retrieved through the complete paginated collection rather than the incorrect reported total.

Rental areas were verified to already use square-foot values, so the sale-listing area normalization is not applied to rentals.

The rental UI performs deterministic client-side sorting, including descending ordering.

### Projects

Project prices use two observed numeric encodings even though the API documentation describes the fields as direct INR values.

The verified normalization is:

```text
raw value < 10  -> crore
raw value >= 10 -> lakh
```

Each value is normalized independently before displaying, filtering, or sorting project price ranges.

For example:

```text
1.66 -> ₹1,66,00,000
94.6 -> ₹94,60,000
```

The API's `total_listings` metadata disagrees with live listing associations for 106 of the 400 retrievable projects.

The Projects screen therefore computes live project-listing counts independently from the complete sale-listing dataset and visibly identifies metadata mismatches.

### Insights

The documented analytics summary endpoint was unavailable during runtime verification.

The Insights screen therefore computes the requested market metrics from the complete retrievable sale-listing collection in the browser and explicitly identifies the values as client-computed.

Insights include retrieved and active listing counts, median asking price, normalized median price per square foot, locality distributions, and BHK distributions.

## Data Integrity

The frontend intentionally separates API transport from data interpretation.

Known API discrepancies are handled in domain-specific utility and service layers rather than being hidden inside UI components. This keeps normalization, pagination, sorting, and compatibility behaviour auditable and reusable.

The frontend does not depend on the local investigation snapshots in `data/raw`; those snapshots were used during assignment analysis and verification only. Runtime application data is retrieved from the Ivy Homes API.

## Security and Resilience

Authentication sessions are validated before being restored from browser storage.

Invalid or corrupted persisted sessions are discarded safely.

Protected requests refresh near-expired access tokens and coordinate concurrent refresh requests to avoid duplicate refresh races.

External listing and project URLs are accepted only when they use `http` or `https`.

A React error boundary prevents unexpected render errors from taking down the entire application without recovery.

## Accessibility

The application provides keyboard-accessible navigation, a skip-to-content link, semantic form controls, visible `:focus-visible` styling, status/error announcements, disabled-state handling, and responsive layouts for smaller screens.

## Known Behaviour

Saved listings are intentionally browser-local because the documented favourites API is unavailable.

Analytics are intentionally client-computed because the documented analytics endpoint is unavailable.

Filtering and sorting operate against complete retrieved datasets, which makes the first visit to a data-heavy screen perform more requests than a single server page. Results are cached in-memory during the application session to avoid unnecessary repeat downloads.

## Assignment Verification

The project includes reproducible investigation scripts and documentation outside the frontend directory.

The final submission validator checks the computed answers and finding structure before submission:

```powershell
python scripts\validate_submission.py
```

The frontend can be independently verified with:

```bash
npm run build
npm run lint
```
