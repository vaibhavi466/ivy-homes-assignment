# Ivy Homes Assignment - Requirements & Acceptance Checklist

## 1. Core Objective

Build a reliable web application against the **actual running Ivy Homes API**, even when the supplied API documentation is inaccurate.

The running API is the source of truth.

The project must:

1. Discover the actual API behaviour.
2. Identify discrepancies between the API and the supplied documentation.
3. Compute the ten required answers accurately.
4. Build the required web frontend against observed API behaviour.
5. Document the investigation process, including hypotheses that were tested and turned out to be correct.
6. Document hypotheses that were tested and turned out to be false.

---

# 2. Fixed Reference Time

All time-dependent calculations must use:

```text
REFERENCE = 2026-09-10T00:00:00+05:30
```

For `listings_last_7_days`, the exact interval is:

```text
[REFERENCE - 7 days, REFERENCE)
```

Meaning:

```text
start <= posted_at < reference
```

Do NOT use the current date/time.

---

# 3. Definition of "Retrievable"

For the assignment:

> Retrievable means every record the assigned API key can obtain from the endpoint with no filters applied, after paging completely to the end.

Therefore:

* Do not calculate answers from only the first page.
* Do not use filters when determining the full retrievable dataset.
* Verify pagination behaviour against the running API.

---

# 4. Mandatory Frontend Requirements

All six features are mandatory.

## 4.1 Login

* [ ] Uses the real API authentication flow.
* [ ] Uses real demo credentials.
* [ ] Session survives browser refresh.
* [ ] Application remains authenticated and functional at least 30 minutes after login.
* [ ] Logout behaviour is tested.

## 4.2 Browse Listings

The listings UI must support pagination or infinite scrolling.

Required filters:

* [ ] Locality
* [ ] Bedrooms
* [ ] Price range
* [ ] Furnishing

Important:

Each filter must **actually filter the results**.

If the server does not correctly implement a documented filter, the frontend must still produce correct filtering behaviour.

## 4.3 Listing Detail

* [ ] Every listing has a detail page.
* [ ] Listing page is reachable through its own URL.
* [ ] Direct navigation to the URL works.
* [ ] Browser refresh on a listing detail page works.

## 4.4 Saved Listings

Users must be able to:

* [ ] Save a listing.
* [ ] Remove a saved listing.
* [ ] View saved listings.
* [ ] Retain saved listings after page reload.
* [ ] Retain saved listings after logout and re-login.
* [ ] Saved listings must be user-specific.

Test with multiple demo accounts.

## 4.5 Rentals and Projects

* [ ] Rentals are browsable.
* [ ] Projects are browsable.
* [ ] Rental prices use the correct actual unit.
* [ ] Rental areas use the correct actual unit.
* [ ] Project prices use the correct actual unit.
* [ ] Project areas use the correct actual unit.

Do not blindly trust documented units.

## 4.6 Insights Screen

The insights screen must include:

* [ ] Information promised by the documented analytics summary, where appropriate.
* [ ] Useful discoveries made during the investigation.
* [ ] Information translated into something understandable/useful for a property user.

The insights screen should make relevant discoveries visible to a human rather than leaving them only inside analysis scripts.

---

# 5. Required Answers

The final submission must contain exactly these answer fields.

## Q1 — total_listing_records

Question:

How many listing records are retrievable from `/v1/listings`?

Acceptance:

* [ ] Fetch all pages.
* [ ] Use no filters.
* [ ] Count records, not assumed unique properties.

---

## Q2 — unique_properties

Question:

Among all retrievable listing records, how many distinct physical properties are represented?

Important:

Multiple listing records may describe the same physical property.

Acceptance:

* [ ] Do not assume `listing_id` = physical property identity.
* [ ] Build and validate a property deduplication/entity-resolution rule.
* [ ] Inspect edge cases and possible false merges.
* [ ] Inspect edge cases and possible false splits.
* [ ] Produce reproducible logic.

---

## Q3 — active_listings

Question:

How many retrievable listing records have:

```text
is_live = true
```

Acceptance:

* [ ] Use the actual returned field.
* [ ] Count exact boolean `true` records.

---

## Q4 — corrupt_listing_ids

Question:

Identify listing records that describe something that cannot exist.

Acceptance:

* [ ] Detect logically/physically impossible records.
* [ ] Distinguish unusual records from impossible records.
* [ ] Manually inspect detected candidates.
* [ ] Include only confirmed IDs.
* [ ] Sort IDs in final output.

Precision is important.

---

## Q5 — total_monthly_rent

Question:

Sum the monthly rent of all retrievable rental records in the assigned locality supplied with the API credentials.

Acceptance:

* [ ] Fetch every rental record.
* [ ] Confirm actual rent field/unit.
* [ ] Filter using assigned locality.
* [ ] Sum monthly rent only.

---

## Q6 — avg_price_per_sqft_2bhk

