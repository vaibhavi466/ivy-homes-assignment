# Ivy Homes — Observed API Contract

This document describes API behaviour personally reproduced against the running service.

It is intentionally separate from `API_REFERENCE.md`.

The supplied API documentation is treated as a hypothesis source; the running API is treated as the source of truth.

---

## Health

### `GET /health`

Authentication observed:

```text
None required


## Authentication

### API-key transport

Observed protected endpoints require:

```http
X-API-Key: <assigned API key>
```

The documented query-parameter form:

```text
?api_key=<key>
```

is explicitly rejected by tested protected endpoints.

Verified against:

* `POST /auth/login`
* `GET /v1/listings`

### Login

Observed request:

```http
POST /auth/login
X-API-Key: <assigned API key>
Content-Type: application/json
```

Body:

```json
{
  "email": "<demo user>",
  "password": "<demo password>"
}
```

Observed successful response shape:

```json
{
  "access_token": "<sensitive>",
  "refresh_token": "<sensitive>",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_url": "/auth/refresh",
  "user": {
    "email": "<demo user>"
  }
}
```

Observed access-token lifetime:

```text
900 seconds
```

Observed refresh mechanism:

```text
/auth/refresh
```

The supplied API reference does not accurately describe the token fields, lifetime, or refresh behaviour.

### Protected listing requests

`GET /v1/listings` requires both:

```http
X-API-Key: <assigned API key>
Authorization: Bearer <access token>
```

Neither credential alone was sufficient in testing.



## Listings Pagination

### `GET /v1/listings`

Observed pagination model:

```text
offset + limit
```

Observed response metadata:

```json
{
  "limit": 50,
  "offset": 0,
  "count": 50,
  "total": 3201,
  "has_more": true,
  "results": []
}
```

### Traversal behaviour

Observed default limit:

```text
20
```

Observed effective maximum limit:

```text
50
```

Requests for limits above 50 were accepted but clamped to 50.

The documented `page` parameter did not advance pagination during testing.

The observed `offset` parameter controls traversal.

Recommended traversal logic:

```text
offset = 0

repeat:
    request offset + limit
    consume results

    if has_more is false:
        stop

    offset = reported_offset + reported_count
```

Do not use the reported `total` value as the stopping condition.

### Full listings traversal

Observed:

```text
pages fetched: 70
records retrieved: 3500
unique listing IDs: 3500
repeated listing ID occurrences: 0
final offset: 3450
final count: 50
final has_more: false
```

The API reported:

```text
total=3201
```

on every page during the traversal.

Therefore, for this observed dataset, `total` does not represent the complete number of retrievable listing records and must not be used as the authoritative traversal boundary.


## Rentals Collection

### `GET /v1/rentals`

Observed authentication:

```http
X-API-Key: <assigned API key>
Authorization: Bearer <access token>

### Full traversal

Observed:

```text
pages fetched: 27
records retrieved: 1320
unique listing IDs: 1320
repeated ID occurrences: 0
final offset: 1300
final count: 20
final has_more: false


## Project Price Units

Observed `/v1/projects` price values do not use one uniform INR representation.

Across all 400 retrievable projects, 800 total `price_min` / `price_max` values formed two separated clusters:

```text
< 10:
    610 values
    maximum = 5.83

>= 10:
    190 values
    minimum = 41.5


## Listing Activity Status

`GET /v1/listings` must not be assumed to return active listings only.

Full traversal produced:

```text
total retrievable listings: 3500
is_live = true: 2792
is_live = false: 708
```

All observed `is_live` values were JSON booleans.

Therefore, application features that require active listings must explicitly apply:

```text
is_live == true
```

rather than assuming the endpoint performs the filtering server-side.


## Listing Timestamps

Observed `posted_at` values from all 3500 retrievable sale listings are timezone-naive ISO datetime strings.

Example:

```text
2026-09-09T23:01:00
```

Observed across the complete snapshot:

```text
timezone-naive timestamps: 3500
parse failures: 0
```

The documented UTC `Z` representation was not observed.

For assignment calculations that use the fixed IST reference, the observed naive timestamps are interpreted using the runtime service timezone:

```text
Asia/Kolkata
UTC+05:30
```

For Q8, the required interval is:

```text
2026-09-03T00:00:00+05:30
<= posted_at <
2026-09-10T00:00:00+05:30
```

Using the observed service timezone produced:

```text
listings_last_7_days = 129
```

Application code must not assume `posted_at` includes an explicit timezone.

---

## Sale Listing Detail Endpoint

The documented endpoint:

```http
GET /v1/listing/{listing_id}
```

did not return records for tested IDs that were known to exist in the `/v1/listings` collection.

Eight existing listing IDs were tested and each returned:

```text
HTTP 404
{"detail":"Not Found"}
```

Therefore the application must not currently rely on the documented detail endpoint.

Listing-detail routes in the frontend should be built from listing data retrieved through the functioning collection endpoint unless another working server-side detail route is subsequently discovered.




## Sale Listing Area Units

Sale listing area values are not consistently returned in one unit across all sources.

A confirmed subset of `magichomes` listings returns both `carpet_area` and
`super_built_up_area` in square metres.

The observed subset is identified by:

```text
website == "magichomes"
AND carpet_area < 300
AND super_built_up_area < 400
```

Exactly 323 retrievable listings matched both conditions, with no disagreement
between the carpet-area and super-built-up-area populations.

For those records, normalize using:

```text
area_sqft = raw_area × 10.7639104167
```

All other observed sale-listing area values are treated as square feet.

This normalization is required before:

* comparing areas across listing sources;
* property deduplication;
* calculating price per square foot;
* displaying consistent area values in the application.
