# Ivy Homes API Investigation Log

This document records hypotheses tested against the running API.

A hypothesis is recorded whether it is confirmed or rejected.

---

## H-001 — Health endpoint availability, authentication, and timestamp convention

### Source

`API_REFERENCE.md` documents:

`GET /health`

as an unauthenticated endpoint returning service status and the server clock.

The global API conventions also state that timestamps are:

`ISO 8601, UTC, Z suffix, everywhere in the API`.

### Hypothesis

1. `/health` exists at the documented path.
2. `/health` can be called without API-key or user-session authentication.
3. The endpoint returns service status and server time.
4. Its timestamp follows the documented global UTC `Z` convention.

### Test

Sent:

```http
GET /health
```

without:

* API key
* Bearer token
* user session

The request was executed multiple times to confirm that the observed timestamp representation was stable.

### Evidence

Observed HTTP status:

```text
200
```

Observed content type:

```text
application/json
```

Representative response:

```json
{
  "status": "ok",
  "server_time": "2026-09-12T14:34:44.142140+05:30",
  "timezone": "Asia/Kolkata",
  "reference_date": "2026-09-10T00:00:00+05:30"
}
```

### Result

**Partially confirmed.**

Confirmed:

* `/health` exists at the documented path.
* It is accessible without authentication.
* It returns service status.
* It returns the server clock.

Rejected:

* The global documentation claim that timestamps use UTC with a `Z` suffix everywhere does not hold for `/health`.
* `server_time` carries an explicit `+05:30` offset.
* `reference_date` also carries an explicit `+05:30` offset.
* The endpoint explicitly reports its timezone as `Asia/Kolkata`.

### Impact

The frontend and analysis code must not assume that every API timestamp ends in `Z`.

Timestamp values should be parsed as timezone-aware ISO 8601 values using the offset supplied by the API.

This is a candidate documentation discrepancy under the `timestamps` findings category.


---

## H-002 — Login endpoint authentication contract

### Source

`API_REFERENCE.md` documents:

`POST /auth/login`

using an email/password JSON body.

The global authentication section states that every request must carry the API key and documents the key as an `api_key` query parameter.

The documented successful login response contains:

* `token`
* `token_type`
* `expires_in`
* `user`

The documentation states that tokens remain valid for 86400 seconds and that no refresh flow exists.

### Hypothesis

1. `/auth/login` exists at the documented path.
2. The documented email/password JSON body is accepted.
3. Login requires the assigned API key.
4. The documented `api_key` query-parameter mechanism authenticates the request.
5. A successful response follows the documented token-response structure.
6. Invalid credentials return an authentication error.

### Test

Performed controlled login requests using:

1. Valid demo credentials with no API key.
2. Valid demo credentials with the API key supplied using the documented query parameter.
3. Valid demo credentials with the `X-API-Key` request header indicated by the API error response.
4. Valid demo email with an incorrect password using the observed API-key mechanism.
5. A nonexistent demo-style email using the observed API-key mechanism.

Secrets and returned authentication tokens are excluded from the investigation log.

### Evidence

#### No API key

Observed:

```text
401
{"detail":"missing X-API-Key header"}
```

#### API key supplied using documented query parameter

Observed:

```text
401
{"detail":"send your key in the X-API-Key request header, not as a query parameter"}
```

#### Valid credentials with `X-API-Key`

Observed:

```text
200
```

Redacted response shape:

```json
{
  "access_token": "<REDACTED>",
  "refresh_token": "<REDACTED>",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_url": "/auth/refresh",
  "user": {
    "email": "demo1@ivy.homes"
  }
}
```

#### Incorrect password

Observed:

```text
401
{"detail":"invalid email or password"}
```

#### Nonexistent user

Observed:

```text
401
{"detail":"invalid email or password"}
```

### Result

**Partially confirmed with multiple documented discrepancies.**

Confirmed:

* `/auth/login` exists at the documented path.
* The email/password JSON request body is accepted.
* An API key is required.
* `token_type` is `Bearer`.
* Invalid credentials return HTTP 401.
* Wrong passwords and nonexistent users return the same generic authentication error.

Rejected:

* The API key is not accepted as the documented `api_key` query parameter.
* The running API requires the `X-API-Key` request header.
* The successful response uses `access_token`, not the documented `token` field.
* The observed access-token lifetime is 900 seconds, not the documented 86400 seconds.
* A refresh flow does exist.
* Successful login returns a `refresh_token`.
* Successful login returns `refresh_url: "/auth/refresh"`.
* The observed user object contains `email` but does not contain the documented `name` field.