Population:

Retrievable listing records where:

```text
is_live = true
AND bedroom = 2
AND listing_id NOT IN corrupt_listing_ids
AND listing_id NOT IN fake_listing_ids
```

For every remaining listing calculate:

```text
price / carpet_area
```

Then calculate the arithmetic mean of those individual values.

Return rupees per square foot rounded to 2 decimal places.

Acceptance:

* [ ] Q4 finalized first.
* [ ] Q9 finalized first.
* [ ] Price unit verified.
* [ ] Carpet area unit verified.
* [ ] Corrupt records excluded.
* [ ] Fake records excluded.
* [ ] Arithmetic mean used.
* [ ] Rounded to two decimals.

Do NOT automatically calculate:

```text
sum(price) / sum(area)
```

unless analysis proves that interpretation is required.

---

## Q7 — costliest_project

Question:

Find the project having the highest maximum price.

Required output structure:

```json
{
  "project_id": "...",
  "price_max_inr": 0
}
```

Acceptance:

* [ ] Fetch every project.
* [ ] Verify actual maximum-price field.
* [ ] Verify price unit.
* [ ] Return exact required JSON structure.

---

## Q8 — listings_last_7_days

Count listings posted inside:

```text
[REFERENCE - 7 days, REFERENCE)
```

where:

```text
REFERENCE = 2026-09-10T00:00:00+05:30
```

Acceptance:

* [ ] Parse timestamps correctly.
* [ ] Handle timezone correctly.
* [ ] Lower boundary inclusive.
* [ ] Upper boundary exclusive.
* [ ] Do not use current time.

---

## Q9 — fake_listing_ids

Question:

Identify deliberately non-genuine listings that exist to generate enquiries.

Acceptance:

* [ ] Use dataset evidence.
* [ ] Build testable hypotheses.
* [ ] Inspect matching records.
* [ ] Inspect exceptions to proposed rules.
* [ ] Optimize both precision and recall.
* [ ] Do not add speculative IDs.
* [ ] Sort final IDs.

---

## Q10 — projects_with_wrong_listing_count

Question:

For how many projects is the project's reported listing count wrong?

Acceptance:

* [ ] Fetch all projects.
* [ ] Establish what the API actually considers listings belonging to a project.
* [ ] Compare reported counts against independently derived actual counts.
* [ ] Investigate inconsistencies rather than assuming documentation semantics.

---

# 6. Findings Requirements

Every confirmed discrepancy between documentation and actual API behaviour must be represented as a finding.

Structure:

```json
{
  "endpoint": "",
  "category": "",
  "documented": "",
  "actual": "",
  "how_found": "",
  "impact": "",
  "evidence": []
}
```

## Allowed categories

Only these values may be used:

```text
auth
pagination
units
filters
sorting
timestamps
duplicates
completeness
data_quality
fraud
consistency
missing_endpoint
undocumented_endpoint
```

Do NOT invent additional category names.

---

# 7. Finding Acceptance Gate

Before adding any finding to `submission.json`, verify:

* [ ] I personally reproduced the discrepancy.
* [ ] The documentation actually makes the claim I am disputing.
* [ ] I can clearly describe the observed API behaviour.
* [ ] I know how I tested it.
* [ ] I understand its impact.
* [ ] Evidence is included when the claim concerns records.
* [ ] Evidence actually demonstrates the claim.
* [ ] Endpoint notation follows assignment rules.
* [ ] Category is one of the allowed values.
* [ ] This is not merely a suspicion.

Precision and recall both matter.

Do not pad the findings list with speculative claims.

---

# 8. Evidence Rules

Evidence may contain relevant identifiers such as:

```text
listing_id
project_id
phone number
```

For record-level findings, evidence must be supplied.

Use up to 20 identifiers demonstrating the discrepancy.

Do not include evidence that does not actually demonstrate the claim.

---

# 9. Endpoint Formatting Rules for Findings

When documentation itself contains the wrong endpoint:

Use the path exactly as documented.

For parameterized paths use:

```text
/v1/listings/{id}
```

not a real record ID.

When reporting an endpoint that exists but is undocumented:

Use the actual working API path.

Use:

```text
*
```

only when a discrepancy applies to every endpoint.

---

# 10. Investigation Requirements

The investigation must distinguish:

```text
documented behaviour
vs
observed API behaviour
```

For every meaningful hypothesis record:

```text
Observation
Hypothesis
Test
Evidence
Result
Impact
```

Results should be classified as:

```text
Confirmed
Rejected
Inconclusive
```

Rejected hypotheses must also be retained because the README must explain things that were checked and turned out to be fine.

---

# 11. Data Collection Requirements

* [ ] Verify pagination behaviour first.
* [ ] Download the complete retrievable listing dataset.
* [ ] Download the complete retrievable rental dataset.
* [ ] Download the complete retrievable project dataset.
* [ ] Preserve raw responses during analysis.
* [ ] Perform repeated analytical work locally when possible.
* [ ] Avoid unnecessary API requests.
* [ ] Stay well below the API rate limit.

