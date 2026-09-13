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



---

## H-013 — Duplicate property representations and Q2

### Source

The assignment defines `unique_properties` as:

> Among the retrievable listing records, genuine or not, how many distinct
> properties do they describe? A property described by several records counts
> once.

Therefore `listing_id` uniqueness cannot be used as a proxy for physical
property uniqueness.

The listing schema exposes physical attributes including locality,
apartment/building name, property type, bedrooms, bathrooms, floor,
total floors, carpet area, super-built-up area and coordinates.

### Hypothesis

Determine whether multiple listing records represent the same physical
property and identify a reproducible property-identity rule.

### Test

Using all 3500 retrievable sale listings:

1. measure exact duplication of a strict physical signature consisting of:
   - locality;
   - apartment name;
   - property type;
   - bedroom/bathroom/balcony counts;
   - floor and total floors;
   - carpet area;
   - super-built-up area;
   - latitude and longitude;

2. repeat the analysis without apartment name to detect naming variation;

3. measure coordinate reuse independently;

4. inspect duplicate groups across websites and compare fields that are
   expected to vary between advertisements, including price, seller/contact,
   source and listing URL.

No final property count will be produced until the observed duplicate pattern
is inspected.

### Evidence

All 3500 retrievable listing records were analyzed for multiple advertisements of
the same physical property.

Exact equality across all physical fields was too strict:

```text
strict physical signatures: 3500
exact duplicate groups: 0
```

Coordinate reuse alone was also not sufficient:

```text
repeated-coordinate groups: 245
records in repeated-coordinate groups: 519
```

Inspection showed that identical coordinates generally represented a building
or project location rather than an individual unit. Records sharing coordinates
frequently differed in BHK, floor, area and price.

Before property matching, a confirmed mixed-area-unit issue in 323
`magichomes` records was normalized from square metres to square feet.

After normalization, near-duplicate analysis was performed within the same
normalized locality and apartment/building name.

The final conservative property-identity rule required:

* same normalized locality;
* same normalized apartment/building name;
* same property type;
* same bedroom count;
* same bathroom count;
* same balcony count;
* same floor;
* same total floors;
* normalized carpet area within 5%;
* normalized super-built-up area within 5%;
* coordinates within 150 metres.

Two independently designed conservative matching rules initially found the
same 253 candidate pairs.

Independent validation found:

```text
property-type mismatches: 0
balcony mismatches: 0
pairs within 150 metres: 252
geographic outliers: 1
```

The only geographic outlier was:

```text
DWE-6000679
ZER-6002666
```

Although their structured attributes were similar, their coordinates were
36,837.79 metres apart. Since one physical property cannot exist at two
locations separated by approximately 36.8 km, this pair was rejected as a
false match.

The final duplicate graph therefore contained 252 valid duplicate edges.

After collapsing connected components:

```text
valid duplicate property groups: 240

component sizes:
size 2: 234 groups
size 3: 6 groups

duplicate listing records collapsed: 246
```

Therefore:

```text
3500 retrievable listing records
- 246 duplicate representations
= 3254 distinct physical properties
```

### Result

**Confirmed.**

The reproducible Q2 answer is:

```text
unique_properties = 3254
```

The count includes genuine and non-genuine listings because Q2 asks only how
many distinct physical properties the retrievable records describe.

### Impact

Listing records cannot be treated as one-to-one with physical properties.

Analytics or UI features that operate at the property level should normalize
the confirmed mixed area units and apply property-resolution logic before
counting properties.

The duplicate groups also provide useful structure for later investigation of
cross-site inconsistencies and suspicious/fake listings.





---

## H-014 — Mixed listing area units

### Source

The listing schema describes `carpet_area` and `super_built_up_area`
as property-area fields.

The assignment later requires Q6 to calculate rupees per square foot,
so the unit of `carpet_area` directly affects a scored answer.

### Observation

Area profiling across all 3500 retrievable listings showed a
source-specific low-value cluster.

For `carpet_area < 300`:

- magichomes: 323 records
- all other sources combined: 1 record

For magichomes `super_built_up_area`, exactly 323 records were below 400.

Representative magichomes records included values such as:

- 36 carpet / 45 super-built-up for a 1 BHK
- 82 carpet / 113 super-built-up for a 2 BHK
- 149 carpet / 206 super-built-up for a 4 BHK

Interpreting those values as square metres and converting them to square feet
produces physically plausible residential areas.

### Hypothesis

A subset of magichomes listings returns both area fields in square metres,
while the remaining listing records use square feet.

A candidate unit split is:

- magichomes records with `carpet_area < 300` and
  `super_built_up_area < 400` → square metres;
- remaining records → square feet.

### Test