### Impact

The frontend cannot implement authentication correctly from the supplied documentation alone.

It must:

* send the assigned API key using the `X-API-Key` request header;
* read `access_token` rather than `token`;
* handle a 15-minute access-token lifetime;
* account for the observed refresh-token mechanism if the session must remain usable beyond access-token expiry.

This is especially important because the assignment requires the application to remain functional at least thirty minutes after login.

The API-key transport, token schema, token lifetime, and refresh-flow behaviour are candidate `auth` discrepancies for the final findings set.




---

## H-003 — Authentication requirements for listing retrieval

### Source

`API_REFERENCE.md` states that:

1. Every request must carry the assigned API key using the `api_key` query parameter.
2. After login, the user token should be supplied as a Bearer token on subsequent requests.

H-002 showed that `/auth/login` instead requires the API key in the `X-API-Key` request header.

### Hypothesis

Determine which authentication components `/v1/listings` actually requires:

* API key
* user Bearer token
* both

Also determine whether the `X-API-Key` transport behaviour observed during login applies to a normal data endpoint.

### Test

Compare six requests to:

```http
GET /v1/listings
```

using:

1. No credentials.
2. Documented query-parameter API key only.
3. Observed `X-API-Key` header only.
4. Bearer token only.
5. Query-parameter API key plus Bearer token.
6. `X-API-Key` header plus Bearer token.

Only authentication behaviour is being investigated in this experiment.

### Evidence

#### No credentials

Observed:

```text
401
{"detail":"missing X-API-Key header"}
```

#### Documented query-parameter API key only

Observed:

```text
401
{"detail":"send your key in the X-API-Key request header, not as a query parameter"}
```

#### `X-API-Key` header only

Observed:

```text
401
{"detail":"missing bearer token - log in at POST /auth/login first"}
```

#### Bearer token only

Observed:

```text
401
{"detail":"missing X-API-Key header"}
```

#### Documented query-parameter API key + Bearer token

Observed:

```text
401
{"detail":"send your key in the X-API-Key request header, not as a query parameter"}
```

#### `X-API-Key` header + Bearer token

Observed:

```text
200
```

The successful response contained listing collection data.

### Result

**Confirmed with a documentation discrepancy.**

For `/v1/listings`:

* The assigned API key is required.
* A logged-in user Bearer token is also required.
* The API key must be sent in the `X-API-Key` request header.
* The documented `api_key` query parameter is explicitly rejected.
* Supplying only the API key is insufficient.
* Supplying only the Bearer token is insufficient.
* Supplying both `X-API-Key` and `Authorization: Bearer ...` succeeds.

The `X-API-Key` behaviour observed during login therefore also applies to a normal protected data endpoint.

### Impact

The frontend API client must attach both:

```http
X-API-Key: <assigned key>
Authorization: Bearer <access token>
```

to protected listing requests.

Using the API-key query-parameter mechanism described in `API_REFERENCE.md` would cause the application to fail authentication.

This strengthens the candidate `auth` finding that the documented API-key transport mechanism is incorrect.


---

## H-004 — Listings pagination contract

### Source

`API_REFERENCE.md` states that collection endpoints use:

* `page`
* `limit`

with:

* `page` defaulting to 1;
* `limit` defaulting to 20;
* maximum `limit` of 200.

The documented response shape is:

```json
{
  "total": 1240,
  "page": 1,
  "page_size": 20,
  "results": []
}
```

A successful `/v1/listings` request observed during H-003 instead returned pagination-related fields:

* `limit`
* `offset`
* `count`
* `total`
* `has_more`
* `results`

### Hypothesis

Determine the real pagination mechanism used by `/v1/listings`.

Specifically test:

1. The default pagination behaviour.
2. Whether the documented `page` parameter affects retrieval.
3. Whether an `offset` parameter controls retrieval.
4. The actual behaviour of `limit`.
5. Whether the documented maximum limit of 200 is enforced.
6. How the endpoint indicates that additional records remain.

### Test

Compare listing requests using:

* no pagination parameters;
* `page=1&limit=5`;
* `page=2&limit=5`;
* `offset=0&limit=5`;
* `offset=5&limit=5`;
* `offset=10&limit=5`;
* `limit=200`;
* `limit=201`;
* invalid negative offset.

