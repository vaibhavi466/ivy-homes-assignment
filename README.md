# Ivy Homes Software Engineering Assignment

Engineering investigation and production frontend implementation for the Ivy Homes Software Engineering Internship assignment.

## Live Application

**Demo:** https://ivy-homes-assignment-tau.vercel.app

**Repository:** https://github.com/vaibhavi466/ivy-homes-assignment

The deployed application uses the real Ivy Homes API and the demo login credentials supplied with the assignment.

## Status

Complete.

The repository contains:

- a reproducible investigation of the running Ivy Homes API
- verification of discrepancies between the supplied documentation and actual runtime behaviour
- the ten required assignment answers
- confirmed API/documentation findings
- preserved raw analysis snapshots
- reproducible analysis scripts
- a React + TypeScript frontend deployed on Vercel

## Assignment Objective

The goal of the assignment was not simply to implement the supplied API documentation.

The running API was treated as the source of truth.

The work therefore followed two parallel tracks:

1. investigate and verify the real API contract
2. build a frontend that remains correct even where the documented contract is incomplete or inaccurate

Correctness and reproducibility were prioritized over assuming the documentation was correct.

## Final Answer Summary

The final verified results are stored in `submission.json`.

Key results include:

| Metric | Verified result |
| --- | ---: |
| Retrievable listing records | 3,500 |
| Distinct physical properties | 3,254 |
| Active listing records | 2,792 |
| Monthly rent in assigned locality | ₹4,328,000 |
| Average price/sq ft for valid active 2 BHK listings | ₹14,230.56 |
| Listings posted in the required 7-day interval | 129 |
| Projects with incorrect reported listing counts | 106 |
| Costliest project | P60060 |
| Maximum normalized project price | ₹58,300,000 |

The confirmed corrupt and fake listing IDs are recorded in `submission.json` together with the documented API findings.

## Repository Structure

```text
.
├── data/
│   └── raw/                    preserved API snapshots used for analysis
├── docs/
│   ├── documentation-audit.md  documentation-vs-runtime verification
│   ├── investigation-log.md    detailed hypotheses, tests, and evidence
│   ├── observed-contract.md    verified runtime API contract
│   └── requirements.md         assignment acceptance checklist
├── frontend/
│   ├── src/                    React + TypeScript application
│   ├── README.md               detailed frontend architecture
│   └── vercel.json             SPA deployment routing
├── scripts/                    reproducible investigation and validation tools
├── submission.json             required answers and findings
└── README.md
```

## Investigation Method

The API investigation was performed before relying on any documented behaviour.

For each meaningful API behaviour, the process was:

```text
Documentation claim
        ↓
Observation
        ↓
Hypothesis
        ↓
Controlled API test
        ↓
Evidence collection
        ↓
Confirmed / Rejected / Inconclusive
        ↓
Impact on analysis and frontend
```

The detailed chronological investigation is preserved in:

```text
docs/investigation-log.md
```

The final documentation audit is in:

```text
docs/documentation-audit.md
```

The resulting verified runtime contract is summarized in:

```text
docs/observed-contract.md
```

Rejected hypotheses were deliberately retained rather than deleted so that the investigation shows both what was wrong and what was tested and found to behave correctly.

## Major API Discoveries

### Authentication

Protected endpoints require the API key through:

```text
X-API-Key
```

rather than relying on the documented query-parameter mechanism.

The actual login response exposes:

```text
access_token
refresh_token
token_type
expires_in
refresh_url
user
```

The access token expires after 900 seconds.

The frontend therefore implements token-aware protected requests, refresh-token renewal, concurrent-refresh coordination, and one retry after authentication renewal.

### Pagination and Collection Completeness

The runtime collection API uses:

```text
offset
limit
```

The effective page size limit is 50.

The documented/reported collection totals cannot safely be used as the stopping condition.

Complete retrieval instead continues until:

```text
has_more = false
```

