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