Record:

* HTTP status;
* pagination metadata;
* result count;
* first and last listing IDs.

### Evidence

Observed default request:

```text
limit=20
offset=0
count=20
total=3201
has_more=true
```

Observed response pagination keys:

```text
limit
offset
count
total
has_more
results
```

#### Documented `page` parameter

`page=1&limit=5` returned:

```text
offset=0
count=5
first listing_id=100-6000047
last listing_id=MAG-6000434
```

`page=2&limit=5` returned the same:

```text
offset=0
count=5
first listing_id=100-6000047
last listing_id=MAG-6000434
```

The `page` parameter was accepted but did not advance pagination.

#### Observed `offset` parameter

`offset=0&limit=5` returned the first five records.

`offset=5&limit=5` returned a different next set of five records.

`offset=10&limit=5` returned the following set.

This confirms that `offset`, rather than `page`, controls pagination.

#### Limit behaviour

Requesting:

```text
limit=200
```

produced:

```text
limit=50
count=50
```

Requesting:

```text
limit=201
```

also produced:

```text
limit=50
count=50
```

Therefore the observed effective maximum limit is 50, not the documented 200.

#### Invalid offset

Requesting:

```text
offset=-1
```

returned HTTP 422 with validation indicating that offset must be greater than or equal to zero.

#### Full traversal

The collection was traversed using:

```text
offset = server-reported offset + server-reported count
```

until the API itself returned:

```text
has_more=false
```

Observed traversal summary:

```text
pages fetched: 70
records retrieved: 3500
unique listing IDs: 3500
repeated listing ID occurrences: 0
final offset: 3450
final count: 50
final has_more: false
```

Across every fetched page, the API reported:

```text
total=3201
```

However, 3500 distinct listing records were successfully retrieved before the API reported `has_more=false`.

### Result

**Confirmed with multiple documentation discrepancies.**

Observed pagination behaviour for `/v1/listings` is:

* pagination is offset-based;
* `offset` controls collection traversal;
* the documented `page` parameter is accepted but does not advance the collection;
* the response exposes `limit`, `offset`, `count`, `total`, and `has_more`;
* the documented `page` and `page_size` response fields were not observed;
* the observed effective maximum limit is 50, not 200;
* `has_more` correctly identified when traversal reached the end;
* the reported `total` value did not equal the number of retrievable listing records.

The API reported `total=3201` throughout traversal, while 3500 distinct records were retrieved before `has_more` became false.

### Impact

Client code must not implement pagination using the documented `page` parameter or terminate traversal using the reported `total`.

Reliable traversal for the observed listings endpoint should:

1. start at `offset=0`;
2. request up to 50 records;
3. advance using the server-reported `offset + count`;
4. continue while `has_more=true`;
5. stop only when `has_more=false`.

Using the documented pagination model would cause repeated first-page results and could prevent complete retrieval of the dataset.

The pagination mechanism, maximum limit, response metadata, ignored `page` parameter, and inaccurate `total` field are candidate `pagination` discrepancies for the final findings set.



---

## H-005 — Rentals collection contract

### Source

`API_REFERENCE.md` documents:

```http
GET /v1/rentals
```

as a paginated rental collection supporting `page`, `limit`, `locality`, `bhk`, `furnishing`, `sort_by`, and `order`.

The global pagination documentation claims collection endpoints use `page` and `limit`.

Previous investigation of `/v1/listings` showed that the running API instead used offset-based pagination.

### Hypothesis

Determine whether `/v1/rentals`:

1. exists at the documented path;
2. requires both the assigned API key and logged-in Bearer token;
3. uses the documented page-based pagination model or the observed offset-based model;
4. enforces the documented maximum limit;
5. returns the documented rental field names.

### Test

Compare requests using:

* no credentials;
* `X-API-Key` only;
* `X-API-Key` plus Bearer token;
* `page=2&limit=5`;
* `offset=5&limit=5`;
* `limit=200`.

Record:

* HTTP status;
* pagination metadata;
* returned record count;
* representative record field names.

Filters, sorting, units, and full dataset retrieval are intentionally outside the scope of this hypothesis.

### Evidence
#### Full rental traversal

The rental collection was traversed using the observed offset-based model until the API returned:

```text
has_more=false

#### Authentication

No credentials:

```text
401
{"detail":"missing X-API-Key header"}
```

`X-API-Key` only:

```text
401
{"detail":"missing bearer token - log in at POST /auth/login first"}
```

`X-API-Key` plus Bearer token:

```text
200
```

#### Default pagination

Observed:

```text
limit=20
offset=0
count=20
total=1207
has_more=true
```

Observed top-level response keys:

```text
limit
offset
count
total
has_more
results
```

#### Documented `page` parameter

`page=2&limit=5` returned:

```text
offset=0
count=5
first listing_id=R6000001
```

Therefore the documented `page` parameter did not advance retrieval.

#### Observed `offset` parameter

`offset=5&limit=5` returned:

```text
offset=5
count=5
first listing_id=R6000005
```

This confirms that `offset` controls rental pagination.

#### Limit behaviour

Requesting:

```text
limit=200
```

produced:

```text
limit=50
count=50
```

Therefore the observed effective maximum limit is 50.

#### Representative rental fields

Observed fields included:

```text
listing_id
locality
bedroom
furnishing
price
deposit
maintenance
carpet_area
super_builtup_area
is_live
posted_at
```

### Result

**Confirmed with the same broad pagination/authentication discrepancies previously observed on listings.**

For `/v1/rentals`:

* both `X-API-Key` and Bearer token are required;
* pagination is offset-based;
* the documented `page` parameter was accepted but did not advance retrieval;
* the response exposes `limit`, `offset`, `count`, `total`, and `has_more`;
* the observed effective maximum limit is 50, not the documented 200;
* representative rental fields were successfully returned.

### Impact

The frontend and analysis tooling must paginate rentals using `offset`, not the documented `page` parameter.

Rental retrieval should use the observed authentication model and should not assume the documented pagination schema is correct.

The full rental dataset must still be traversed to `has_more=false` before using it for Q5.




---

## H-006 — Projects collection contract

### Source

`API_REFERENCE.md` documents:

```http
GET /v1/projects
```

as a paginated project collection supporting `page`, `limit`, `locality`, `project_status`, `sort_by`, and `order`.

The global pagination documentation claims collection endpoints use `page` and `limit`.

Previous investigation of `/v1/listings` showed that the running API instead used offset-based pagination.

### Hypothesis

Determine whether `/v1/projects`:

1. exists at the documented path;
2. requires both the assigned API key and logged-in Bearer token;
3. uses the documented page-based pagination model or the observed offset-based model;
4. enforces the documented maximum limit;
5. returns the documented project field names.

### Test

Compare requests using:

* no credentials;
* `X-API-Key` only;
* `X-API-Key` plus Bearer token;
* `page=2&limit=5`;
* `offset=5&limit=5`;
* `limit=200`.

Record:

* HTTP status;
* pagination metadata;
* returned record count;
* representative record field names.

Filters, sorting, units, project/listing count consistency, and full dataset retrieval are intentionally outside the scope of this hypothesis.

### Evidence
#### Full project traversal

The project collection was traversed using the observed offset-based model until the API returned:

```text
has_more=false

#### Authentication

No credentials:

```text
401
{"detail":"missing X-API-Key header"}
```

`X-API-Key` only:

```text
401
{"detail":"missing bearer token - log in at POST /auth/login first"}
```

`X-API-Key` plus Bearer token:

```text
200
```

#### Default pagination

Observed:

```text
limit=20
offset=0
count=20
total=366
has_more=true
```

Observed top-level response keys:

```text
limit
offset
count
total
has_more
results
```

#### Documented `page` parameter

`page=2&limit=5` returned:

```text
offset=0
count=5
first project_id=P60001
```

Therefore the documented `page` parameter did not advance retrieval.

#### Observed `offset` parameter

`offset=5&limit=5` returned:

```text
offset=5
count=5
first project_id=P60006
```

This confirms that `offset` controls project pagination.

#### Limit behaviour

Requesting:

```text
limit=200
```

produced:

```text
limit=50
count=50
```

Therefore the observed effective maximum limit is 50.

#### Representative project fields

Observed fields included:

```text
project_id
locality
project_status
price_min
price_max
min_area_sqft
max_area_sqft
total_listings
```

One representative project returned:

```json
{
  "project_id": "P60001",
  "locality": "golf course road",
  "price_min": 1.66,
  "price_max": 4.54,
  "min_area_sqft": 1223,
  "max_area_sqft": 2718,
  "total_listings": 6,
  "project_status": "ready to move"
}
```

