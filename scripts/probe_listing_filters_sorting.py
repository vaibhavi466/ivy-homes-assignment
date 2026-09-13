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

LISTINGS_PATH = Path(
    "data/raw/listings.json"
)


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


def make_headers(token):
    return {
        "X-API-Key": API_KEY,
        "Authorization":
            f"Bearer {token}",
    }


def request_listings(
    session,
    headers,
    params,
):
    request_params = {
        "limit": 50,
        "offset": 0,
        **params,
    }

    response = session.get(
        f"{BASE_URL}/v1/listings",
        headers=headers,
        params=request_params,
        timeout=30,
    )

    print()
    print(
        "Request params:",
        request_params,
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
            response.text[:500]
        )
        return None

    if response.status_code != 200:
        print(
            json.dumps(
                payload,
                indent=2,
            )
        )
        return None

    print(
        "Response metadata:",
        {
            "limit":
                payload.get("limit"),
            "offset":
                payload.get("offset"),
            "count":
                payload.get("count"),
            "total":
                payload.get("total"),
            "has_more":
                payload.get(
                    "has_more"
                ),
        },
    )

    return payload


def show_filter_result(
    label,
    payload,
    predicate,
):
    print()
    print(
        f"=== {label} ==="
    )

    if payload is None:
        return

    results = payload.get(
        "results",
        [],
    )

    mismatches = [
        listing
        for listing in results
        if not predicate(listing)
    ]

    print(
        f"Returned records: "
        f"{len(results)}"
    )

    print(
        f"Mismatching records: "
        f"{len(mismatches)}"
    )

    print(
        "Filter honored on "
        "returned page:",
        len(mismatches) == 0,
    )

    if mismatches:
        print(
            "First 10 mismatching IDs:"
        )

        for listing in (
            mismatches[:10]
        ):
            print(
                listing.get(
                    "listing_id"
                )
            )


def show_sort_result(
    label,
    payload,
    field,
    descending,
):
    print()
    print(
        f"=== {label} ==="
    )

    if payload is None:
        return

    results = payload.get(
        "results",
        [],
    )

    values = [
        listing.get(field)
        for listing in results
    ]

    missing = sum(
        value is None
        for value in values
    )

    comparable = [
        value
        for value in values
        if value is not None
    ]

    if descending:
        correct = all(
            left >= right
            for left, right
            in zip(
                comparable,
                comparable[1:],
            )
        )
    else:
        correct = all(
            left <= right
            for left, right
            in zip(
                comparable,
                comparable[1:],
            )
        )

    print(
        f"Returned records: "
        f"{len(results)}"
    )

    print(
        f"Missing {field}: "
        f"{missing}"
    )

    print(
        "Sorted correctly on "
        "returned page:",
        correct,
    )

    print(
        "First 10 values:"
    )

    print(
        comparable[:10]
    )

    print(
        "First 10 listing IDs:"
    )

    print(
        [
            listing.get(
                "listing_id"
            )
            for listing
            in results[:10]
        ]
    )


