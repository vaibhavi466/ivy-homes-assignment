import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()

BASE_URL = os.getenv("IVY_BASE_URL")
API_KEY = os.getenv("IVY_API_KEY")
DEMO_USER = os.getenv("IVY_DEMO_USER_1")
DEMO_PASSWORD = os.getenv("IVY_DEMO_PASSWORD")

LIMIT = 50
MAX_PAGES = 500

OUTPUT_PATH = Path("data/raw/listings.json")


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


def main():
    validate_environment()

    session = requests.Session()

    access_token = login(session)

    headers = {
        "X-API-Key": API_KEY,
        "Authorization": f"Bearer {access_token}",
    }

    url = f"{BASE_URL.rstrip('/')}/v1/listings"

    offset = 0
    page_number = 0

    all_results = []
    page_metadata = []

    seen_listing_ids = set()
    repeated_listing_ids = []

    totals_seen = set()

    while True:
        page_number += 1

        if page_number > MAX_PAGES:
            raise RuntimeError(
                f"Safety stop reached after {MAX_PAGES} pages. "
                "Pagination may not be progressing correctly."
            )

        response = session.get(
            url,
            headers=headers,
            params={
                "offset": offset,
                "limit": LIMIT,
            },
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        actual_offset = data.get("offset")
        actual_limit = data.get("limit")
        count = data.get("count")
        total = data.get("total")
        has_more = data.get("has_more")
        results = data.get("results")

        if not isinstance(results, list):
            raise RuntimeError(
                f"Page {page_number}: results is not a list."
            )

        if count != len(results):
            raise RuntimeError(
                f"Page {page_number}: count={count} "
                f"but len(results)={len(results)}."
            )

        if actual_offset != offset:
            raise RuntimeError(
                f"Page {page_number}: requested offset={offset}, "
                f"server reported offset={actual_offset}."
            )

        totals_seen.add(total)

        page_ids = []

        for item in results:
            listing_id = item.get("listing_id")

            if listing_id is not None:
                page_ids.append(listing_id)

                if listing_id in seen_listing_ids:
                    repeated_listing_ids.append(listing_id)

                seen_listing_ids.add(listing_id)

        page_metadata.append(
            {
                "page_number": page_number,
                "requested_offset": offset,
                "reported_offset": actual_offset,
                "reported_limit": actual_limit,
                "count": count,
                "total": total,
                "has_more": has_more,
                "first_listing_id": (
                    page_ids[0] if page_ids else None
                ),
                "last_listing_id": (
                    page_ids[-1] if page_ids else None
                ),
            }
        )

        all_results.extend(results)

        if (
            page_number == 1
            or page_number % 10 == 0
            or not has_more
        ):
            print(
                f"Page {page_number}: "
                f"offset={actual_offset}, "
                f"count={count}, "
                f"total={total}, "
                f"has_more={has_more}, "
                f"accumulated={len(all_results)}"
            )

        if not has_more:
            break

        if count <= 0:
            raise RuntimeError(
                "API reported has_more=true but returned zero records. "
                "Stopping to avoid an infinite loop."
            )

        next_offset = actual_offset + count

        if next_offset <= offset:
            raise RuntimeError(
                f"Pagination did not progress: "
                f"current offset={offset}, "
                f"next offset={next_offset}."
            )

        offset = next_offset

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    snapshot = {
        "metadata": {
            "endpoint": "/v1/listings",
            "fetched_at_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "requested_limit": LIMIT,
            "pages_fetched": page_number,
            "records_retrieved": len(all_results),
            "unique_listing_ids": len(seen_listing_ids),
            "repeated_listing_id_occurrences": len(
                repeated_listing_ids
            ),
            "repeated_listing_ids": sorted(
                set(repeated_listing_ids)
            ),
            "reported_totals_seen": sorted(totals_seen),
            "final_offset": page_metadata[-1][
                "reported_offset"
            ],
            "final_count": page_metadata[-1]["count"],
            "final_has_more": page_metadata[-1][
                "has_more"
            ],
        },
        "pages": page_metadata,
        "results": all_results,
    }

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            snapshot,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=== Fetch Complete ===")
    print(
        f"Pages fetched: {page_number}"
    )
    print(
        f"Records retrieved: {len(all_results)}"
    )
    print(
        f"Unique listing IDs: {len(seen_listing_ids)}"
    )
    print(
        "Repeated listing ID occurrences: "
        f"{len(repeated_listing_ids)}"
    )
    print(
        "Reported total values seen: "
        f"{sorted(totals_seen)}"
    )
    print(
        f"Final offset: "
        f"{page_metadata[-1]['reported_offset']}"
    )
    print(
        f"Final count: "
        f"{page_metadata[-1]['count']}"
    )
    print(
        f"Final has_more: "
        f"{page_metadata[-1]['has_more']}"
    )
    print(
        f"Raw snapshot saved to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()