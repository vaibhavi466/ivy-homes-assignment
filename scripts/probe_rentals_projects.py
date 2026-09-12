import json
import os

import requests
from dotenv import load_dotenv


load_dotenv()

BASE_URL = os.getenv("IVY_BASE_URL")
API_KEY = os.getenv("IVY_API_KEY")
DEMO_USER = os.getenv("IVY_DEMO_USER_1")
DEMO_PASSWORD = os.getenv("IVY_DEMO_PASSWORD")


def validate_environment():
    required = {
        "IVY_BASE_URL": BASE_URL,
        "IVY_API_KEY": API_KEY,
        "IVY_DEMO_USER_1": DEMO_USER,
        "IVY_DEMO_PASSWORD": DEMO_PASSWORD,
    }

    missing = [
        name
        for name, value in required.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}"
        )


def login(session):
    response = session.post(
        f"{BASE_URL.rstrip('/')}/auth/login",
        headers={
            "X-API-Key": API_KEY,
        },
        json={
            "email": DEMO_USER,
            "password": DEMO_PASSWORD,
        },
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    access_token = data.get("access_token")

    if not access_token:
        raise RuntimeError(
            "Login succeeded but access_token was not returned."
        )

    return access_token


def summarize(label, response, id_field):
    print(f"\n=== {label} ===")
    print(f"Status code: {response.status_code}")
    print(
        "Content-Type:",
        response.headers.get("content-type", "")
    )

    try:
        data = response.json()
    except ValueError:
        print("Non-JSON response:")
        print(response.text[:500])
        return

    if response.status_code >= 400:
        print("Response:")
        print(json.dumps(data, indent=2))
        return

    print(
        "Top-level keys:",
        list(data.keys())
    )

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
            print(
                f"{key}: {data[key]}"
            )

    results = data.get("results", [])

    if not isinstance(results, list):
        print(
            "WARNING: results is not a list."
        )
        return

    print(
        "results length:",
        len(results)
    )

    if results:
        first = results[0]

        print(
            "first record ID:",
            first.get(id_field, "<missing>")
        )

        print(
            "first record keys:",
            sorted(first.keys())
        )

        # Print only a safe subset of fields.
        safe_fields = {}

        for key in [
            id_field,
            "locality",
            "bedroom",
            "furnishing",
            "price",
            "carpet_area",
            "super_built_up_area",
            "super_builtup_area",
            "project_id",
            "price_min",
            "price_max",
            "min_area_sqft",
            "max_area_sqft",
            "total_listings",
            "project_status",
        ]:
            if key in first:
                safe_fields[key] = first[key]

        print(
            "safe sample fields:"
        )
        print(
            json.dumps(
                safe_fields,
                indent=2
            )
        )


def probe_endpoint(
    session,
    endpoint,
    id_field,
    headers,
):
    url = (
        f"{BASE_URL.rstrip('/')}"
        f"{endpoint}"
    )

    print("\n")
    print("=" * 70)
    print(
        f"PROBING {endpoint}"
    )
    print("=" * 70)

    # A — No authentication
    response = session.get(
        url,
        timeout=20,
    )

    summarize(
        "A — No credentials",
        response,
        id_field,
    )

    # B — X-API-Key only
    response = session.get(
        url,
        headers={
            "X-API-Key": API_KEY,
        },
        timeout=20,
    )

    summarize(
        "B — X-API-Key only",
        response,
        id_field,
    )

    # C — Correct observed credentials
    response = session.get(
        url,
        headers=headers,
        timeout=20,
    )

    summarize(
        "C — X-API-Key + Bearer, no pagination params",
        response,
        id_field,
    )

    # D — Documented page mechanism
    response = session.get(
        url,
        headers=headers,
        params={
            "page": 2,
            "limit": 5,
        },
        timeout=20,
    )

    summarize(
        "D — page=2, limit=5",
        response,
        id_field,
    )

    # E — offset mechanism
    response = session.get(
        url,
        headers=headers,
        params={
            "offset": 5,
            "limit": 5,
        },
        timeout=20,
    )

    summarize(
        "E — offset=5, limit=5",
        response,
        id_field,
    )

    # F — documented large limit
    response = session.get(
        url,
        headers=headers,
        params={
            "limit": 200,
        },
        timeout=20,
    )

    summarize(
        "F — limit=200",
        response,
        id_field,
    )


def main():
    validate_environment()

    session = requests.Session()

    access_token = login(session)

    headers = {
        "X-API-Key": API_KEY,
        "Authorization": (
            f"Bearer {access_token}"
        ),
    }

    print(
        "=== Ivy Homes Rentals & Projects Probe ==="
    )
    print(
        "Secrets, tokens, passwords, and seller "
        "contact data will not be printed."
    )

    probe_endpoint(
        session=session,
        endpoint="/v1/rentals",
        id_field="listing_id",
        headers=headers,
    )

    probe_endpoint(
        session=session,
        endpoint="/v1/projects",
        id_field="project_id",
        headers=headers,
    )


if __name__ == "__main__":
    main()