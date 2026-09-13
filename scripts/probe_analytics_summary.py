import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import requests
from dotenv import load_dotenv


load_dotenv()


BASE_URL = os.environ["IVY_BASE_URL"].rstrip("/")
API_KEY = os.environ["IVY_API_KEY"]
EMAIL = os.environ["IVY_DEMO_USER_1"]
PASSWORD = os.environ["IVY_DEMO_PASSWORD"]

ASSIGNED_CITY = os.environ.get(
    "IVY_ASSIGNED_CITY",
    "",
)

LISTINGS_PATH = Path(
    "data/raw/listings.json"
)

SUBMISSION_PATH = Path(
    "submission.json"
)

SQFT_PER_SQM = 10.7639104167


def load_listings():
    with LISTINGS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["results"]


def load_answers():
    with SUBMISSION_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["answers"]


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


def headers(token):
    return {
        "X-API-Key": API_KEY,
        "Authorization":
            f"Bearer {token}",
    }


def is_number(value):
    return (
        isinstance(
            value,
            (int, float),
        )
        and not isinstance(
            value,
            bool,
        )
    )


def normalize_carpet_area(
    listing,
):
    carpet = listing.get(
        "carpet_area"
    )

    super_area = listing.get(
        "super_built_up_area"
    )

    if not is_number(carpet):
        return None

    # Previously established listing
    # mixed-area-unit rule.
    if (
        listing.get("website")
        == "magichomes"
        and is_number(super_area)
        and carpet < 300
        and super_area < 400
    ):
        return (
            carpet
            * SQFT_PER_SQM
        )

    return carpet


def clean_median(values):
    values = [
        value
        for value in values
        if is_number(value)
    ]

    if not values:
        return None

    return median(values)


def price_per_sqft(
    listing,
    normalize_area,
):
    price = listing.get(
        "price"
    )

    if not is_number(price):
        return None

    if price <= 0:
        return None

    if normalize_area:
        area = normalize_carpet_area(
            listing
        )
    else:
        area = listing.get(
            "carpet_area"
        )

    if (
        not is_number(area)
        or area <= 0
    ):
        return None

    return price / area


def compute_candidate_metrics(
    listings,
    corrupt_ids,
    fake_ids,
):
    candidates = {}

    variants = {
        "all_raw": [
            item
            for item in listings
        ],
        "live_raw": [
            item
            for item in listings
            if item.get("is_live")
            is True
        ],
        "all_clean": [
            item
            for item in listings
            if (
                item["listing_id"]
                not in corrupt_ids
                and item["listing_id"]
                not in fake_ids
            )
        ],
        "live_clean": [
            item
            for item in listings
            if (
                item.get("is_live")
                is True
                and item["listing_id"]
                not in corrupt_ids
                and item["listing_id"]
                not in fake_ids
            )
        ],
    }

    for name, records in variants.items():
        prices = [
            item.get("price")
            for item in records
            if (
                is_number(
                    item.get("price")
                )
                and item["price"] > 0
            )
        ]

        raw_ppsf = [
            value
            for item in records
            for value in [
                price_per_sqft(
                    item,
                    normalize_area=False,
                )
            ]
            if value is not None
        ]

        normalized_ppsf = [
            value
            for item in records
            for value in [
                price_per_sqft(
                    item,
                    normalize_area=True,
                )
            ]
            if value is not None
        ]

        candidates[name] = {
            "count":
                len(records),
            "median_price":
                clean_median(prices),
            "median_ppsf_raw":
                clean_median(
                    raw_ppsf
                ),
            "median_ppsf_normalized":
                clean_median(
                    normalized_ppsf
                ),
        }

    return candidates


def summarize_by_locality(
    listings,
    live_only=False,
):
    groups = defaultdict(list)

    for listing in listings:
        if (
            live_only
            and listing.get(
                "is_live"
            )
            is not True
        ):
            continue

        locality = listing.get(
            "locality"
        )

        if locality is None:
            continue

        groups[locality].append(
            listing
        )

    result = {}

    for locality, records in groups.items():
        positive_prices = [
            item["price"]
            for item in records
            if (
                is_number(
                    item.get("price")
                )
                and item["price"] > 0
            )
        ]

        result[locality] = {
            "count":
                len(records),
            "median_price":
                (
                    median(
                        positive_prices
                    )
                    if positive_prices
                    else None
                ),
        }

    return result


def summarize_by_bhk(
    listings,
    live_only=False,
):
    counts = Counter()

    for listing in listings:
        if (
            live_only
            and listing.get(
                "is_live"
            )
            is not True
        ):
            continue

        bedroom = listing.get(
            "bedroom"
        )

        if bedroom is not None:
            counts[bedroom] += 1

    return dict(counts)