Verify:

1. whether the low-carpet and low-super-built-up sets are exactly the same;
2. whether there is a clear numerical boundary between the two populations;
3. whether converting the candidate records by
   `1 sqm = 10.7639104167 sqft` makes BHK-specific area distributions align
   with the other listing sources;
4. whether normalized 2-BHK price-per-square-foot values become comparable
   with the other websites.

### Evidence

The suspected low-area population was isolated to `magichomes`.

For `magichomes`:

```text
carpet_area < 300: 323
super_built_up_area < 400: 323
intersection: 323
carpet-only records: 0
super-only records: 0
```

Therefore the two independently observed low-area conditions identify exactly the
same 323 records.

The two populations also have clear numerical separation.

For carpet area:

```text
largest candidate value: 221
smallest non-candidate value: 334
```

For super-built-up area:

```text
largest candidate value: 271
smallest non-candidate value: 429
```

The candidate values were converted using:

```text
1 square metre = 10.7639104167 square feet
```

After conversion, BHK-specific median carpet areas closely matched the other
four listing sources:

```text
1 BHK: 2.58% difference
2 BHK: 0.79% difference
3 BHK: 0.25% difference
4 BHK: 0.51% difference
5 BHK: 0.34% difference
```

The normalized 2-BHK price-per-square-foot medians were also comparable:

```text
100acres:   14321.49
dwelling:   13652.54
magichomes: 14365.36
squarelane: 14765.30
zerobroker: 14322.49
```

Without conversion, the low-area `magichomes` records would produce implausible
residential areas and artificially inflated price-per-square-foot values.

After normalizing the confirmed mixed `magichomes` area units, a
within-building near-duplicate search was performed.

The dataset contained:

```text
buildings with multiple listings: 872
within-building listing pairs: 2386
cross-site pairs: 1932

### Result

**Confirmed unit discrepancy.**

A subset of 323 `magichomes` sale listings returns `carpet_area` and
`super_built_up_area` in square metres even though the remaining sale listings
use square feet.

The reproducible normalization rule is:

```text
website == "magichomes"
AND carpet_area < 300
AND super_built_up_area < 400
```

For records satisfying that rule, convert both area values to square feet using:

```text
area_sqft = raw_area * 10.7639104167
```

All other observed sale-listing area values remain in square feet.

### Impact

Area values must be normalized before:

* property deduplication for Q2;
* price-per-square-foot calculation for Q6;
* area comparisons or analytics;
* displaying these records consistently in the application.

Failing to normalize these records would make 323 properties appear roughly
10.76 times smaller than their actual square-foot areas.

This is a high-confidence candidate `units` finding.



---

## H-015 — Fake enquiry-generation listings and Q9

### Source

The assignment states that some sale listings are deliberately fake and exist
to generate enquiries.

Q9 requires the sorted listing IDs of those fake records.

Because Q9 is evaluated on both discoveries and false positives, unusual or
cheap listings must not automatically be labelled fake.

### Hypothesis

Fake enquiry-generation listings may exhibit one or more reproducible signals,
including:

- an unusually low advertised price compared with independent advertisements
  of the same physical property;
- abnormal normalized price per square foot;
- suspicious seller/contact reuse across many otherwise unrelated properties;
- a source-specific pattern among bait-priced listings.

### Test

Using all retrievable sale listings:

1. reuse the confirmed Q2 physical-property resolution logic;
2. compare advertised prices where the same physical property is listed more
   than once;
3. rank the largest same-property price disagreements;
4. inspect normalized price-per-square-foot outliers;
5. profile seller/contact reuse.

No listing will be classified as fake until a distinct repeated pattern is
observed.

### Evidence

Fraud analysis was performed across all 3500 retrievable sale listings.

Seller/contact reuse was initially investigated, but reuse was found to be
normal in the dataset:

```text
unique contacts: 593
contacts appearing on more than one listing: 582
```

A broad relative-underpricing test also produced 226 listings priced below 65%
of the median for comparable locality/BHK/property-type records.

Those listings formed a continuous price distribution and many otherwise normal
contacts appeared repeatedly within it. Therefore ordinary underpricing and
contact reuse were not treated as sufficient evidence of fake listings.

A separate and sharply isolated price population was found.

Exactly six positive-price sale records had `price < 100000`:

```text
100-6000678    5030
MAG-6002472    8010
100-6000578   14620
SQU-6000395   17010
MAG-6002941   17250
100-6001599   26260
```

There were:

```text
6 records below 100000
0 records from 100000 through 999999
1 record from 1000000 through 2999999
```

The next positive sale price after the six-record cluster was:

```text
ZER-6001884 = 2730000
```

The adjacent jump from the highest ultra-low price to the next record was:

```text
26260 -> 2730000
approximately 103.96x
```

For five candidates where comparable peer medians were available, their
price-to-peer-median ratios were approximately:

```text
0.000629
0.000730
0.000747
0.000762
0.001195
```

The next-lowest non-candidate ratio was:

```text
0.3459
```

This created a further approximately 289x separation between the isolated
ultra-low cluster and the broader underpriced population.

The six records were distributed across multiple listing sources:

```text
100acres: 3
magichomes: 2
squarelane: 1
```

Most were also marked verified, demonstrating that `is_verified` cannot be
relied upon as a fake-listing indicator.

The associated contacts otherwise published ordinary market-priced listings,
so fake classification was kept at the individual record level rather than
expanded to every listing from those contacts.

### Result

**Confirmed high-confidence fake/bait listing cluster.**

The Q9 result is:

```text
100-6000578
100-6000678
100-6001599
MAG-6002472
MAG-6002941
SQU-6000395
```

The reproducible classification rule is the isolated positive-price cluster:

```text
0 < price < 100000
```

This threshold is data-driven rather than arbitrary because no other positive
sale listings occur anywhere near this range and the next record is priced at
2730000.

### Impact

These six records must be excluded where the assignment explicitly requires
fake listings to be excluded, particularly Q6.

The application should also avoid presenting these bait prices as ordinary
property sale totals without appropriate data-quality handling.

This is a high-confidence `fraud` finding.




---

## H-016 — Live 2BHK average price per square foot

### Requirement

Q6 asks for the arithmetic mean of the individual price-per-square-foot values
for qualifying live 2BHK sale listings.

The qualifying population must:

* have `is_live == true`;
* have `bedroom == 2`;
* exclude all Q4 corrupt listing records;
* exclude all Q9 fake enquiry-generation listings.

The price-per-square-foot calculation must use normalized carpet area.

### Important dependency

A previous investigation confirmed that 323 `magichomes` sale listings expose
both area fields in square metres rather than square feet.

Those records must therefore be converted using:

```text
sqft = sqm × 10.7639104167
```

before calculating price per square foot.

### Calculation

For every qualifying listing:

```text
listing_ppsf = price / normalized_carpet_area_sqft
```

Then:

```text
Q6 = arithmetic mean of all listing_ppsf values
```

This is intentionally different from:

```text
sum(price) / sum(carpet_area)
```
### Evidence

The complete retrievable listing dataset contained:

```text
all 2BHK records: 1150
live 2BHK records: 934
```

The Q6 population was then cleaned using the assignment-required exclusion
sets:

```text
live Q4 corrupt records excluded: 6
live Q9 fake records excluded: 2
eligible records after exclusions: 926
```

The two exclusion sets did not overlap within this population because:

```text
934 - 6 - 2 = 926
```

Validation of the remaining records found:

```text
invalid/non-positive prices: 0
invalid/non-positive carpet areas: 0
```

Among the qualifying records, 84 `magichomes` listings matched the previously
confirmed square-metre area pattern and were converted to square feet before
the PPSF calculation.

The resulting normalized price-per-square-foot distribution was:

```text
minimum:          4719.90
5th percentile:   8943.30
median:           14243.85
95th percentile:  19702.70
maximum:          21685.91
```

The qualifying records were distributed across all listing sources:

```text
100acres:    197
dwelling:    188
magichomes:  190
squarelane:  180
zerobroker:  171
```

For each qualifying listing:

```text
listing_ppsf = price / normalized_carpet_area_sqft
```

The final value was computed as the arithmetic mean of the 926 individual PPSF
values.

### Result

**Confirmed.**

```text
avg_price_per_sqft_2bhk = 14230.56
```

This is the arithmetic mean of individual listing-level PPSF values, not
`sum(price) / sum(area)`.

### Impact

Any UI or analytics feature displaying sale price per square foot must use the
same area normalization logic to avoid overstating PPSF for affected
`magichomes` records.

Q4 corrupt listings and Q9 fake listings must also be excluded from this
specific assignment metric.



---

## H-017 — Project `total_listings` consistency and Q10

### Documentation claim

The project API exposes `total_listings` and claims that it is the number of
listings currently available for that project and that it always agrees with
the listings endpoint when filtered by `project_id`.

Q10 explicitly asks how many projects report an incorrect listing count.

### Hypothesis

Some project `total_listings` values may disagree with the actual retrievable
sale-listing records associated with that project's `project_id`.

There is also an ambiguity around whether "currently available" means:

1. every retrievable listing record associated with the project; or
2. only associated records having `is_live == true`.

Both interpretations will be tested before Q10 is finalized.

### Test

Using the complete locally retrieved datasets:

1. group all sale listings by `project_id`;
2. separately group live sale listings by `project_id`;
3. compare every project's declared `total_listings` with both counts;
4. inspect mismatch direction and magnitude;
5. verify whether any listing references a project ID absent from the projects
   endpoint;
6. separately test the documented `/v1/listings?project_id=...` behavior before
   relying upon that filter.

### Evidence

### Evidence

The complete local snapshots contained:

```text
sale listing records: 3500
project records: 400
```

Every listing carrying a `project_id` referenced an existing record from the
projects endpoint:

```text
distinct project IDs used by listings: 396
project IDs absent from projects dataset: 0
```

Two interpretations of project `total_listings` were compared.

Against every associated retrievable listing record:

```text
projects matching declared count: 105
projects with mismatched count: 295
```

Against only associated records having `is_live == true`:

```text
projects matching declared count: 294
projects with mismatched count: 106
```

The large improvement from 105 matches to 294 matches strongly indicates that
`total_listings` represents currently available/live listings rather than all
historical listing records.

This is also visible in individual projects. For example:

```text
P60001
declared:    6
all records: 7
live:        6

