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
