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

COLLECTIONS = {
    "rentals": {
        "endpoint": "/v1/rentals",
        "id_field": "listing_id",
        "output": Path("data/raw/rentals.json"),
    },
    "projects": {
        "endpoint": "/v1/projects",
        "id_field": "project_id",
        "output": Path("data/raw/projects.json"),
    },
}


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


def fetch_collection(
    session,
    headers,
    name,
    config,
):
    endpoint = config["endpoint"]
    id_field = config["id_field"]
    output_path = config["output"]

    url = f"{BASE_URL.rstrip('/')}{endpoint}"

    print()
    print("=" * 70)
    print(f"FETCHING {name.upper()}")
    print("=" * 70)

    offset = 0
    page_number = 0

    all_results = []
    page_metadata = []

    seen_ids = set()
    repeated_ids = []

    totals_seen = set()

    while True:
        page_number += 1

        if page_number > MAX_PAGES:
            raise RuntimeError(
                f"{name}: safety stop reached after "
                f"{MAX_PAGES} pages."
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
                f"{name}, page {page_number}: "
                "results is not a list."
            )

        if count != len(results):
            raise RuntimeError(
                f"{name}, page {page_number}: "
                f"count={count}, "
                f"len(results)={len(results)}."
            )

        if actual_offset != offset:
            raise RuntimeError(
                f"{name}, page {page_number}: "
                f"requested offset={offset}, "
                f"reported offset={actual_offset}."
            )

        totals_seen.add(total)

        page_ids = []

        for item in results:
            record_id = item.get(id_field)

            if record_id is None:
                continue

            page_ids.append(record_id)

            if record_id in seen_ids:
                repeated_ids.append(record_id)

            seen_ids.add(record_id)

        page_metadata.append(
            {
                "page_number": page_number,
                "requested_offset": offset,
                "reported_offset": actual_offset,
                "reported_limit": actual_limit,
                "count": count,
                "total": total,
                "has_more": has_more,
                "first_id": (
                    page_ids[0]
                    if page_ids
                    else None
                ),
                "last_id": (
                    page_ids[-1]
                    if page_ids
                    else None
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
                f"{name}: API reported has_more=true "
                "but returned zero records."
            )

        next_offset = actual_offset + count

        if next_offset <= offset:
            raise RuntimeError(
                f"{name}: pagination did not progress. "
                f"current={offset}, next={next_offset}"
            )

        offset = next_offset

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    snapshot = {
        "metadata": {
            "endpoint": endpoint,
            "id_field": id_field,
            "fetched_at_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "requested_limit": LIMIT,
            "pages_fetched": page_number,
            "records_retrieved": len(all_results),
            "unique_ids": len(seen_ids),
            "repeated_id_occurrences": len(
                repeated_ids
            ),
            "repeated_ids": sorted(
                set(repeated_ids)
            ),
            "reported_totals_seen": sorted(
                totals_seen
            ),
            "final_offset": page_metadata[-1][
                "reported_offset"
            ],
            "final_count": page_metadata[-1][
                "count"
            ],
            "final_has_more": page_metadata[-1][
                "has_more"
            ],
        },
        "pages": page_metadata,
        "results": all_results,
    }

    with output_path.open(
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
    print(f"=== {name.upper()} FETCH COMPLETE ===")
    print(
        f"Pages fetched: {page_number}"
    )
    print(
        f"Records retrieved: {len(all_results)}"
    )
    print(
        f"Unique IDs: {len(seen_ids)}"
    )
    print(
        "Repeated ID occurrences: "
        f"{len(repeated_ids)}"
    )
    print(
        "Reported totals seen: "
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
        f"Saved to: {output_path}"
    )

    return snapshot


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

    for name, config in COLLECTIONS.items():
        fetch_collection(
            session=session,
            headers=headers,
            name=name,
            config=config,
        )


if __name__ == "__main__":
    main()