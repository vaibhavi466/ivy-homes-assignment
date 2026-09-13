import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()


BASE_URL = os.environ["IVY_BASE_URL"].rstrip("/")
API_KEY = os.environ["IVY_API_KEY"]
EMAIL = os.environ["IVY_DEMO_USER_1"]
PASSWORD = os.environ["IVY_DEMO_PASSWORD"]

RENTALS_PATH = Path(
    "data/raw/rentals.json"
)


DOCUMENTED_FIELDS = {
    "listing_id",
    "listing_url",
    "website",
    "city_id",
    "title",
    "apartment_name",
    "locality",
    "property_type",
    "bedroom",
    "bathroom",
    "floor",
    "total_floors",
    "furnishing",
    "facing_direction",
    "price",
    "deposit",
    "maintenance",
    "carpet_area",
    "super_builtup_area",
    "latitude",
    "longitude",
    "posted_by",
    "posted_by_name",
    "posted_by_contact",
    "description",
    "posted_at",
}


def load_rentals():
    with RENTALS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["results"]


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


def make_headers(token):
    return {
        "X-API-Key": API_KEY,
        "Authorization":
            f"Bearer {token}",
    }


def request_rentals(
    session,
    headers,
    params,
):
    response = session.get(
        f"{BASE_URL}/v1/rentals",
        headers=headers,
        params={
            "limit": 50,
            "offset": 0,
            **params,
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def monotonic(
    values,
    descending=False,
):
    values = [
        value
        for value in values
        if value is not None
    ]

    if descending:
        return all(
            left >= right
            for left, right
            in zip(
                values,
                values[1:],
            )
        )

    return all(
        left <= right
        for left, right
        in zip(
            values,
            values[1:],
        )
    )


def filter_check(
    session,
    headers,
    rentals,
    name,
    params,
    predicate,
):
    payload = request_rentals(
        session,
        headers,
        params,
    )

    local_count = sum(
        predicate(rental)
        for rental in rentals
    )

    results = payload.get(
        "results",
        [],
    )

    mismatches = [
        rental
        for rental in results
        if not predicate(rental)
    ]

    print()
    print(
        f"=== FILTER: {name} ==="
    )

    print(
        "Local snapshot matches:",
        local_count,
    )

    print(
        "API reported total:",
        payload.get("total"),
    )

    print(
        "Total agrees with snapshot:",
        payload.get("total")
        == local_count,
    )

    print(
        "Returned records:",
        len(results),
    )

    print(
        "Returned mismatches:",
        len(mismatches),
    )

    print(
        "Filter honored:",
        len(mismatches) == 0,
    )

    if mismatches:
        print(
            "First 10 mismatch IDs:"
        )

        print(
            [
                rental.get(
                    "listing_id"
                )
                for rental
                in mismatches[:10]
            ]
        )


def sort_check(
    session,
    headers,
    field,
):
    asc = request_rentals(
        session,
        headers,
        {
            "sort_by": field,
            "order": "asc",
        },
    )

    desc = request_rentals(
        session,
        headers,
        {
            "sort_by": field,
            "order": "desc",
        },
    )

    asc_results = asc[
        "results"
    ]

    desc_results = desc[
        "results"
    ]

    asc_ids = [
        rental["listing_id"]
        for rental
        in asc_results
    ]

    desc_ids = [
        rental["listing_id"]
        for rental
        in desc_results
    ]

    print()
    print(
        "=" * 72
    )

    print(
        f"SORT: {field}"
    )

    print(
        "=" * 72
    )

    print(
        "ASC and DESC identical IDs:",
        asc_ids == desc_ids,
    )

    if field == "posted_at":
        asc_values = [
            rental.get(
                "posted_at"
            )
            for rental
            in asc_results
        ]

        desc_values = [
            rental.get(
                "posted_at"
            )
            for rental
            in desc_results
        ]

        asc_dt = [
            datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )
            if value
            else None
            for value
            in asc_values
        ]

        desc_dt = [
            datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )
            if value
            else None
            for value
            in desc_values
        ]

        asc_dates = [
            value.date()
            if value
            else None
            for value
            in asc_dt
        ]

        desc_dates = [
            value.date()
            if value
            else None
            for value
            in desc_dt
        ]

        print(
            "ASC full timestamp monotonic:",
            monotonic(
                asc_dt
            ),
        )

        print(
            "ASC date-only monotonic:",
            monotonic(
                asc_dates
            ),
        )

        print(
            "DESC full timestamp monotonic:",
            monotonic(
                desc_dt,
                descending=True,
            ),
        )

        print(
            "DESC date-only monotonic:",
            monotonic(
                desc_dates,
                descending=True,
            ),
        )

        print(
            "ASC first 15:"
        )

        print(
            asc_values[:15]
        )

        print(
            "DESC first 15:"
        )

        print(
            desc_values[:15]
        )

        return

    asc_values = [
        rental.get(field)
        for rental
        in asc_results
    ]

    desc_values = [
        rental.get(field)
        for rental
        in desc_results
    ]

    print(
        "ASC monotonic:",
        monotonic(
            asc_values
        ),
    )

    print(
        "DESC monotonic:",
        monotonic(
            desc_values,
            descending=True,
        ),
    )

    print(
        "ASC first 15:"
    )

    print(
        asc_values[:15]
    )

    print(
        "DESC first 15:"
    )

    print(
        desc_values[:15]
    )