def print_locality_comparison(
    summary_rows,
    all_locality,
    live_locality,
):
    print()
    print(
        "=== BY_LOCALITY COMPARISON ==="
    )

    if not isinstance(
        summary_rows,
        list,
    ):
        print(
            "by_locality is not a list."
        )
        return

    print(
        "Analytics locality rows:",
        len(summary_rows),
    )

    print(
        "Snapshot unique localities:",
        len(all_locality),
    )

    all_count_matches = 0
    live_count_matches = 0

    all_median_matches = 0
    live_median_matches = 0

    unknown_localities = []

    for row in summary_rows:
        if not isinstance(
            row,
            dict,
        ):
            continue

        locality = row.get(
            "locality"
        )

        api_count = row.get(
            "count"
        )

        api_median = row.get(
            "median_price"
        )

        all_row = all_locality.get(
            locality
        )

        live_row = live_locality.get(
            locality
        )

        if all_row is None:
            unknown_localities.append(
                locality
            )
            continue

        if (
            api_count
            == all_row["count"]
        ):
            all_count_matches += 1

        if (
            live_row is not None
            and api_count
            == live_row["count"]
        ):
            live_count_matches += 1

        if (
            api_median
            == all_row[
                "median_price"
            ]
        ):
            all_median_matches += 1

        if (
            live_row is not None
            and api_median
            == live_row[
                "median_price"
            ]
        ):
            live_median_matches += 1

    print(
        "Rows whose count matches ALL records:",
        all_count_matches,
    )

    print(
        "Rows whose count matches LIVE records:",
        live_count_matches,
    )

    print(
        "Rows whose median_price "
        "matches ALL records:",
        all_median_matches,
    )

    print(
        "Rows whose median_price "
        "matches LIVE records:",
        live_median_matches,
    )

    print(
        "Unknown locality rows:",
        unknown_localities,
    )

    print()
    print(
        "First 10 analytics locality rows:"
    )

    for row in summary_rows[:10]:
        locality = row.get(
            "locality"
        )

        print(
            {
                "api":
                    row,
                "all_snapshot":
                    all_locality.get(
                        locality
                    ),
                "live_snapshot":
                    live_locality.get(
                        locality
                    ),
            }
        )


def print_bhk_comparison(
    summary_rows,
    all_bhk,
    live_bhk,
):
    print()
    print(
        "=== BY_BHK COMPARISON ==="
    )

    if not isinstance(
        summary_rows,
        list,
    ):
        print(
            "by_bhk is not a list."
        )
        return

    print(
        "Analytics BHK rows:",
        len(summary_rows),
    )

    print(
        "Snapshot BHK values:",
        sorted(
            all_bhk.keys()
        ),
    )

    all_matches = 0
    live_matches = 0

    for row in summary_rows:
        if not isinstance(
            row,
            dict,
        ):
            continue

        bedroom = row.get(
            "bedroom"
        )

        count = row.get(
            "count"
        )

        if (
            count
            == all_bhk.get(
                bedroom
            )
        ):
            all_matches += 1

        if (
            count
            == live_bhk.get(
                bedroom
            )
        ):
            live_matches += 1

    print(
        "Rows matching ALL counts:",
        all_matches,
    )

    print(
        "Rows matching LIVE counts:",
        live_matches,
    )

    print()
    print(
        "Analytics rows:"
    )

    for row in summary_rows:
        bedroom = row.get(
            "bedroom"
        )

        print(
            {
                "api":
                    row,
                "all_snapshot":
                    all_bhk.get(
                        bedroom
                    ),
                "live_snapshot":
                    live_bhk.get(
                        bedroom
                    ),
            }
        )


