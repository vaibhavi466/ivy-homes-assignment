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