The observed project price values do not resemble the documented integer-rupee convention and require dedicated unit verification before use.

### Result

**Confirmed with pagination/authentication discrepancies and a new price-unit hypothesis.**

For `/v1/projects`:

* both `X-API-Key` and Bearer token are required;
* pagination is offset-based;
* the documented `page` parameter was accepted but did not advance retrieval;
* the observed effective maximum limit is 50;
* representative project fields were returned successfully.

The observed project price values require further investigation before they are interpreted as INR.

### Impact

The frontend and analysis tooling must paginate projects using `offset`.

Project prices must not be displayed or used for Q7 until their real unit has been established.

The full projects dataset must be traversed to `has_more=false` before computing project-based answers.



---

## H-007 — Assigned-locality rental matching and rent-value interpretation

### Source

The assignment asks for the sum of monthly rent across all retrievable rental records in the candidate's assigned locality.

The assigned locality supplied with the API credentials is:

`Sector 49`

`API_REFERENCE.md` documents rental `price` as monthly rent in Indian rupees.

### Hypothesis

Determine:

1. how the assigned locality is represented in the retrieved rental dataset;
2. whether case/whitespace normalization is sufficient to match it correctly;
3. whether rental `price` values are numerically plausible as monthly rent in INR before using them for Q5.

### Test

Using the complete retrievable rental snapshot:

- normalize the assigned locality and rental locality values using lowercase and whitespace normalization;
- count exact normalized matches;
- inspect similar locality strings;
- inspect the distribution of `price` values for matching rental records.

No final Q5 sum will be produced until the locality match and rent interpretation are validated.

### Evidence

The assigned locality supplied with the assignment credentials is:

```text
Sector 49
```

After lowercase and whitespace normalization:

```text
sector 49
```

The complete retrievable rental dataset contained:

```text
123
```

records whose normalized locality exactly matched `sector 49`.

No alternative similar locality representation was observed in the rental snapshot.

Price validation across those 123 matching records produced:

```text
matching rental records: 123
numeric price values: 123
missing prices: 0
non-numeric prices: 0
non-positive prices: 0
```

Observed price distribution:

```text
minimum price: 11600
maximum price: 81400
average price: 35186.99
```

These values are numerically consistent with plausible monthly residential rents in INR and do not contradict the documented interpretation of rental `price` as monthly rent.

Summing the `price` field across all 123 retrievable matching rental records produced:

```text
4328000
```

### Result

**Confirmed.**

The assigned locality `Sector 49` maps unambiguously to the rental locality value `sector 49` using lowercase and whitespace normalization.

Exactly 123 retrievable rental records matched the assigned locality.

Every matching rental record contained a numeric, positive `price` value.

No evidence was found contradicting the documented interpretation of rental `price` as monthly rent in INR.

The reproducible Q5 result is:

```text
total_monthly_rent = 4328000
```

### Impact

For Q5, locality matching should use normalized text rather than case-sensitive comparison.

The final answer must be derived from all 123 matching retrievable rental records:

```text
SUM(price) = 4328000
```

This investigation did not identify a rental-price unit discrepancy and should be preserved as an example of a documented behavior that was checked and found consistent with the retrieved data.






---

## H-008 — Project price units and Q7 interpretation

### Source

The assignment asks for:

`costliest_project`

defined as the project with the highest maximum price, returned as:

```json
{
  "project_id": "...",
  "price_max_inr": 0
}
```

`API_REFERENCE.md` documents project `price_min` and `price_max` as values in INR.

However, representative project records returned values such as:

```text
price_min=1.66
price_max=4.54
```

which do not resemble literal INR prices for residential projects.

### Hypothesis

Determine:

1. whether project prices use one consistent unit or multiple numeric scales;
2. whether the documented INR interpretation is incorrect;
3. what normalization rule, if any, converts project prices to INR;
4. whether the apparent cases where `price_min > price_max` are caused by mixed units rather than reversed field meanings;
5. which project has the highest normalized `price_max` for Q7.

### Test

Using all retrievable project records:

* validate `price_min` and `price_max`;
* inspect the complete value distribution;
* count apparent cases where `price_min > price_max`;
* rank projects by raw `price_max`;
* compare project prices with sale listing prices linked through `project_id` as a plausibility cross-check;
* test candidate lakh/crore conversions across the complete project dataset;
* verify whether normalization restores `price_min <= price_max`;
* do not finalize Q7 until a consistent normalization rule is supported by the data.

