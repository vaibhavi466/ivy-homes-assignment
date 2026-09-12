import os
import json

import requests
from dotenv import load_dotenv


load_dotenv()

BASE_URL = os.getenv("IVY_BASE_URL")
API_KEY = os.getenv("IVY_API_KEY")
DEMO_USER = os.getenv("IVY_DEMO_USER_1")
DEMO_PASSWORD = os.getenv("IVY_DEMO_PASSWORD")


def login():
    response = requests.post(
        f"{BASE_URL.rstrip('/')}/auth/login",
        headers={
            "X-API-Key": API_KEY
        },
        json={
            "email": DEMO_USER,
            "password": DEMO_PASSWORD,
        },
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    token = data.get("access_token")

    if not token:
        raise RuntimeError(
            "Login succeeded but access_token was not returned."
        )

    return token


def summarize(label, response):
    print(f"\n=== {label} ===")
    print(f"Status code: {response.status_code}")

    try:
        data = response.json()
    except ValueError:
        print("Non-JSON response:")
        print(response.text[:500])
        return

    if response.status_code >= 400:
        print(json.dumps(data, indent=2))
        return

    print("Top-level keys:", list(data.keys()))

    for key in [
        "limit",
        "offset",
        "count",
        "total",
        "has_more",
        "page",
        "page_size",
    ]:
        if key in data:
            print(f"{key}: {data[key]}")

    results = data.get("results", [])

    print("results length:", len(results))

    ids = [
        item.get("listing_id")
        for item in results
        if item.get("listing_id")
    ]

    if ids:
        print("first ID:", ids[0])
        print("last ID:", ids[-1])


def main():
    token = login()

    url = f"{BASE_URL.rstrip('/')}/v1/listings"

    headers = {
        "X-API-Key": API_KEY,
        "Authorization": f"Bearer {token}",
    }

    tests = [
        (
            "A — No pagination parameters",
            {}
        ),
        (
            "B — Documented page=1, limit=5",
            {
                "page": 1,
                "limit": 5,
            }
        ),
        (
            "C — Documented page=2, limit=5",
            {
                "page": 2,
                "limit": 5,
            }
        ),
        (
            "D — offset=0, limit=5",
            {
                "offset": 0,
                "limit": 5,
            }
        ),
        (
            "E — offset=5, limit=5",
            {
                "offset": 5,
                "limit": 5,
            }
        ),
        (
            "F — offset=10, limit=5",
            {
                "offset": 10,
                "limit": 5,
            }
        ),
        (
            "G — limit=200",
            {
                "limit": 200,
            }
        ),
        (
            "H — limit=201",
            {
                "limit": 201,
            }
        ),
        (
            "I — offset=-1, limit=5",
            {
                "offset": -1,
                "limit": 5,
            }
        ),
    ]

    for label, params in tests:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10,
        )

        summarize(label, response)

        # Determine the collection boundary dynamically.
    baseline_response = requests.get(
        url,
        headers=headers,
        params={
            "offset": 0,
            "limit": 1,
        },
        timeout=10,
    )

    baseline_response.raise_for_status()

    baseline_data = baseline_response.json()

    total = baseline_data["total"]

    print("\n=== Dynamic boundary information ===")
    print(f"Observed total: {total}")

    boundary_tests = [
        (
            "J — 51 records before end, limit=50",
            {
                "offset": max(total - 51, 0),
                "limit": 50,
            },
        ),
        (
            "K — Final record only",
            {
                "offset": max(total - 1, 0),
                "limit": 50,
            },
        ),
        (
            "L — Offset exactly equal to total",
            {
                "offset": total,
                "limit": 50,
            },
        ),
        (
            "M — Offset beyond total",
            {
                "offset": total + 50,
                "limit": 50,
            },
        ),
    ]

    for label, params in boundary_tests:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10,
        )

        summarize(label, response)


if __name__ == "__main__":
    main()