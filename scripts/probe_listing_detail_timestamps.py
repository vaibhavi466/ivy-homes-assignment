import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()

BASE_URL = os.getenv("IVY_BASE_URL")
API_KEY = os.getenv("IVY_API_KEY")
DEMO_USER = os.getenv("IVY_DEMO_USER_1")
DEMO_PASSWORD = os.getenv("IVY_DEMO_PASSWORD")

LISTINGS_PATH = Path("data/raw/listings.json")

IST = timezone(
    timedelta(
        hours=5,
        minutes=30,
    )
)

UTC = timezone.utc

REFERENCE = datetime.fromisoformat(
    "2026-09-10T00:00:00+05:30"
)

WINDOW_START = REFERENCE - timedelta(days=7)
WINDOW_END = REFERENCE


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

    token = data.get("access_token")

    if not token:
        raise RuntimeError(
            "Login succeeded but access_token "
            "was not returned."
        )

    return token


def load_listings():
    with LISTINGS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["results"]


def parse_naive(value):
    parsed = datetime.fromisoformat(
        value
    )

    if parsed.tzinfo is not None:
        raise RuntimeError(
            f"Expected naive timestamp: {value}"
        )

    return parsed


def qualifies(
    naive,
    assumed_timezone,
):
    aware = naive.replace(
        tzinfo=assumed_timezone
    )

    return (
        WINDOW_START
        <= aware
        < WINDOW_END
    )


def timestamp_style(value):
    if not isinstance(value, str):
        return "non-string"

    if value.endswith("Z"):
        return "UTC-Z"

    if (
        "+" in value[10:]
        or "-" in value[10:]
    ):
        return "explicit-offset"

    return "no-explicit-timezone"


def main():
    listings = load_listings()

    by_id = {
        listing["listing_id"]: listing
        for listing in listings
    }

    only_ist = []
    only_utc = []

    for listing in listings:
        listing_id = listing["listing_id"]

        raw = listing.get(
            "posted_at"
        )

        naive = parse_naive(raw)

        ist_match = qualifies(
            naive,
            IST,
        )

        utc_match = qualifies(
            naive,
            UTC,
        )

        if (
            ist_match
            and not utc_match
        ):
            only_ist.append(
                listing_id
            )

        if (
            utc_match
            and not ist_match
        ):
            only_utc.append(
                listing_id
            )

    sample_ids = (
        only_ist[:6]
        + only_utc[:2]
    )

    print(
        "=== Listing Detail Timestamp Probe ==="
    )

    print(
        f"Only-IST candidates: "
        f"{len(only_ist)}"
    )

    print(
        f"Only-UTC candidates: "
        f"{len(only_utc)}"
    )

    print(
        f"Detail records to probe: "
        f"{len(sample_ids)}"
    )

    session = requests.Session()

    token = login(session)

    headers = {
        "X-API-Key": API_KEY,
        "Authorization": (
            f"Bearer {token}"
        ),
    }

    for listing_id in sample_ids:
        collection_record = by_id[
            listing_id
        ]

        collection_posted_at = (
            collection_record.get(
                "posted_at"
            )
        )

        url = (
            f"{BASE_URL.rstrip('/')}"
            f"/v1/listing/{listing_id}"
        )

        response = session.get(
            url,
            headers=headers,
            timeout=20,
        )

        print()
        print("=" * 60)
        print(
            f"Listing ID: {listing_id}"
        )

        print(
            f"Status code: "
            f"{response.status_code}"
        )

        print(
            "Collection posted_at: "
            f"{collection_posted_at}"
        )

        if response.status_code != 200:
            try:
                print(
                    "Response:",
                    response.json(),
                )
            except ValueError:
                print(
                    "Response:",
                    response.text[:300],
                )

            continue

        detail = response.json()

        detail_posted_at = detail.get(
            "posted_at"
        )

        print(
            "Detail posted_at: "
            f"{detail_posted_at}"
        )

        print(
            "Detail timestamp style: "
            f"{timestamp_style(detail_posted_at)}"
        )

        print(
            "Collection == detail: "
            f"{collection_posted_at == detail_posted_at}"
        )

        print(
            "Detail keys:"
        )

        print(
            sorted(
                detail.keys()
            )
        )


if __name__ == "__main__":
    main()