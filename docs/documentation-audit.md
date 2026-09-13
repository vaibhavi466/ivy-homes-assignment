# Documentation Coverage Audit

This file tracks every meaningful contract claim in `API_REFERENCE.md`.

Status meanings:

* `CONFIRMED WRONG` — reproduced discrepancy; candidate `submission.json` finding.
* `CONFIRMED OK` — tested and matched documentation; keep for README.
* `NOT TESTED` — must be checked before final findings are locked.
* `PARTIAL` — some parts tested, but the full documented contract is not yet closed.

## Authentication

| Claim                                             | Status          |
| ------------------------------------------------- | --------------- |
| API key is supplied as query parameter            | CONFIRMED WRONG |
| Login accepts documented credentials              | CONFIRMED OK    |
| Login response contains documented token contract | CONFIRMED WRONG |
| Token remains valid for 24 hours without refresh  | CONFIRMED WRONG |
| No refresh flow exists                            | CONFIRMED WRONG |
| `/auth/logout` behaves as documented              | NOT TESTED      |

## Global conventions

| Claim                                        | Status          |
| -------------------------------------------- | --------------- |
| Money is INR everywhere                      | CONFIRMED WRONG |
| Area is sqft everywhere                      | CONFIRMED WRONG |
| Timestamps are ISO UTC with `Z` everywhere   | CONFIRMED WRONG |
| Documented lowercase string conventions hold | NOT TESTED      |

## Collection pagination

| Claim                                                 | Status          |
| ----------------------------------------------------- | --------------- |
| Collections use `page` and `limit`                    | CONFIRMED WRONG |
| Maximum limit is 200                                  | CONFIRMED WRONG |
| Response uses `total`, `page`, `page_size`, `results` | CONFIRMED WRONG |
| `total` is exact                                      | CONFIRMED WRONG |

## Listings

| Claim                                           | Status          |
| ----------------------------------------------- | --------------- |
| `/v1/listings` exists                           | CONFIRMED OK    |
| Returns active listings only                    | CONFIRMED WRONG |
| `locality` filter works                         | CONFIRMED OK    |
| `bhk` filter works                              | CONFIRMED OK    |
| `property_type` filter works                    | CONFIRMED OK    |
| `min_price` works                               | CONFIRMED OK    |
| `max_price` works                               | CONFIRMED OK    |
| `furnishing` works                              | CONFIRMED OK    |
| `sort_by=price` works                           | CONFIRMED OK    |
| `sort_by=carpet_area` works                     | CONFIRMED WRONG |
| `sort_by=posted_at` works                       | CONFIRMED WRONG |
| `sort_by=bedroom` works                         | CONFIRMED OK    |
| `order=asc/desc` works                          | CONFIRMED WRONG |
| Single-listing path `/v1/listing/{id}` exists   | CONFIRMED WRONG |
| `/v1/listings/{id}/similar` works as documented | CONFIRMED WRONG |
| Listing areas are sqft                          | CONFIRMED WRONG |
| Listing timestamps are UTC `Z`                  | CONFIRMED WRONG |

## Rentals

| Claim                              | Status       |
| ---------------------------------- | ------------ |
| `/v1/rentals` exists               | CONFIRMED OK |
| `price` is monthly rent in INR     | CONFIRMED OK |
| `locality` filter works            | NOT TESTED   |
| `bhk` filter works                 | NOT TESTED   |
| `furnishing` filter works          | NOT TESTED   |
| documented sorting works           | NOT TESTED   |
| `/v1/rentals/{id}` works           | CONFIRMED OK |
| documented rental field names hold | PARTIAL      |

## Projects

| Claim                                         | Status          |
| --------------------------------------------- | --------------- |
| `/v1/projects` exists                         | CONFIRMED OK    |
| project prices are INR                        | CONFIRMED WRONG |
| `locality` filter works                       | NOT TESTED      |
| `project_status` filter works                 | NOT TESTED      |
| documented sorting works                      | NOT TESTED      |
| `/v1/projects/{id}` works                     | CONFIRMED OK    |
| `total_listings` agrees with current listings | CONFIRMED WRONG |
| referenced `project_id` listings filter works | CONFIRMED WRONG |

## Favourites

| Claim                              | Status     |
| ---------------------------------- | ---------- |
| GET `/v1/favourites` works         | NOT TESTED |
| POST `/v1/favourites` works        | NOT TESTED |
| DELETE `/v1/favourites/{id}` works | NOT TESTED |
| favourites remain user-specific    | NOT TESTED |
| favourites survive reload/re-login | NOT TESTED |

## Analytics

| Claim                                         | Status     |
| --------------------------------------------- | ---------- |
| `/v1/analytics/summary` exists                | NOT TESTED |
| returned aggregate fields match documentation | NOT TESTED |
| documented aggregates are numerically correct | NOT TESTED |

## Erros 
| Unknown record IDs return documented 404 JSON errors | CONFIRMED OK |

## Data-level discoveries

| Issue                            | Status                                                                                      |
| -------------------------------- | ------------------------------------------------------------------------------------------- |
| impossible/corrupt listings      | CONFIRMED WRONG                                                                             |
| fake enquiry-generation listings | CONFIRMED WRONG                                                                             |
| duplicate-property resolution    | ANSWERED FOR Q2; finding status intentionally withheld pending documentation wording review |
| project listing counts           | CONFIRMED WRONG                                                                             |

## Final quality gate

`submission.json` findings will only contain discrepancies that:

1. were personally reproduced;
2. map to an allowed category;
3. can be described as one clear documentation-vs-API disagreement;
4. include evidence IDs whenever the claim concerns records;
5. do not duplicate another finding.
