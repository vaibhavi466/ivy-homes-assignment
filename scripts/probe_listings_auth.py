import os
import json

import requests
from dotenv import load_dotenv


load_dotenv()

BASE_URL = os.getenv("IVY_BASE_URL")
API_KEY = os.getenv("IVY_API_KEY")
DEMO_USER = os.getenv("IVY_DEMO_USER_1")
DEMO_PASSWORD = os.getenv("IVY_DEMO_PASSWORD")


def summarize_response(label, response):
    print(f"\n=== {label} ===")
    print(f"Status code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', '')}")

    try:
        data = response.json()

        # For errors, print the useful error body.
        if response.status_code >= 400:
            print("Response:")
            print(json.dumps(data, indent=2))
            return

        print("Top-level keys:", list(data.keys()))

        if "total" in data:
            print("total:", data["total"])

        if "page" in data:
            print("page:", data["page"])

        if "page_size" in data:
            print("page_size:", data["page_size"])

        results = data.get("results")

        if isinstance(results, list):
            print("results returned:", len(results))

            if results:
                first = results[0]

                print(
                    "first listing_id:",
                    first.get("listing_id", "<missing>")
                )

    except ValueError:
        print("Non-JSON response:")
        print(response.text[:500])


def login():
    url = f"{BASE_URL.rstrip('/')}/auth/login"

    response = requests.post(
        url,
        headers={"X-API-Key": API_KEY},
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


def main():
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

    print("=== Ivy Homes Listings Authentication Probe ===")
    print("Secrets and tokens will not be printed.")

    access_token = login()

    url = f"{BASE_URL.rstrip('/')}/v1/listings"

    bearer_header = {
        "Authorization": f"Bearer {access_token}"
    }

    api_key_header = {
        "X-API-Key": API_KEY
    }

    both_headers = {
        "X-API-Key": API_KEY,
        "Authorization": f"Bearer {access_token}",
    }

    # A — no API key, no Bearer token
    response = requests.get(
        url,
        timeout=10,
    )

    summarize_response(
        "A — No API key, no Bearer token",
        response,
    )

    # B — documented query-parameter API key only
    response = requests.get(
        url,
        params={"api_key": API_KEY},
        timeout=10,
    )

    summarize_response(
        "B — Query-parameter API key only",
        response,
    )

    # C — observed X-API-Key header only
    response = requests.get(
        url,
        headers=api_key_header,
        timeout=10,
    )

    summarize_response(
        "C — X-API-Key header only",
        response,
    )

    # D — Bearer token only
    response = requests.get(
        url,
        headers=bearer_header,
        timeout=10,
    )

    summarize_response(
        "D — Bearer token only",
        response,
    )

    # E — documented query-parameter API key + Bearer token
    response = requests.get(
        url,
        params={"api_key": API_KEY},
        headers=bearer_header,
        timeout=10,
    )

    summarize_response(
        "E — Query-parameter API key + Bearer token",
        response,
    )

    # F — observed X-API-Key + Bearer token
    response = requests.get(
        url,
        headers=both_headers,
        timeout=10,
    )

    summarize_response(
        "F — X-API-Key header + Bearer token",
        response,
    )


if __name__ == "__main__":
    main()