Raw data should not automatically be committed to the public repository.

---

# 12. Documentation/API Audit Areas

At minimum investigate:

* [ ] Authentication
* [ ] Endpoint paths
* [ ] Response schemas
* [ ] Pagination
* [ ] Page size / limit behaviour
* [ ] Filters
* [ ] Sorting
* [ ] Money units
* [ ] Area units
* [ ] Timestamp formats/timezones
* [ ] Duplicate/property identity assumptions
* [ ] Completeness assumptions
* [ ] Data-quality assumptions
* [ ] Fraud/authenticity assumptions
* [ ] Cross-endpoint consistency
* [ ] Missing documented endpoints
* [ ] Potential undocumented endpoints discovered through legitimate observable behaviour

Do not perform unauthorized endpoint scanning.

---

# 13. Submission Structure

Repository root must contain:

```text
submission.json
```

Required top-level structure:

```json
{
  "api_key": "",
  "candidate": {
    "name": "",
    "email": "",
    "repo_url": "",
    "demo_url": ""
  },
  "answers": {
    "total_listing_records": 0,
    "unique_properties": 0,
    "active_listings": 0,
    "corrupt_listing_ids": [],
    "total_monthly_rent": 0,
    "avg_price_per_sqft_2bhk": 0.0,
    "costliest_project": {
      "project_id": "",
      "price_max_inr": 0
    },
    "listings_last_7_days": 0,
    "fake_listing_ids": [],
    "projects_with_wrong_listing_count": 0
  },
  "findings": []
}
```

---

# 14. README Requirements

README must explain:

* [ ] How to run the project.
* [ ] How documentation claims were evaluated.
* [ ] How discrepancies were investigated.
* [ ] What was discovered.
* [ ] What was tested and turned out to be correct.
* [ ] How AI/LLM tools were used.
* [ ] What would be done with another two days.

README should explain reasoning rather than merely listing features.

---

# 15. Git Requirements

* [ ] Commit throughout development.
* [ ] Use meaningful commit messages.
* [ ] Preserve investigation progress.
* [ ] Avoid one giant final commit.
* [ ] Do not fabricate Git history afterward.

---

# 16. API Safety Rules

Do not:

* [ ] Perform credential stuffing.
* [ ] Search for another candidate's API key.
* [ ] Share the assigned API key with other candidates.
* [ ] Attempt denial-of-service behaviour.
* [ ] Attempt to circumvent rate limits.
* [ ] Perform unnecessary aggressive endpoint scanning.

Every API request may be logged against the assigned key.

---

# 17. AI Usage

AI/LLM usage is permitted.

Requirements:

* [ ] Disclose AI/tool usage honestly in README.
* [ ] Personally review generated code.
* [ ] Personally validate generated findings.
* [ ] Do not treat AI-generated claims as evidence.

Final responsibility for every submitted answer and finding remains with the candidate.

---

# 18. Scoring

## Stage 1 — Automatic

```text
10 answers: 60 points
Findings:   40 points
```

Important:

Not all ten questions have equal value.

Questions requiring reasoning are worth considerably more than simple counting questions.

Findings are evaluated using both precision and recall.

---

## Stage 2 — Human Review

Only strong Stage-1 candidates proceed.

Final weighting:

```text
Stage 1 accuracy             50%
Application                  40%
README + Git history         10%
```

---

# 19. Development Priority

Use this priority order:

```text
1. API/data correctness
2. Ten required answers
3. High-precision findings
4. Six mandatory frontend features
5. Reliability and UX
6. Insights
7. Documentation
8. Optional visual polish
```

Do not sacrifice correctness for extra frontend features.

---

# 20. Final Definition of Done

The assignment is not finished until:

* [ ] Every API collection required for analysis has been fully retrieved.
* [ ] Every one of the ten answers is reproducible.
* [ ] Q2 methodology has been validated.
* [ ] Q4 IDs have been individually checked.
* [ ] Q9 IDs have been individually checked.
* [ ] Q6 excludes Q4 and Q9 correctly.
* [ ] Every submitted finding is reproducible.
* [ ] Every record-level finding has valid evidence.
* [ ] All six frontend requirements work.
* [ ] Authentication survives refresh and 30+ minutes.
* [ ] Saved listings survive reload and re-login and are user-specific.
* [ ] Price and area units shown in the UI are verified.
* [ ] Insights expose useful investigation discoveries.
* [ ] Production build succeeds.
* [ ] Demo URL works from a fresh browser.
* [ ] Repository is public.
* [ ] README is complete.
* [ ] AI usage is disclosed.
* [ ] Git history demonstrates incremental work.
* [ ] `submission.json` passes final schema validation.
* [ ] Final answers have been recomputed immediately before submission.