def main():
    rentals = load_rentals()

    print(
        "=== Rental API Contract Probe ==="
    )

    print(
        "Complete local snapshot:",
        len(rentals),
    )

    # ---------------------------------
    # Snapshot contract
    # ---------------------------------

    print()
    print(
        "=== FIELD CONTRACT ==="
    )

    all_fields = set()

    records_missing_documented = []

    for rental in rentals:
        all_fields.update(
            rental.keys()
        )

        missing = (
            DOCUMENTED_FIELDS
            - set(
                rental.keys()
            )
        )

        if missing:
            records_missing_documented.append(
                (
                    rental[
                        "listing_id"
                    ],
                    sorted(missing),
                )
            )

    print(
        "Fields observed:"
    )

    print(
        sorted(all_fields)
    )

    print(
        "Documented fields absent "
        "from every record:"
    )

    print(
        sorted(
            DOCUMENTED_FIELDS
            - all_fields
        )
    )

    print(
        "Records missing one or more "
        "documented fields:",
        len(
            records_missing_documented
        ),
    )

    if records_missing_documented:
        print(
            "First 10:"
        )

        for item in (
            records_missing_documented[:10]
        ):
            print(item)

    undocumented_fields = (
        all_fields
        - DOCUMENTED_FIELDS
    )

    print(
        "Additional observed fields:"
    )

    print(
        sorted(
            undocumented_fields
        )
    )

    # ---------------------------------
    # Money validation
    # ---------------------------------

    print()
    print(
        "=== MONEY FIELDS ==="
    )

    for field in [
        "price",
        "deposit",
        "maintenance",
    ]:
        values = [
            rental.get(field)
            for rental in rentals
        ]

        non_numeric = [
            rental["listing_id"]
            for rental in rentals
            if not isinstance(
                rental.get(field),
                (int, float),
            )
            or isinstance(
                rental.get(field),
                bool,
            )
        ]

        negative = [
            rental["listing_id"]
            for rental in rentals
            if isinstance(
                rental.get(field),
                (int, float),
            )
            and not isinstance(
                rental.get(field),
                bool,
            )
            and rental[field] < 0
        ]

        numeric_values = [
            value
            for value in values
            if isinstance(
                value,
                (int, float),
            )
            and not isinstance(
                value,
                bool,
            )
        ]

        print()
        print(
            f"{field}:"
        )

        print(
            "non-numeric:",
            len(non_numeric),
        )

        print(
            "negative:",
            len(negative),
        )

        if numeric_values:
            print(
                "min:",
                min(
                    numeric_values
                ),
            )

            print(
                "max:",
                max(
                    numeric_values
                ),
            )

    # ---------------------------------
    # String convention
    # ---------------------------------

    print()
    print(
        "=== LOWERCASE STRING CONTRACT ==="
    )

    for field in [
        "locality",
        "furnishing",
        "property_type",
    ]:
        violations = [
            rental[
                "listing_id"
            ]
            for rental in rentals
            if (
                isinstance(
                    rental.get(field),
                    str,
                )
                and rental[field]
                != rental[field].lower()
            )
        ]

        print(
            f"{field} uppercase/mixed-case "
            f"violations: "
            f"{len(violations)}"
        )

        if violations:
            print(
                violations[:20]
            )

    # ---------------------------------
    # Timestamp convention
    # ---------------------------------

    print()
    print(
        "=== TIMESTAMP CONTRACT ==="
    )

    posted_values = [
        rental.get(
            "posted_at"
        )
        for rental in rentals
    ]

    missing_timestamps = sum(
        value is None
        for value in posted_values
    )

    z_suffix = sum(
        isinstance(
            value,
            str,
        )
        and value.endswith("Z")
        for value in posted_values
    )

    explicit_offset = sum(
        isinstance(
            value,
            str,
        )
        and (
            value.endswith("Z")
            or (
                len(value) >= 6
                and value[-6] in (
                    "+",
                    "-",
                )
                and value[-3] == ":"
            )
        )
        for value in posted_values
    )

    print(
        "Missing posted_at:",
        missing_timestamps,
    )

    print(
        "UTC Z suffix:",
        z_suffix,
    )

    print(
        "Any explicit timezone:",
        explicit_offset,
    )

    print(
        "First 10 timestamps:"
    )

    print(
        posted_values[:10]
    )

    # ---------------------------------
    # Choose common filter values
    # ---------------------------------

    locality_counts = Counter(
        rental.get(
            "locality"
        )
        for rental in rentals
        if rental.get(
            "locality"
        )
    )

    bedroom_counts = Counter(
        rental.get(
            "bedroom"
        )
        for rental in rentals
        if isinstance(
            rental.get(
                "bedroom"
            ),
            int,
        )
    )

    furnishing_counts = Counter(
        rental.get(
            "furnishing"
        )
        for rental in rentals
        if rental.get(
            "furnishing"
        )
    )

    localities = [
        item[0]
        for item
        in locality_counts.most_common(
            2
        )
    ]

    bedrooms = [
        item[0]
        for item
        in bedroom_counts.most_common(
            2
        )
    ]

    furnishing = (
        furnishing_counts
        .most_common(1)[0][0]
    )

    print()
    print(
        "=== FILTER PROBE VALUES ==="
    )

    print(
        "localities:",
        localities,
    )

    print(
        "bedrooms:",
        bedrooms,
    )

    print(
        "furnishing:",
        furnishing,
    )

    session = requests.Session()

    token = login(
        session
    )

    auth_headers = make_headers(
        token
    )

    # ---------------------------------
    # Filters
    # ---------------------------------

    for locality in localities:
        filter_check(
            session,
            auth_headers,
            rentals,
            f"locality={locality}",
            {
                "locality":
                    locality,
            },
            lambda rental,
            locality=locality:
                rental.get(
                    "locality"
                )
                == locality,
        )

    for bedroom in bedrooms:
        filter_check(
            session,
            auth_headers,
            rentals,
            f"bhk={bedroom}",
            {
                "bhk":
                    bedroom,
            },
            lambda rental,
            bedroom=bedroom:
                rental.get(
                    "bedroom"
                )
                == bedroom,
        )

    filter_check(
        session,
        auth_headers,
        rentals,
        (
            "furnishing="
            f"{furnishing}"
        ),
        {
            "furnishing":
                furnishing,
        },
        lambda rental:
            rental.get(
                "furnishing"
            )
            == furnishing,
    )

    filter_check(
        session,
        auth_headers,
        rentals,
        "combined filter",
        {
            "locality":
                localities[0],
            "bhk":
                bedrooms[0],
            "furnishing":
                furnishing,
        },
        lambda rental:
            (
                rental.get(
                    "locality"
                )
                == localities[0]
                and rental.get(
                    "bedroom"
                )
                == bedrooms[0]
                and rental.get(
                    "furnishing"
                )
                == furnishing
            ),
    )

    # ---------------------------------
    # Sorting
    # ---------------------------------

    # The rental docs say sort_by/order
    # are supported but do not enumerate
    # allowed sort fields. Probe common,
    # meaningful rental fields without
    # treating a failure as a finding
    # until the behavior is reviewed.
    for field in [
        "price",
        "bedroom",
        "posted_at",
    ]:
        sort_check(
            session,
            auth_headers,
            field,
        )

    print()
    print(
        "Do not update the audit yet."
    )

    print(
        "Review all results first."
    )


if __name__ == "__main__":
    main()