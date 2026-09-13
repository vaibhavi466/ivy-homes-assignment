import json
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()


BASE_URL = os.environ["IVY_BASE_URL"].rstrip("/")
API_KEY = os.environ["IVY_API_KEY"]
EMAIL = os.environ["IVY_DEMO_USER_1"]
PASSWORD = os.environ["IVY_DEMO_PASSWORD"]

LISTINGS_PATH = Path(
    "data/raw/listings.json"
)

SQFT_PER_SQM = 10.7639104167


def load_listings():
    with LISTINGS_PATH.open(
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


def headers(token):
    return {
        "X-API-Key": API_KEY,
        "Authorization":
            f"Bearer {token}",
    }


def request(
    session,
    auth_headers,
    params,
):
    response = session.get(
        f"{BASE_URL}/v1/listings",
        headers=auth_headers,
        params={
            "limit": 50,
            "offset": 0,
            **params,
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


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


def normalized_carpet(
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


def print_filter_check(
    session,
    auth_headers,
    listings,
    name,
    params,
    predicate,
):
    payload = request(
        session,
        auth_headers,
        params,
    )

    local_count = sum(
        predicate(listing)
        for listing in listings
    )

    results = payload[
        "results"
    ]

    returned_mismatches = sum(
        not predicate(listing)
        for listing in results
    )

    print()
    print(
        f"=== FILTER: {name} ==="
    )

    print(
        f"local snapshot matches: "
        f"{local_count}"
    )

    print(
        f"API reported total: "
        f"{payload.get('total')}"
    )

    print(
        "total agrees with snapshot:",
        payload.get("total")
        == local_count,
    )

    print(
        f"returned mismatches: "
        f"{returned_mismatches}"
    )

    print(
        "returned page filtered "
        "correctly:",
        returned_mismatches == 0,
    )


def print_sort_check(
    session,
    auth_headers,
    field,
):
    asc = request(
        session,
        auth_headers,
        {
            "sort_by": field,
            "order": "asc",
        },
    )

    desc = request(
        session,
        auth_headers,
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
        listing["listing_id"]
        for listing
        in asc_results
    ]

    desc_ids = [
        listing["listing_id"]
        for listing
        in desc_results
    ]

    print()
    print(
        "=" * 72
    )

    print(
        f"SORT FIELD: {field}"
    )

    print(
        "=" * 72
    )

    print(
        "ASC and DESC return "
        "identical IDs:",
        asc_ids == desc_ids,
    )

    if field == "carpet_area":
        asc_raw = [
            listing.get(
                "carpet_area"
            )
            for listing
            in asc_results
        ]

        desc_raw = [
            listing.get(
                "carpet_area"
            )
            for listing
            in desc_results
        ]

        asc_normalized = [
            normalized_carpet(
                listing
            )
            for listing
            in asc_results
        ]

        desc_normalized = [
            normalized_carpet(
                listing
            )
            for listing
            in desc_results
        ]

        print(
            "ASC raw monotonic:",
            monotonic(
                asc_raw
            ),
        )

        print(
            "ASC normalized monotonic:",
            monotonic(
                asc_normalized
            ),
        )

        print(
            "DESC raw monotonic:",
            monotonic(
                desc_raw,
                descending=True,
            ),
        )

        print(
            "DESC normalized monotonic:",
            monotonic(
                desc_normalized,
                descending=True,
            ),
        )

        print(
            "ASC first 15 raw:"
        )

        print(
            asc_raw[:15]
        )

        print(
            "ASC first 15 normalized:"
        )

        print(
            [
                round(value, 2)
                if value is not None
                else None
                for value
                in asc_normalized[:15]
            ]
        )

        return

    if field == "posted_at":
        asc_values = [
            listing.get(
                "posted_at"
            )
            for listing
            in asc_results
        ]

        desc_values = [
            listing.get(
                "posted_at"
            )
            for listing
            in desc_results
        ]

        asc_datetimes = [
            datetime.fromisoformat(
                value
            )
            if value
            else None
            for value
            in asc_values
        ]

        desc_datetimes = [
            datetime.fromisoformat(
                value
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
            in asc_datetimes
        ]

        desc_dates = [
            value.date()
            if value
            else None
            for value
            in desc_datetimes
        ]

        print(
            "ASC full timestamp "
            "monotonic:",
            monotonic(
                asc_datetimes
            ),
        )

        print(
            "ASC date-only monotonic:",
            monotonic(
                asc_dates
            ),
        )

        print(
            "DESC full timestamp "
            "monotonic:",
            monotonic(
                desc_datetimes,
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

        return

    asc_values = [
        listing.get(field)
        for listing
        in asc_results
    ]

    desc_values = [
        listing.get(field)
        for listing
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
    listings = load_listings()

    session = requests.Session()

    token = login(
        session
    )

    auth_headers = headers(
        token
    )

    print(
        "=== Listing Filter/Sorting "
        "Verification ==="
    )

    print(
        f"Complete snapshot: "
        f"{len(listings)}"
    )

    # ---------------------------------
    # Exact filtered-total verification
    # ---------------------------------

    checks = [
        (
            "locality=sector 65",
            {
                "locality":
                    "sector 65",
            },
            lambda item:
                item.get("locality")
                == "sector 65",
        ),
        (
            "locality=dwarka expressway",
            {
                "locality":
                    "dwarka expressway",
            },
            lambda item:
                item.get("locality")
                == "dwarka expressway",
        ),
        (
            "bhk=3",
            {
                "bhk": 3,
            },
            lambda item:
                item.get("bedroom")
                == 3,
        ),
        (
            "bhk=2",
            {
                "bhk": 2,
            },
            lambda item:
                item.get("bedroom")
                == 2,
        ),
        (
            "property_type=apartment",
            {
                "property_type":
                    "apartment",
            },
            lambda item:
                item.get(
                    "property_type"
                )
                == "apartment",
        ),
        (
            "furnishing=fully-furnished",
            {
                "furnishing":
                    "fully-furnished",
            },
            lambda item:
                item.get(
                    "furnishing"
                )
                == "fully-furnished",
        ),
        (
            "min_price=12420000",
            {
                "min_price":
                    12420000,
            },
            lambda item:
                is_number(
                    item.get("price")
                )
                and item["price"]
                >= 12420000,
        ),
        (
            "max_price=17700000",
            {
                "max_price":
                    17700000,
            },
            lambda item:
                is_number(
                    item.get("price")
                )
                and item["price"]
                <= 17700000,
        ),
    ]

    for (
        name,
        params,
        predicate,
    ) in checks:
        print_filter_check(
            session,
            auth_headers,
            listings,
            name,
            params,
            predicate,
        )

    # ---------------------------------
    # One combined-filter test
    # ---------------------------------

    print_filter_check(
        session,
        auth_headers,
        listings,
        (
            "combined: sector 65 + "
            "3 BHK + fully-furnished"
        ),
        {
            "locality":
                "sector 65",
            "bhk":
                3,
            "furnishing":
                "fully-furnished",
        },
        lambda item:
            (
                item.get("locality")
                == "sector 65"
                and item.get(
                    "bedroom"
                )
                == 3
                and item.get(
                    "furnishing"
                )
                == "fully-furnished"
            ),
    )

    # ---------------------------------
    # Sorting verification
    # ---------------------------------

    for field in [
        "price",
        "carpet_area",
        "posted_at",
        "bedroom",
    ]:
        print_sort_check(
            session,
            auth_headers,
            field,
        )

    print()
    print(
        "Review before updating "
        "documentation-audit.md."
    )


if __name__ == "__main__":
    main()