P60002
declared:    3
all records: 7
live:        3

P60004
declared:    8
all records: 9
live:        8
```

The aggregate values were:

```text
sum of project total_listings: 2031
associated listing records:    2249
associated live records:       1809
```

Although most project counts agree with live records, 106 of the 400 projects
still disagree.

The documented `project_id` filter will be tested separately before the final
Q10 value is locked.


### Evidence

The complete local snapshots contained:

```text
sale listing records: 3500
project records: 400
```

Every non-null listing `project_id` referenced an existing project:

```text
distinct project IDs used by listings: 396
project IDs absent from projects dataset: 0
```

Project `total_listings` was compared against two possible interpretations.

Against every associated retrievable listing record:

```text
matching projects: 105
mismatching projects: 295
```

Against associated records having `is_live == true`:

```text
matching projects: 294
mismatching projects: 106
```

This strongly establishes that `total_listings` is intended to represent
currently available/live listings.

Examples where the declared value correctly matches the live population but
not the complete historical population include:

```text
P60001
declared: 6
all records: 7
live records: 6

P60002
declared: 3
all records: 7
live records: 3

P60004
declared: 8
all records: 9
live records: 8
```

However, 106 projects still disagree with their actual live listing count.

Examples include:

```text
P60006  declared 4   live 10
P60011  declared 0   live 9
P60012  declared 0   live 5
P60017  declared 9   live 2
P60021  declared 3   live 6
P60022  declared 7   live 5
P60027  declared 16  live 7
P60030  declared 20  live 6
P60035  declared 0   live 2
P60039  declared 8   live 3
P60040  declared 21  live 7
P60042  declared 0   live 4
P60046  declared 10  live 8
P60048  declared 2   live 7
P60050  declared 0   live 4
P60057  declared 5   live 3
P60063  declared 15  live 4
P60073  declared 0   live 3
P60074  declared 0   live 6
P60075  declared 1   live 6
```

The documented cross-check endpoint was also tested.

Requests such as:

```text
GET /v1/listings?project_id=P60001
GET /v1/listings?project_id=P60006
GET /v1/listings?project_id=P60022
```

did not filter by project.

Each request returned the same general listing page with unrelated project IDs,
a response total of 3201, and records whose `project_id` did not match the
requested projec


### Evidence

The complete local snapshots contained:

```text
sale listing records: 3500
project records: 400
```

Every non-null listing `project_id` referenced an existing project:

```text
distinct project IDs used by listings: 396
project IDs absent from projects dataset: 0
```

Project `total_listings` was compared against two possible interpretations.

Against every associated retrievable listing record:

```text
matching projects: 105
mismatching projects: 295
```

Against associated records having `is_live == true`:

```text
matching projects: 294
mismatching projects: 106
```

This strongly establishes that `total_listings` is intended to represent
currently available/live listings.

Examples where the declared value correctly matches the live population but
not the complete historical population include:

```text
P60001
declared: 6
all records: 7
live records: 6

P60002
declared: 3
all records: 7
live records: 3