def main():
    listings = load_listings()
    answers = load_answers()

    corrupt_ids = set(
        answers[
            "corrupt_listing_ids"
        ]
    )

    fake_ids = set(
        answers[
            "fake_listing_ids"
        ]
    )

    print(
        "=== Analytics Summary Contract Probe ==="
    )

    print(
        "Complete listing snapshot:",
        len(listings),
    )

    print(
        "Verified active listings:",
        answers[
            "active_listings"
        ],
    )

    session = requests.Session()

    # ---------------------------------
    # Authentication behavior
    # ---------------------------------

    response = session.get(
        f"{BASE_URL}/v1/analytics/summary",
        timeout=30,
    )

    print()
    print(
        "=== Without credentials ==="
    )

    print(
        "Status:",
        response.status_code,
    )

    try:
        print(
            "Payload:",
            response.json(),
        )
    except ValueError:
        print(
            "Body:",
            response.text[:500],
        )

    token = login(
        session
    )

    # ---------------------------------
    # Correct request
    # ---------------------------------

    response = session.get(
        f"{BASE_URL}/v1/analytics/summary",
        headers=headers(token),
        timeout=30,
    )

    print()
    print(
        "=== Authenticated analytics ==="
    )

    print(
        "Status:",
        response.status_code,
    )

    try:
        payload = response.json()
    except ValueError:
        print(
            "Non-JSON response:"
        )
        print(
            response.text[:1000]
        )
        return

    print(
        "Payload type:",
        type(payload).__name__,
    )

    print()
    print(
        "=== RAW PAYLOAD ==="
    )

    print(
        json.dumps(
            payload,
            indent=2,
        )
    )

    if response.status_code != 200:
        return

    if not isinstance(
        payload,
        dict,
    ):
        return

    # ---------------------------------
    # Schema
    # ---------------------------------

    print()
    print(
        "=== SCHEMA CHECK ==="
    )

    expected_fields = {
        "city",
        "total_listings",
        "median_price",
        "median_price_per_sqft",
        "by_locality",
        "by_bhk",
    }

    actual_fields = set(
        payload.keys()
    )

    print(
        "Missing documented fields:",
        sorted(
            expected_fields
            - actual_fields
        ),
    )

    print(
        "Additional fields:",
        sorted(
            actual_fields
            - expected_fields
        ),
    )

    print(
        "city:",
        payload.get("city"),
    )

    print(
        "assigned city:",
        ASSIGNED_CITY,
    )

    print(
        "city matches assigned city "
        "(case-insensitive):",
        (
            isinstance(
                payload.get("city"),
                str,
            )
            and payload["city"]
            .strip()
            .lower()
            == ASSIGNED_CITY
            .strip()
            .lower()
        ),
    )

    # ---------------------------------
    # Total listings
    # ---------------------------------

    print()
    print(
        "=== TOTAL_LISTINGS CHECK ==="
    )

    api_total = payload.get(
        "total_listings"
    )

    print(
        "analytics total_listings:",
        api_total,
    )

    print(
        "retrievable records:",
        len(listings),
    )

    print(
        "verified live records:",
        answers[
            "active_listings"
        ],
    )

    print(
        "collection reported total "
        "observed earlier:",
        3201,
    )

    print(
        "Matches retrievable count:",
        api_total
        == len(listings),
    )

    print(
        "Matches live count:",
        api_total
        == answers[
            "active_listings"
        ],
    )

    print(
        "Matches collection metadata 3201:",
        api_total == 3201,
    )

    # ---------------------------------
    # Candidate median definitions
    # ---------------------------------

    print()
    print(
        "=== MEDIAN CANDIDATE CHECK ==="
    )

    candidates = (
        compute_candidate_metrics(
            listings,
            corrupt_ids,
            fake_ids,
        )
    )

    print(
        "Analytics median_price:",
        payload.get(
            "median_price"
        ),
    )

    print(
        "Analytics median_price_per_sqft:",
        payload.get(
            "median_price_per_sqft"
        ),
    )

    for name, values in (
        candidates.items()
    ):
        print()
        print(
            f"Candidate: {name}"
        )

        print(
            values
        )

        print(
            "median_price exact match:",
            payload.get(
                "median_price"
            )
            == values[
                "median_price"
            ],
        )

        api_ppsf = payload.get(
            "median_price_per_sqft"
        )

        raw_ppsf = values[
            "median_ppsf_raw"
        ]

        normalized_ppsf = values[
            "median_ppsf_normalized"
        ]

        if (
            is_number(api_ppsf)
            and is_number(raw_ppsf)
        ):
            print(
                "median PPSF difference "
                "from raw:",
                round(
                    api_ppsf
                    - raw_ppsf,
                    4,
                ),
            )

        if (
            is_number(api_ppsf)
            and is_number(
                normalized_ppsf
            )
        ):
            print(
                "median PPSF difference "
                "from normalized:",
                round(
                    api_ppsf
                    - normalized_ppsf,
                    4,
                ),
            )

    # ---------------------------------
    # Locality aggregates
    # ---------------------------------

    all_locality = (
        summarize_by_locality(
            listings,
            live_only=False,
        )
    )

    live_locality = (
        summarize_by_locality(
            listings,
            live_only=True,
        )
    )

    print_locality_comparison(
        payload.get(
            "by_locality"
        ),
        all_locality,
        live_locality,
    )

    # ---------------------------------
    # BHK aggregates
    # ---------------------------------

    all_bhk = (
        summarize_by_bhk(
            listings,
            live_only=False,
        )
    )

    live_bhk = (
        summarize_by_bhk(
            listings,
            live_only=True,
        )
    )

    print_bhk_comparison(
        payload.get(
            "by_bhk"
        ),
        all_bhk,
        live_bhk,
    )

    print()
    print(
        "Do not update the audit "
        "or commit yet."
    )

    print(
        "Review which dataset the "
        "analytics endpoint is actually "
        "summarizing."
    )


if __name__ == "__main__":
    main()