This produced:

```text
Listings: 3,500 retrievable records
Rentals:  1,320 retrievable records
Projects:   400 retrievable records
```

For example, the listings collection reports fewer records through its `total` metadata than can actually be retrieved.

All final analysis and frontend collection services therefore page to the real end of the dataset.

### Listing Detail Endpoint

The documented listing-detail path does not match the working runtime path.

The verified working route is:

```text
GET /v1/listings/{id}
```

The frontend uses the observed route rather than the failing documented route.

### Filtering and Sorting

Documented filters were tested independently rather than assumed to work.

Several filters do behave correctly, including useful listing, rental, and project filters.

However, some documented server sorting behaviour is unreliable. In particular, descending ordering is not consistently respected.

Because the frontend fully retrieves the relevant datasets, deterministic user-facing sorting is performed client-side.

### Sale Listing Area Units

A subset of sale listings from the `magichomes` source contains area values encoded in square metres despite the apparent square-foot contract.

The affected sale-listing areas were identified empirically and normalized using:

```text
1 square metre = 10.7639 square feet
```

Normalization is applied before area display, area sorting, and price-per-square-foot analytics.

This conversion is intentionally scoped to the verified affected sale records rather than globally applied to every dataset.

### Rentals

Rental records were independently checked rather than inheriting the sale-listing area rule.

Rental areas were found to already be consistent with square feet.

Rental timestamps also use explicit UTC `Z` timestamps, unlike the timezone-naive sale-listing timestamps.

Rental locality, BHK, furnishing, and combined filtering were confirmed to work.

### Project Prices

Project price fields use mixed numeric units.

The verified normalization rule is:

```text
raw value < 10  -> crore
raw value >= 10 -> lakh
```

Each endpoint value is normalized independently.

For example:

```text
1.66 -> ₹1,66,00,000
94.6 -> ₹94,60,000
```

This normalization resolves apparent invalid ranges such as a raw minimum value numerically larger than the raw maximum.

### Project Listing Counts

The `total_listings` value on project records cannot be assumed to equal the actual number of live listings associated with that project.

Independent association against the complete live listing dataset found:

```text
106 / 400 projects
```

with incorrect reported counts.

The frontend therefore computes the verified live-listing association count independently and visibly flags metadata mismatches.

### Missing Favourites API

The documented favourites endpoints were unavailable during runtime verification.

Instead of leaving a mandatory frontend feature broken, the application implements a browser-local compatibility fallback.

Only listing IDs are persisted.

Storage is namespaced by the authenticated user's normalized email address so saved listings remain user-specific across reload, logout, and re-login.

### Missing Analytics Summary

The documented analytics-summary endpoint was unavailable.

The Insights screen therefore computes the relevant metrics from the complete retrievable listing collection in the browser.

The UI explicitly labels these values as client-computed rather than pretending that the missing endpoint exists.

## What Was Tested and Found to Work

The investigation also verified behaviour that did not require a discrepancy finding.

Examples include:

- rental detail retrieval through the documented rental detail endpoint
- project detail retrieval through the documented project detail endpoint
- rental locality filtering
- rental BHK filtering
- rental furnishing filtering
- project locality filtering
- project-status filtering
- useful ascending sort behaviour for several fields
- rental areas being consistently represented as square feet
- rental timestamps containing explicit UTC timezone information
- direct retrieval of inactive sale-listing records by ID

These checks are retained in the investigation log so the audit does not contain only negative findings.

## Frontend

The production frontend is located in:

```text
frontend/
```

It is built with:

- React 19
- TypeScript
- React Router
- Vite
- ESLint

No UI framework or charting library is required.

### Implemented Features

The application contains:

- real API login
- persisted authenticated sessions
- automatic token refresh
- protected routes
- complete listing retrieval
- listing search and filtering
- deterministic sorting
- listing detail pages
- per-user saved listings
- rental browsing and details
- project browsing and details
- normalized project prices
- verified project listing-count comparisons
- client-computed market insights
- URL-persisted browse state
- pagination
- responsive layouts
- keyboard navigation
- skip navigation
- visible focus states
- safe external URLs
- global runtime error handling

Detailed frontend documentation is available in:

```text
frontend/README.md
```

## Running the Frontend Locally

Requirements:

```text
Node.js
npm
A valid assignment API key
Demo credentials supplied with the assignment
```

Move into the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Copy the environment template.

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Configure:

```env
VITE_IVY_BASE_URL=https://solve.ivy.homes
VITE_IVY_API_KEY=your_assignment_api_key
```

Do not commit the real `.env`.

Start the development server:

```bash
npm run dev
```

Production build:

```bash
npm run build
```

Lint:

```bash
npm run lint
```

Preview the production build:

```bash
npm run preview
```

## Reproducing the Investigation

The repository contains standalone scripts under:

```text
scripts/
```

These scripts were used to:

- retrieve complete datasets
- audit pagination
- test filters and sorting
- inspect duplicate properties
- detect unit anomalies
- analyze project/listing consistency
- verify required answers
- validate the final submission structure

The final submission validator can be run from the repository root:

```powershell
python scripts\validate_submission.py
```

The investigation log documents which script or API test corresponds to each major conclusion.

## Data and Evidence Policy

Raw snapshots were retained during investigation so repeated analysis could be performed locally instead of repeatedly calling the API.

Final findings distinguish between:

```text
documented behaviour
```

and:

```text
observed runtime behaviour
```

Record-level findings include concrete evidence identifiers.

Speculative discrepancies were not added to the final findings list.

## Deployment

The frontend is deployed on Vercel:

https://ivy-homes-assignment-tau.vercel.app

The Vercel project uses:

```text
Root directory: frontend
Framework: Vite
Build command: npm run build
Output directory: dist
```

`frontend/vercel.json` provides SPA fallback routing so direct navigation and refresh work correctly for routes such as:

```text
/listings/{id}
/rentals/{id}
/projects/{id}
/insights
```

## AI / LLM Usage

AI tooling was used during development as a programming and reasoning assistant.

It was used to help:

- structure the investigation plan
- suggest controlled API experiments
- review test outputs
- draft analysis scripts
- draft and refactor frontend code
- identify edge cases worth testing
- organize documentation

AI-generated claims were not treated as evidence.

API behaviour was verified through executed requests, local scripts, saved responses, and manual inspection.

Generated code was run and reviewed before being committed, and findings were only included after their behaviour had been reproduced against the actual assignment API.

Final responsibility for the submitted answers, findings, code, and interpretation remains with the candidate.

## If I Had Two More Days

With two additional days I would focus on strengthening verification and operational quality rather than adding unrelated features.

The highest-priority improvements would be:

1. Add automated unit tests for normalization, filtering, pagination termination, project-price conversion, and analytics calculations.
2. Add Playwright end-to-end tests covering login, token refresh, direct detail navigation, saved listings across accounts, and browse-state restoration.
3. Add automated accessibility checks with axe-core and perform a full screen-reader review.
4. Add route-level code splitting and profile initial full-dataset loading performance.
5. Add stronger cache invalidation and background refresh behaviour while preserving the verified completeness rules.
6. Add a small diagnostics view exposing data provenance and collection-refresh timestamps.
7. Re-run the complete API audit to detect any runtime behaviour that changed after the original investigation.

## Final Verification

Before submission the project was checked with:

```text
Frontend production build
Frontend ESLint
Live Vercel deployment
Direct SPA route refreshes
Login and logout
Listing filters and sorting
Listing detail
Saved listings
Rentals
Projects
Insights
URL-persisted browse state
Keyboard navigation
Session recovery
Final submission schema validation
```

The live production application and repository are both intended to be directly usable by an evaluator without relying on undocumented local setup.