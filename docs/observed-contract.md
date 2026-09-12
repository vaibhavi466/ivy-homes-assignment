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