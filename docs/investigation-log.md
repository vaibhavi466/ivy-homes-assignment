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

### Source

`API_REFERENCE.md` documents:

`GET /health`

as an unauthenticated endpoint returning service status and the server clock.

### Hypothesis

The `/health` endpoint exists at the documented path and can be called without API-key or user-session authentication.

### Test

Send:

```http
GET /health