P60004
declared: 8
all records: 9
live records: 8
```

However, 106 projects still disagree with their actual live listing count.

Examples include:

```text
P60006  declared 4   live 10
P60011  declared 0   live 9
P60012  declared 0   live 5
P60017  declared 9   live 2
P60021  declared 3   live 6
P60022  declared 7   live 5
P60027  declared 16  live 7
P60030  declared 20  live 6
P60035  declared 0   live 2
P60039  declared 8   live 3
P60040  declared 21  live 7
P60042  declared 0   live 4
P60046  declared 10  live 8
P60048  declared 2   live 7
P60050  declared 0   live 4
P60057  declared 5   live 3
P60063  declared 15  live 4
P60073  declared 0   live 3
P60074  declared 0   live 6
P60075  declared 1   live 6
```

The documented cross-check endpoint was also tested.

Requests such as:

```text
GET /v1/listings?project_id=P60001
GET /v1/listings?project_id=P60006
GET /v1/listings?project_id=P60022
```

did not filter by project.

Each request returned the same general listing page with unrelated project IDs,
a response total of 3201, and records whose `project_id` did not match the
requested project.

Therefore the broken server-side filter cannot be used as the source of truth.
The count was reconstructed from the complete unfiltered listing dataset
instead.



### Result

**Confirmed.**

```text
projects_with_wrong_listing_count = 106
```

A project's count is considered correct when:

```text
project.total_listings
==
number of retrievable listing records where:
    listing.project_id == project.project_id
    and listing.is_live == true
```

### Impact

Project pages cannot safely trust `total_listings` for all projects.

For accurate application behavior, project listing counts should be derived
from the complete retrieved listing dataset where necessary rather than relying
on the broken `project_id` filter.




---

## H-018 — `/v1/listings` ignores `project_id`

### Documentation claim

The projects documentation states that project `total_listings` always agrees
with:

```text
GET /v1/listings?project_id=...
```

This implies that the listing endpoint supports filtering records by project.

### Test

Requests were made for multiple different project IDs, including projects whose
declared counts were correct and projects whose counts were incorrect.

Examples:

```text
project_id=P60001
project_id=P60002
project_id=P60006
project_id=P60011
project_id=P60022
```

### Evidence

The responses did not change according to the requested project.

For example, requesting:

```text
GET /v1/listings?project_id=P60001
```

returned 50 records containing many unrelated project IDs and records with a
null `project_id`.

The response reported:

```text
count: 50
total: 3201
wrong project records on page: 50
filter honored: false
```

The same behavior was reproduced for all sampled project IDs.

### Result

**Confirmed documentation discrepancy.**

`project_id` is ignored by `/v1/listings`.

### Impact

Clients cannot retrieve a project's listings by trusting the documented
project-specific query.

Project/listing relationships must instead be reconstructed client-side from
the complete listing dataset.

Candidate submission finding category:

```text
filters
```



---

## H-019 — Listing filters and sorting

### Documentation claim

`GET /v1/listings` documents the following filters:

```text
locality
bhk
property_type
min_price
max_price
furnishing
```

and the following sorting contract:

```text
sort_by = price | carpet_area | posted_at | bedroom
order   = asc | desc
```

### Filter verification

Each documented filter was tested using values present in the complete
3,500-record listing snapshot.

Every returned record satisfied the requested predicate.

Examples:

```text
locality=sector 65
returned mismatches: 0

locality=dwarka expressway
returned mismatches: 0

bhk=3
returned mismatches: 0

bhk=2
returned mismatches: 0

property_type=apartment
returned mismatches: 0

furnishing=fully-furnished
returned mismatches: 0

min_price=12420000
returned mismatches: 0

max_price=17700000
returned mismatches: 0
```

A combined request was also tested:

```text
locality=sector 65
bhk=3
furnishing=fully-furnished
```

and every returned record satisfied all three conditions.

Therefore the documented listing filters themselves are working.

### Filtered `total` metadata

The API-reported `total` values did not agree with the complete local snapshot.

For example:

```text
sector 65
snapshot matches: 385
API total:        352

bhk=3
snapshot matches: 1297
API total:        1186