### Evidence

Full-dataset unit analysis covered all 400 retrievable projects and all 800 `price_min` / `price_max` values.

Two completely separated numeric clusters were observed:

```text
values < 10: 610
maximum value < 10: 5.83

values >= 10: 190
minimum value >= 10: 41.5
```

No project-price values occurred between `5.83` and `41.5`.

Cross-checking project records against INR-denominated sale listings linked by `project_id` indicated that:

```text
raw value < 10
→ crores

raw value >= 10
→ lakhs
```

The conversion tested across the complete project dataset was therefore:

```text
value < 10
→ value × 10,000,000 INR

value >= 10
→ value × 100,000 INR
```

Before normalization:

```text
price_min > price_max: 184 projects
```

After applying the mixed-unit normalization independently to both `price_min` and `price_max`:

```text
price_min_inr > price_max_inr: 0 projects
```

Thus the single observed conversion rule restored valid price-range ordering for every retrievable project.

The highest normalized `price_max` values were:

```text
P60060 → raw 5.83 → ₹58,300,000
P60227 → raw 5.66 → ₹56,600,000
P60355 → raw 5.56 → ₹55,600,000
P60231 → raw 5.32 → ₹53,200,000
P60280 → raw 5.26 → ₹52,600,000
```

The highest normalized maximum price belonged to:

```text
project_id: P60060
raw price_max: 5.83
price_max_inr: 58300000
```

### Result

**Confirmed mixed-unit project-price encoding.**

The observed project `price_min` and `price_max` fields are not consistently stored as INR despite the API reference documenting them as INR values.

The complete retrievable dataset supports two separate unit encodings:

```text
raw value < 10  → crore
raw value >= 10 → lakh
```

Applying those conversions independently to each price field resolves all 184 apparent raw range inversions.

The reproducible Q7 result is:

```json
{
  "project_id": "P60060",
  "price_max_inr": 58300000
}
```

### Impact

Project prices must be normalized before:

* displaying prices in the frontend;
* comparing project prices;
* identifying the costliest project;
* performing project-price analytics.

Using the raw values as literal INR would produce incorrect prices.

Using raw numeric ordering without unit normalization would also incorrectly rank projects such as those containing values around `80–99` above projects whose low-single-digit values represent crores.

This is a high-confidence candidate `units` discrepancy for the final findings set.



---

## H-009 — Active-listing completeness and Q3

### Source

The assignment defines Q3 `active_listings` as the number of retrievable
listing records where `is_live` is true.

`API_REFERENCE.md` states that:

> `GET /v1/listings` returns active sale listings only.

It further states that inactive, expired and withdrawn listings are excluded
server-side.

### Hypothesis

Determine whether every retrievable `/v1/listings` record is actually active,
as documented, and compute Q3 directly from the observed `is_live` field.

### Test

Using all retrievable listing records:

- verify whether every record contains `is_live`;
- verify that `is_live` values are booleans;
- count records where `is_live is True`;
- count records where `is_live is False`;
- preserve example inactive listing IDs if the endpoint returns any.



### Evidence

The complete retrievable `/v1/listings` snapshot contained:

```text
3500 records
```

Every record contained an `is_live` field.

Validation produced:

```text
Missing is_live: 0
Non-boolean is_live: 0
```

Observed boolean distribution:

```text
is_live = true: 2792
is_live = false: 708
```

Therefore 708 retrievable listing records were inactive even though the API reference states that `/v1/listings` returns active sale listings only.

Example inactive listing IDs:

```text
SQU-6001937
DWE-6002796
MAG-6000794
SQU-6003155
SQU-6000987
SQU-6000737
DWE-6002177
DWE-6002689
100-6001196
MAG-6001288
100-6001939
100-6003034
ZER-6000180
ZER-6000474
SQU-6002061
100-6002415
SQU-6001398
ZER-6001587
100-6000309
100-6002885
```

The Q3 count derived directly from the observed boolean field is:

```text
active_listings = 2792
```

### Result

**Confirmed documentation discrepancy.**

The running `/v1/listings` endpoint does not return active listings only.

Out of 3500 retrievable listing records:

```text
2792 were active
708 were inactive
```

The reproducible Q3 result is:

```text
active_listings = 2792
```

### Impact

