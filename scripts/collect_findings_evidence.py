import json
import os
from collections import Counter
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()


BASE_URL = os.environ["IVY_BASE_URL"].rstrip("/")
API_KEY = os.environ["IVY_API_KEY"]
EMAIL = os.environ["IVY_DEMO_USER_1"]
PASSWORD = os.environ["IVY_DEMO_PASSWORD"]

LISTINGS_PATH = Path("data/raw/listings.json")
RENTALS_PATH = Path("data/raw/rentals.json")
PROJECTS_PATH = Path("data/raw/projects.json")
SUBMISSION_PATH = Path("submission.json")


def load_results(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["results"]


def load_submission():
    with SUBMISSION_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def print_ids(title, ids):
    ids = list(ids)

    print()
    print("=" * 72)
    print(title)
    print("=" * 72)

    print("count:", len(ids))

    print(
        "evidence up to 20:"
    )

    print(
        json.dumps(
            ids[:20],
            indent=2,
        )
    )


def login(session):
    response = session.post(
        f"{BASE_URL}/auth/login",
        headers={
            "X-API-Key": API_KEY,
        },
        json={
            "email": EMAIL,
            "password": PASSWORD,
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()[
        "access_token"
    ]


def main():
    listings = load_results(
        LISTINGS_PATH
    )

    rentals = load_results(
        RENTALS_PATH
    )

    projects = load_results(
        PROJECTS_PATH
    )

    submission = load_submission()

    answers = submission[
        "answers"
    ]

    print(
        "=== Final Findings Evidence Collector ==="
    )

    print(
        "listings:",
        len(listings),
    )

    print(
        "rentals:",
        len(rentals),
    )

    print(
        "projects:",
        len(projects),
    )

    # --------------------------------------------------
    # 1. Pagination total under-reporting
    # --------------------------------------------------

    # These records occur AFTER the API's claimed
    # collection total and therefore prove that
    # additional records are retrievable.

    listing_reported_total = 3201
    rental_reported_total = 1207
    project_reported_total = 366

    listing_after_total = [
        item["listing_id"]
        for item
        in listings[
            listing_reported_total:
            listing_reported_total + 20
        ]
    ]

    rental_after_total = [
        item["listing_id"]
        for item
        in rentals[
            rental_reported_total:
            rental_reported_total + 20
        ]
    ]

    project_after_total = [
        item["project_id"]
        for item
        in projects[
            project_reported_total:
            project_reported_total + 20
        ]
    ]

    print_ids(
        "LISTINGS BEYOND REPORTED TOTAL=3201",
        listing_after_total,
    )

    print_ids(
        "RENTALS BEYOND REPORTED TOTAL=1207",
        rental_after_total,
    )

    print_ids(
        "PROJECTS BEYOND REPORTED TOTAL=366",
        project_after_total,
    )

    # --------------------------------------------------
    # 2. Inactive listings returned by active-only API
    # --------------------------------------------------

    inactive_ids = [
        item["listing_id"]
        for item in listings
        if item.get("is_live")
        is False
    ]

    print_ids(
        "INACTIVE LISTINGS RETURNED",
        inactive_ids,
    )

    # --------------------------------------------------
    # 3. Listing area-unit discrepancy
    # --------------------------------------------------

    area_unit_ids = [
        item["listing_id"]
        for item in listings
        if (
            item.get("website")
            == "magichomes"
            and isinstance(
                item.get(
                    "carpet_area"
                ),
                (int, float),
            )
            and isinstance(
                item.get(
                    "super_built_up_area"
                ),
                (int, float),
            )
            and item[
                "carpet_area"
            ] < 300
            and item[
                "super_built_up_area"
            ] < 400
        )
    ]

    print_ids(
        "MAGICHOMES LISTINGS IN SQM-LIKE AREA CLUSTER",
        area_unit_ids,
    )

    # --------------------------------------------------
    # 4. Listing timestamp discrepancy
    # --------------------------------------------------

    naive_timestamp_ids = [
        item["listing_id"]
        for item in listings
        if (
            isinstance(
                item.get(
                    "posted_at"
                ),
                str,
            )
            and not item[
                "posted_at"
            ].endswith("Z")
            and not (
                len(
                    item[
                        "posted_at"
                    ]
                ) >= 6
                and item[
                    "posted_at"
                ][-6]
                in ("+", "-")
                and item[
                    "posted_at"
                ][-3] == ":"
            )
        )
    ]

    print_ids(
        "LISTINGS WITH TIMEZONE-NAIVE posted_at",
        naive_timestamp_ids,
    )

    # --------------------------------------------------
    # 5. Corrupt listings
    # --------------------------------------------------

    corrupt_ids = answers[
        "corrupt_listing_ids"
    ]

    print_ids(
        "CORRUPT LISTINGS",
        corrupt_ids,
    )

    # --------------------------------------------------
    # 6. Fraud / bait listings
    # --------------------------------------------------

    fake_ids = answers[
        "fake_listing_ids"
    ]

    print_ids(
        "FAKE / BAIT LISTINGS",
        fake_ids,
    )

    # --------------------------------------------------
    # 7. Project mixed-price-unit evidence
    # --------------------------------------------------

    # A very strong symptom is raw price_min > raw
    # price_max. After our verified unit normalization,
    # these all become sensible.

    raw_inverted_projects = [
        project["project_id"]
        for project in projects
        if (
            isinstance(
                project.get(
                    "price_min"
                ),
                (int, float),
            )
            and isinstance(
                project.get(
                    "price_max"
                ),
                (int, float),
            )
            and project[
                "price_min"
            ] > project[
                "price_max"
            ]
        )
    ]

    print_ids(
        "PROJECTS WITH RAW price_min > price_max",
        raw_inverted_projects,
    )

    # --------------------------------------------------
    # 8. Wrong project total_listings
    # --------------------------------------------------

    live_counts = Counter(
        item.get("project_id")
        for item in listings
        if (
            item.get("is_live")
            is True
            and item.get(
                "project_id"
            )
            is not None
        )
    )

    wrong_project_counts = [
        project["project_id"]
        for project in projects
        if (
            project.get(
                "total_listings"
            )
            != live_counts.get(
                project[
                    "project_id"
                ],
                0,
            )
        )
    ]

    print_ids(
        "PROJECTS WITH WRONG LIVE LISTING COUNT",
        wrong_project_counts,
    )

    print()
    print(
        "Expected Q10 count:",
        answers[
            "projects_with_wrong_listing_count"
        ],
    )

    print(
        "Recomputed mismatch count:",
        len(
            wrong_project_counts
        ),
    )

    # --------------------------------------------------
    # 9. project_id filter ignored
    # --------------------------------------------------

    session = requests.Session()

    token = login(
        session
    )

    project_id = projects[0][
        "project_id"
    ]

    response = session.get(
        f"{BASE_URL}/v1/listings",
        headers={
            "X-API-Key": API_KEY,
            "Authorization":
                f"Bearer {token}",
        },
        params={
            "project_id":
                project_id,
            "limit":
                50,
            "offset":
                0,
        },
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    returned = payload.get(
        "results",
        [],
    )

    wrong_filter_records = [
        item["listing_id"]
        for item in returned
        if item.get(
            "project_id"
        ) != project_id
    ]

    print()
    print("=" * 72)
    print(
        "project_id FILTER EVIDENCE"
    )
    print("=" * 72)

    print(
        "requested project_id:",
        project_id,
    )

    print(
        "returned records:",
        len(returned),
    )

    print(
        "records belonging to wrong project:",
        len(
            wrong_filter_records
        ),
    )

    print(
        "first 20 wrong listing IDs:"
    )

    print(
        json.dumps(
            wrong_filter_records[:20],
            indent=2,
        )
    )

    # --------------------------------------------------
    # 10. Detail endpoint valid-ID evidence
    # --------------------------------------------------

    valid_listing_ids = [
        listings[0][
            "listing_id"
        ],
        listings[
            len(listings) // 2
        ][
            "listing_id"
        ],
        listings[-1][
            "listing_id"
        ],
    ]

    print_ids(
        "KNOWN-VALID LISTING IDs FOR DETAIL ENDPOINT FINDINGS",
        valid_listing_ids,
    )

    print()
    print("=" * 72)
    print(
        "FINAL SANITY CHECKS"
    )
    print("=" * 72)

    print(
        "inactive listing count:",
        len(inactive_ids),
    )

    print(
        "area-unit candidate count:",
        len(area_unit_ids),
    )

    print(
        "naive listing timestamp count:",
        len(
            naive_timestamp_ids
        ),
    )

    print(
        "raw inverted project-price count:",
        len(
            raw_inverted_projects
        ),
    )

    print(
        "wrong project count:",
        len(
            wrong_project_counts
        ),
    )


if __name__ == "__main__":
    main()