apartment
snapshot matches: 2592
API total:        2371
```

This is consistent with the already-confirmed global collection-count defect
where the unfiltered endpoint reports `total=3201` although 3500 records are
retrievable.

It is therefore treated as part of the pagination/count discrepancy rather than
as multiple separate filter findings.

### Sorting verification

#### Price

Ascending price sorting works.

The beginning of the ascending response was:

```text
-17880000
-17660000
-13650000
-12640000
-12340000
-8550000
5030
8010
14620
17010
```

However, requesting:

```text
sort_by=price&order=desc
```

returned the exact same listing IDs in the exact same order.

Therefore descending order is ignored.

#### Bedroom

Ascending bedroom sorting works.

Both:

```text
sort_by=bedroom&order=asc
sort_by=bedroom&order=desc
```

returned the same listing IDs.

The first page happened to consist entirely of zero-bedroom records, which can
make a simple monotonicity test incorrectly appear valid for both directions.

Comparing the IDs establishes that descending order is ignored.

#### Carpet area

`sort_by=carpet_area` does not correctly order the returned records.

The ascending response failed monotonicity using both:

1. the raw `carpet_area` values; and
2. the independently confirmed normalized square-foot areas for affected
   `magichomes` records.

The descending request returned the same listing IDs as the ascending request.

Therefore this is not explained by the mixed-area-unit issue alone.

#### Posted timestamp

`sort_by=posted_at&order=asc` produced records whose calendar dates were
non-decreasing, but the complete timestamps were not.

For example, records from the same day appeared in this order:

```text
2026-01-13T12:10:00
2026-01-13T12:34:00
2026-01-13T12:36:00
2026-01-13T17:55:00
2026-01-13T04:25:00
2026-01-13T07:28:00
...
```

Therefore the server appears to sort by the date component while ignoring the
time-of-day component.

The descending request again returned the same listing IDs as ascending.

### Results

Confirmed working:

```text
locality filter
bhk filter
property_type filter
min_price filter
max_price filter
furnishing filter
price ascending sort
bedroom ascending sort
```

Confirmed discrepancies:

```text
1. `order=desc` is ignored.
2. `sort_by=carpet_area` does not correctly sort by carpet area.
3. `sort_by=posted_at` does not sort by the complete timestamp.
```

### Impact

The frontend must not rely on server-side descending ordering.

For predictable UI behavior, records should be sorted client-side after the
required records have been retrieved, particularly for carpet area and posting
time.

The documented business filters can still be used server-side, although the
reported `total` cannot be trusted for determining pagination completeness.



---

## H-020 — Detail and related endpoint contract

### Documentation claims

The API reference documents:

```text
GET /v1/listing/{listing_id}
GET /v1/listings/{listing_id}/similar
GET /v1/rentals/{listing_id}
GET /v1/projects/{project_id}
```

No plural listing-detail endpoint is documented.

### Listing detail

Three known-valid listing IDs were tested:

```text
100-6000047
SQU-6001039
SQU-6001481
```

For every valid listing, the documented path:

```text
/v1/listing/{id}
```

returned:

```text
HTTP 404
{"detail": "Not Found"}
```

The plural form:

```text
/v1/listings/{id}
```

was then tested for the same IDs.

Every request returned `HTTP 200` and the correct requested listing object.

For example:

```text
/v1/listings/100-6000047
```

returned:

```text
listing_id = 100-6000047
```

Therefore the working listing-detail endpoint is:

```text
GET /v1/listings/{id}
```

and it is missing from the documentation.

### Similar listings

The documented endpoint:

```text
GET /v1/listings/{id}/similar
```

was tested using the same three known-valid listing IDs.

All three returned:

```text
HTTP 404
{"detail": "Not Found"}
```

Therefore the documented similar-listings endpoint does not exist at that path.

### Rental detail

The documented rental-detail endpoint was tested with:

```text
R6000001
R6000660
R6001320
```

All returned `HTTP 200` and the correct rental object.

Result:

```text
GET /v1/rentals/{id}
```

is confirmed working.

### Project detail

The documented project-detail endpoint was tested with:

```text
P60001
P60201
P60400
```

All returned `HTTP 200` and the correct project object.

Result:

```text
GET /v1/projects/{id}
```

is confirmed working.

### Invalid-ID behavior

Known-invalid IDs were tested against listing, rental and project detail paths.

The valid detail endpoints returned `HTTP 404` with useful JSON error bodies,
including:

```text
{"detail": "no such listing in your city"}
{"detail": "no such rental in your city"}
{"detail": "no such project in your city"}
```

This agrees with the documented 404 error contract.

### Results

Confirmed discrepancies:

```text
1. Documented `/v1/listing/{id}` does not exist.
2. Undocumented `/v1/listings/{id}` exists and returns the correct listing.
3. Documented `/v1/listings/{id}/similar` does not exist.
```

Confirmed working:

```text
/v1/rentals/{id}
/v1/projects/{id}
404 responses for nonexistent records
```

### Impact

The frontend listing-detail page must use:

```text
GET /v1/listings/{id}
```

rather than the documented singular path.

The application must not depend on `/v1/listings/{id}/similar`; if a similar
listings section is desired, it must be derived client-side from the complete
listing dataset or omitted.

Rental and project detail pages may safely use their documented endpoints.


---

## H-021 — Rental collection contract

### Documentation claims

`GET /v1/rentals` documents support for:

```text
locality
bhk
furnishing
sort_by
order
```

The documented rental object also states that:

```text
price       = monthly rent in INR
deposit     = security deposit in INR
areas       = square feet
posted_at   = ISO 8601 UTC with Z suffix
```

### Field contract

The complete local rental snapshot contained:

```text
1320 records
```

Every one of the documented rental fields was present in every record.

No documented field was absent.

One additional field was observed:

```text
is_live
```

This extra field does not interfere with the documented contract and is not
treated as a submission discrepancy.

### Money fields

All 1320 rental records had numeric, non-negative money values.

Observed ranges:

```text
price:
min = 7300
max = 91500