Application and analysis code must not assume that every record returned by `/v1/listings` is active.

Any feature requiring active listings must explicitly filter:

```text
is_live == true
```

The inactive records are evidence that the documented server-side exclusion of inactive listings is not reliable.

This is a high-confidence candidate `completeness` discrepancy for the final findings set, supported by record-level evidence IDs.


---

## H-010 — Listing timestamps and fixed seven-day window for Q8

### Source

The assignment defines Q8 `listings_last_7_days` using the fixed reference:

`2026-09-10T00:00:00+05:30`

and the interval:

`[REFERENCE - 7 days, REFERENCE)`

Therefore the required interval is:

`2026-09-03T00:00:00+05:30`
inclusive

through

`2026-09-10T00:00:00+05:30`
exclusive.

`API_REFERENCE.md` states that timestamps are returned in UTC `Z` format.

### Hypothesis

Determine:

1. whether every retrievable listing contains `posted_at`;
2. whether all timestamps are parseable and timezone-aware;
3. which timestamp formats are actually used;
4. how many retrievable listing records fall inside the assignment's fixed seven-day interval.

### Test

Using all retrievable listing records:

- validate presence and type of `posted_at`;
- parse ISO-8601 timestamps while preserving timezone information;
- inspect observed timestamp representations;
- calculate the earliest and latest timestamps;
- classify every listing as before the window, inside the window, or at/after the reference;
- count records satisfying:

`WINDOW_START <= posted_at < REFERENCE`

### Evidence
Initial timestamp validation across all 3500 retrievable listings showed:

```text
Missing posted_at: 0
Non-string posted_at: 0
Naive/no-timezone timestamps: 3500
Timezone-aware timestamps: 0

### Evidence

All 3500 retrievable listing records contained `posted_at`.

Observed validation:

```text
Successfully parsed naive timestamps: 3500
Parse failures: 0
```

Every `posted_at` value omitted timezone information.

Representative values:

```text
2026-08-19T10:52:00
2026-03-12T16:31:00
2026-09-09T23:01:00
```

This contradicts the API reference convention that timestamps are returned as UTC ISO-8601 values with a `Z` suffix.

The assignment fixes the Q8 interval in IST:

```text
2026-09-03T00:00:00+05:30
<= posted_at <
2026-09-10T00:00:00+05:30
```

Because the returned timestamps were timezone-naive, two interpretations were tested.

Assuming the timestamps represent Asia/Kolkata local time:

```text
Before window: 3365
Inside Q8 window: 129
At/after reference: 6
```

Assuming the timestamps represent UTC:

```text
Before window: 3363
Inside Q8 window: 112
At/after reference: 25
```

Therefore the interpretation affects the Q8 answer.

The running `/health` endpoint identifies the service timezone as:

```text
Asia/Kolkata
```

and returns its server/reference times using the `+05:30` offset.

The assignment also explicitly states that the Q8 interval is in IST.

The runtime service timezone and assignment reference therefore support interpreting the naive listing timestamps as Asia/Kolkata local time.

Under that interpretation:

```text
listings_last_7_days = 129
```

### Result

**Confirmed timestamp-format discrepancy.**

The running listings API does not return `posted_at` timestamps in the documented UTC-`Z` representation.

Instead, all 3500 retrievable listing records returned timezone-naive timestamps.

For Q8, the naive timestamps were interpreted in the runtime service timezone, Asia/Kolkata, consistent with the assignment's IST reference interval.

The reproducible Q8 result is:

```text
listings_last_7_days = 129
```

### Impact

Client and analysis code must not assume that `posted_at` contains an explicit UTC timezone.

For the observed dataset, timestamps must be interpreted using the service's Asia/Kolkata timezone before comparisons against the assignment's IST reference.

This is a high-confidence candidate `timestamps` finding.


---

## H-011 — Documented sale-listing detail endpoint

### Source

`API_REFERENCE.md` documents:

```http
GET /v1/listing/{listing_id}
```

and states that it returns a single listing using the same object schema as the listings collection.

### Hypothesis

Determine whether retrievable listing records can also be fetched through the documented single-listing endpoint.

### Test

Eight `listing_id` values known to exist in the complete `/v1/listings` collection were requested through:

```http
GET /v1/listing/{listing_id}
```

The tested IDs included records close to the Q8 timestamp boundaries.

### Evidence

All eight requests returned:

```text
HTTP 404
{"detail":"Not Found"}
```

Tested existing listing IDs included:

```text
DWE-6000457
DWE-6001897
100-6001004
SQU-6002462
DWE-6001514
100-6002912
MAG-6000954
DWE-6001325
```

Each of these IDs was present in the successfully retrieved `/v1/listings` collection.

### Result

**Confirmed discrepancy.**

The documented sale-listing detail path did not return records known to exist in the listings collection.

### Impact

The frontend cannot rely on the documented single-listing endpoint for its required listing-detail page.

The application must build detail pages from listing data obtained through the working collection endpoint unless another functioning detail route is discovered.

This is a high-confidence candidate `missing_endpoint` finding.


---

## H-012 — Impossible listing records and Q4

### Source

The assignment defines `corrupt_listing_ids` as:

> A small number of listing records describe something that cannot exist.

The answer must contain their sorted `listing_id` values.

Because Q4 is evaluated on both correct discoveries and false positives,
unusual values must not automatically be treated as corrupt.

### Hypothesis

Determine whether a small subset of retrievable sale listings violates hard
physical or logical constraints.

### Test

Using all retrievable listing records, test hard invariants including:

- price must be positive;
- carpet area must be positive;
- super-built-up area, when present, must be positive;
- bedroom, bathroom, balcony and parking counts cannot be negative;
- latitude must be within `[-90, 90]`;
- longitude must be within `[-180, 180]`;
- for ordinary non-negative floor values, `floor` cannot exceed
  `total_floors`.

Separately record unusual but not necessarily impossible values, such as:

- carpet area larger than super-built-up area;
- very large bedroom/bathroom counts;
- unusually large areas;
- extremely high prices.

Only records supported by hard evidence will be considered for Q4.

### Evidence

All 3500 retrievable listings were scanned for hard physical and logical
violations.

No required-field or numeric-type problems were found.

Three isolated classes of impossible records were identified.

#### Negative sale price

Six listings had a negative `price` value:

```text id="x1wmj5"
MAG-6000631
DWE-6002663
100-6001461
ZER-6000669
SQU-6003044
100-6002071
```

Representative values included:

```text id="dthdmr"
100-6001461 → price = -17880000
100-6002071 → price = -12340000
MAG-6000631 → price = -8550000
```

A negative sale price is impossible under the documented sale-price field
semantics.

#### Floor exceeds total building floors

Six listings had:

```text id="t7847t"
floor > total_floors
```

Affected IDs:

```text id="akb8wf"
100-6001968
100-6000323
DWE-6001015
SQU-6001477
MAG-6000453
DWE-6002846
```

Examples:

```text id="am7p5x"
100-6001968 → floor 26, total_floors 11
DWE-6001015 → floor 28, total_floors 17
MAG-6000453 → floor 12, total_floors 5
DWE-6002846 → floor 15, total_floors 8
```

These records describe floors that cannot exist within their stated
buildings.

#### Carpet area exceeds super-built-up area

Six listings had:

```text id="8zvsvo"
carpet_area > super_built_up_area
```

Affected IDs:

```text id="f60ba9"
MAG-6000527
100-6000338
ZER-6000468
MAG-6001135
DWE-6000010
MAG-6002834
```

Examples:

```text id="szxcyc"
100-6000338 → 1739 > 1304
DWE-6000010 → 2668 > 2149
MAG-6001135 → 2202 > 1607
ZER-6000468 → 1562 > 1167
```

These values are inconsistent with the semantic relationship between carpet
area and super-built-up area.

Across the three categories there were:

```text id="1byrw4"
18 unique corrupt listing IDs
```

### Result

**Confirmed.**

The complete retrievable listings dataset contains 18 records that violate
hard physical or logical constraints.

The reproducible Q4 result, sorted by `listing_id`, is:

```text id="h2s90e"
100-6000323
100-6000338
100-6001461
100-6001968
100-6002071
DWE-6000010
DWE-6001015
DWE-6002663
DWE-6002846
MAG-6000453
MAG-6000527
MAG-6000631
MAG-6001135
MAG-6002834
SQU-6001477
SQU-6003044
ZER-6000468
ZER-6000669
```

### Impact

These records must be excluded wherever the assignment explicitly requires
corrupt records to be removed, including Q6.

They should also not be trusted for normal user-facing analytics.

This is a record-level data-quality issue and the affected IDs should be
preserved as evidence.