def main():
    listings = load_listings()

    print(
        "=== Listing Filter & "
        "Sorting Contract Probe ==="
    )

    print(
        f"Local snapshot records: "
        f"{len(listings)}"
    )

    # ---------------------------------
    # Choose real values from snapshot
    # ---------------------------------

    localities = Counter(
        listing.get("locality")
        for listing in listings
        if listing.get("locality")
    ).most_common(2)

    bedrooms = Counter(
        listing.get("bedroom")
        for listing in listings
        if isinstance(
            listing.get("bedroom"),
            int,
        )
    ).most_common(2)

    property_types = Counter(
        listing.get(
            "property_type"
        )
        for listing in listings
        if listing.get(
            "property_type"
        )
    ).most_common(1)

    furnishings = Counter(
        listing.get("furnishing")
        for listing in listings
        if listing.get("furnishing")
    ).most_common(1)

    positive_prices = sorted(
        listing["price"]
        for listing in listings
        if (
            isinstance(
                listing.get("price"),
                (int, float),
            )
            and not isinstance(
                listing.get("price"),
                bool,
            )
            and listing["price"] > 0
        )
    )

    lower_price = positive_prices[
        len(positive_prices) // 3
    ]

    upper_price = positive_prices[
        (
            len(positive_prices)
            * 2
        )
        // 3
    ]

    locality_a = localities[0][0]
    locality_b = localities[1][0]

    bhk_a = bedrooms[0][0]
    bhk_b = bedrooms[1][0]

    property_type = (
        property_types[0][0]
    )

    furnishing = (
        furnishings[0][0]
    )

    print()
    print(
        "=== Probe Values ==="
    )

    print(
        f"locality A: "
        f"{locality_a}"
    )

    print(
        f"locality B: "
        f"{locality_b}"
    )

    print(
        f"BHK A: {bhk_a}"
    )

    print(
        f"BHK B: {bhk_b}"
    )

    print(
        f"property_type: "
        f"{property_type}"
    )

    print(
        f"furnishing: "
        f"{furnishing}"
    )

    print(
        f"min_price probe: "
        f"{lower_price}"
    )

    print(
        f"max_price probe: "
        f"{upper_price}"
    )

    session = requests.Session()

    token = login(
        session
    )

    headers = make_headers(
        token
    )

    # ---------------------------------
    # FILTERS
    # ---------------------------------

    payload = request_listings(
        session,
        headers,
        {
            "locality":
                locality_a,
        },
    )

    show_filter_result(
        f"locality={locality_a}",
        payload,
        lambda listing:
            listing.get(
                "locality"
            )
            == locality_a,
    )

    payload = request_listings(
        session,
        headers,
        {
            "locality":
                locality_b,
        },
    )

    show_filter_result(
        f"locality={locality_b}",
        payload,
        lambda listing:
            listing.get(
                "locality"
            )
            == locality_b,
    )

    payload = request_listings(
        session,
        headers,
        {
            "bhk": bhk_a,
        },
    )

    show_filter_result(
        f"bhk={bhk_a}",
        payload,
        lambda listing:
            listing.get(
                "bedroom"
            )
            == bhk_a,
    )

    payload = request_listings(
        session,
        headers,
        {
            "bhk": bhk_b,
        },
    )

    show_filter_result(
        f"bhk={bhk_b}",
        payload,
        lambda listing:
            listing.get(
                "bedroom"
            )
            == bhk_b,
    )

    payload = request_listings(
        session,
        headers,
        {
            "property_type":
                property_type,
        },
    )

    show_filter_result(
        "property_type="
        f"{property_type}",
        payload,
        lambda listing:
            listing.get(
                "property_type"
            )
            == property_type,
    )

    payload = request_listings(
        session,
        headers,
        {
            "furnishing":
                furnishing,
        },
    )

    show_filter_result(
        f"furnishing={furnishing}",
        payload,
        lambda listing:
            listing.get(
                "furnishing"
            )
            == furnishing,
    )

    payload = request_listings(
        session,
        headers,
        {
            "min_price":
                lower_price,
        },
    )

    show_filter_result(
        f"min_price={lower_price}",
        payload,
        lambda listing:
            (
                isinstance(
                    listing.get(
                        "price"
                    ),
                    (int, float),
                )
                and listing[
                    "price"
                ]
                >= lower_price
            ),
    )

    payload = request_listings(
        session,
        headers,
        {
            "max_price":
                upper_price,
        },
    )

    show_filter_result(
        f"max_price={upper_price}",
        payload,
        lambda listing:
            (
                isinstance(
                    listing.get(
                        "price"
                    ),
                    (int, float),
                )
                and listing[
                    "price"
                ]
                <= upper_price
            ),
    )

    # ---------------------------------
    # SORTING
    # ---------------------------------

    sort_fields = [
        "price",
        "carpet_area",
        "posted_at",
        "bedroom",
    ]

    for field in sort_fields:
        payload = request_listings(
            session,
            headers,
            {
                "sort_by":
                    field,
                "order":
                    "asc",
            },
        )

        show_sort_result(
            f"{field} ASC",
            payload,
            field,
            descending=False,
        )

        payload = request_listings(
            session,
            headers,
            {
                "sort_by":
                    field,
                "order":
                    "desc",
            },
        )

        show_sort_result(
            f"{field} DESC",
            payload,
            field,
            descending=True,
        )

    print()
    print(
        "Do not update the audit "
        "statuses yet."
    )

    print(
        "Review the output first."
    )


if __name__ == "__main__":
    main()