deposit:
min = 19000
max = 806000

maintenance:
min = 0
max = 5000
```

There were:

```text
0 non-numeric prices
0 negative prices

0 non-numeric deposits
0 negative deposits

0 non-numeric maintenance values
0 negative maintenance values
```

The documented interpretation of `price` as monthly rent in rupees is therefore
consistent with the retrieved data.

### String conventions

The documented lowercase convention was checked for:

```text
locality
furnishing
property_type
```

Violations:

```text
locality:      0
furnishing:    0
property_type: 0
```

### Timestamp contract

Every rental had a `posted_at` value.

All 1320 timestamps had a UTC `Z` suffix.

Example values:

```text
2026-09-07T01:17:00Z
2026-09-03T13:06:00Z
2026-08-06T02:15:00Z
```

Therefore rental timestamps comply with the documented global timestamp
convention.

This also proves that the previously discovered timezone-naive timestamp issue
must be scoped specifically to `/v1/listings`, rather than reported as a global
API timestamp failure.

### Filter verification

The documented rental filters were tested using values present in the complete
snapshot.

Examples:

```text
locality=dwarka expressway
snapshot matches: 153
returned mismatches: 0

locality=sector 82
snapshot matches: 147
returned mismatches: 0

bhk=2
snapshot matches: 530
returned mismatches: 0

bhk=3
snapshot matches: 401
returned mismatches: 0

furnishing=semi-furnished
snapshot matches: 463
returned mismatches: 0
```

A combined request using locality, bedroom and furnishing together also returned
only matching records.

Therefore the rental filters themselves work correctly.

### Incorrect filtered totals

Although the returned records obeyed the filters, the response `total` values
were consistently smaller than the actual complete-snapshot counts.

Examples:

```text
dwarka expressway
actual: 153
reported total: 140

bhk=2
actual: 530
reported total: 485

semi-furnished
actual: 463
reported total: 423
```

This is consistent with the already-confirmed rental collection pagination/count
defect:

```text
reported unfiltered total = 1207
retrievable records       = 1320
```

Therefore these incorrect filtered totals are treated as the same pagination
metadata discrepancy rather than separate filter failures.

### Sorting

Price ascending sorting works.

For example:

```text
7300
7500
8200
8900
8900
8900
9100
...
```

However:

```text
sort_by=price&order=desc
```

returned exactly the same listing IDs in exactly the same ascending order.

The same ASC and DESC identity was also observed in other tested sort requests.

Therefore the documented descending ordering mechanism is ignored.

Because the rental documentation does not enumerate which individual fields are
valid values for `sort_by`, no field-specific sorting claim is made beyond the
clearly reproduced `order=desc` failure.

### Area-unit investigation

All rental areas were numeric positive integers.

Validation results:

```text
missing/non-numeric carpet: 0
missing/non-numeric super area: 0
non-positive carpet: 0
non-positive super area: 0
carpet > super area: 0
```

Four records had both carpet area below 300 and super area below 400:

```text
R6000114  dwelling
R6000303  100acres
R6000661  squarelane
R6001068  zerobroker
```

All four were plausible 1-BHK rentals, and the values were distributed across
different sources rather than concentrated in one website.

Website-level area distributions were highly consistent.

For example, median 2-BHK carpet area:

```text
100acres:   772
dwelling:   779
magichomes: 771
squarelane: 775.5
zerobroker: 774
```

Median 3-BHK carpet area:

```text
100acres:   1119
dwelling:   1126
magichomes: 1119.5
squarelane: 1124.5
zerobroker: 1135
```

There is no source-specific low-area cluster comparable to the one found in
sale listings.

Therefore rental areas are consistent with square feet and require no unit
conversion.

### Final result

Confirmed working:

```text
rental object fields
monthly rent / deposit / maintenance units
lowercase string convention
UTC Z timestamps
locality filter
bhk filter
furnishing filter
combined filters
rental detail endpoint
rental area units
ascending price sorting
```

Confirmed discrepancy:

```text
order=desc is ignored
```

### Frontend impact

Rental prices and areas may be displayed using the API values directly.

The frontend may use server-side rental filters, but must not rely on the
reported `total` to determine when all records have been retrieved.

Any user-facing descending sort should be performed client-side.


---

## H-022 — Project collection contract

### Documentation claims

`GET /v1/projects` documents the following filters:

```text
locality
project_status
```

and the following sorting contract:

```text
sort_by =
    price_min
    price_max
    launch_date
    total_units

order =
    asc
    desc
```

The documentation also states that project areas are square feet and project
dates use `YYYY-MM-DD`.

### Field contract

The complete project snapshot contained:

```text
400 projects
```

Every documented project field was present in every record.

There were:

```text
0 documented fields absent
0 records missing a documented field
0 undocumented additional fields
```

### Lowercase string contract

The documented lowercase convention was checked for:

```text
locality
project_status
```

Violations:

```text
locality:       0
project_status: 0
```

### Date contract

Both documented project date fields were checked:

```text
launch_date
possession_date
```

Results:

```text
launch_date:
missing: 0
invalid YYYY-MM-DD: 0

possession_date:
missing: 0
invalid YYYY-MM-DD: 0
```

Therefore project dates comply with the documented date format.

### Area contract

All project area ranges were valid positive values.

```text
invalid/non-positive min_area_sqft: 0
invalid/non-positive max_area_sqft: 0
min_area_sqft > max_area_sqft:      0
```

Observed ranges:

```text
min_area_sqft: 600 to 1400
max_area_sqft: 1027 to 3459
```

There is no evidence that project area fields require any unit conversion.

### Project price-unit confirmation

The raw project price values frequently appear inverted:

```text
raw price_min > raw price_max:
184 projects
```

After applying the independently established mixed-unit normalization:

```text
value < 10
→ crore
→ value × 10,000,000 INR

value >= 10
→ lakh
→ value × 100,000 INR
```

the result becomes:

```text
normalized price_min > normalized price_max:
0 projects
```

This further confirms the previously discovered project price-unit discrepancy.

### Filters

The documented project filters were tested against values present in the
complete snapshot.

Examples:

```text
locality=dwarka expressway
local snapshot matches: 48
returned mismatches: 0

locality=golf course road
local snapshot matches: 47
returned mismatches: 0

project_status=under construction
local snapshot matches: 137
returned mismatches: 0

project_status=new launch
local snapshot matches: 136
returned mismatches: 0
```

A combined `locality + project_status` filter was also tested and returned only
matching records.

Therefore the project filters themselves work correctly.

### Incorrect filtered totals

The API-reported `total` values were consistently lower than the complete
snapshot counts.

Examples:

```text
dwarka expressway
actual: 48
reported total: 44

under construction
actual: 137
reported total: 125
```

This is consistent with the already-confirmed unfiltered project count issue:

```text
reported total:      366
retrievable records: 400
```

Therefore this is treated as part of the existing pagination/count discrepancy,
not as a separate filter defect.

### Sorting — ascending

All four documented ascending sorts behaved correctly.

#### `price_min`

Ascending ordering was valid after normalization.

The first values corresponded to:

```text
41.5 → ₹4,150,000
44.4 → ₹4,440,000
46.1 → ₹4,610,000
48.7 → ₹4,870,000
```

#### `price_max`

The raw values did not appear numerically sorted:

```text
89.1
89.4
98.9
1.0
1.01
1.11
...
```

but after applying the verified lakh/crore normalization they became:

```text
₹8,910,000
₹8,940,000
₹9,890,000
₹10,000,000
₹10,100,000
₹11,100,000
...
```

which is correctly ascending.

This is strong evidence that the server internally understands the mixed project
price representation when sorting.

#### `launch_date`

Ascending launch dates were correctly ordered.

#### `total_units`

Ascending total-unit counts were correctly ordered.

### Descending order

For every tested sort field:

```text
price_min
price_max
launch_date
total_units
```

the requests:

```text
order=asc
order=desc
```

returned the exact same project IDs in the exact same order.

Examples:

```text
price_min ASC and DESC identical IDs: true
price_max ASC and DESC identical IDs: true
launch_date ASC and DESC identical IDs: true
total_units ASC and DESC identical IDs: true
```

Therefore `order=desc` is ignored.

### Results

Confirmed working:

```text
project object field contract
locality lowercase convention
project_status lowercase convention
launch_date format
possession_date format
project square-foot area fields
locality filter
project_status filter
combined filters
price_min ascending sort
price_max ascending sort after unit normalization
launch_date ascending sort
total_units ascending sort
project detail endpoint
```

Previously confirmed discrepancies reinforced here:

```text
project price unit representation
incorrect collection total metadata
incorrect project total_listings values
```

New confirmed discrepancy:

```text
order=desc is ignored on /v1/projects
```

### Frontend impact

Project prices must be normalized into INR before display.

The server-side filters and ascending sorting may be used.

The frontend must not rely on `order=desc`; descending user-facing sorting
should be performed client-side.

The API-reported `total` must not be used to determine whether all project
records have been retrieved.
