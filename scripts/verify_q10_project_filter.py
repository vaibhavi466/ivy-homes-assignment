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

PROJECTS_PATH = Path(
    "data/raw/projects.json"
)


# Projects where declared == local live count.
MATCH_SAMPLES = [
    "P60001",
    "P60002",
    "P60004",
    "P60005",
    "P60007",
    "P60009",
]


# Projects where declared != local live count.
MISMATCH_SAMPLES = [
    "P60006",
    "P60011",
    "P60012",
    "P60017",
    "P60021",
    "P60022",
]


def load_results(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["results"]


def login():
    response = requests.post(
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

    payload = response.json()

    return payload["access_token"]


def get_listings(
    token,
    project_id,
    live_filter=None,
):
    params = {
        "project_id": project_id,
        "limit": 50,
        "offset": 0,
    }

    if live_filter is not None:
        params["is_live"] = live_filter

    response = requests.get(
        f"{BASE_URL}/v1/listings",
        headers={
            "X-API-Key": API_KEY,
            "Authorization":
                f"Bearer {token}",
        },
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def summarize_response(
    project_id,
    response,
):
    results = response.get(
        "results",
        []
    )

    raw_project_ids = [
        item.get("project_id")
        for item in results
    ]

    returned_project_ids = sorted(
        set(raw_project_ids),
        key=lambda value: (
            value is None,
            str(value),
        ),
    )

    live_count = sum(
        item.get("is_live") is True
        for item in results
    )

    inactive_count = sum(
        item.get("is_live") is False
        for item in results
    )

    missing_project_id_count = sum(
        item.get("project_id") is None
        for item in results
    )

    wrong_project_records = [
        item
        for item in results
        if item.get("project_id")
        != project_id
    ]

    return {
        "requested_project":
            project_id,

        "response_count":
            response.get("count"),

        "response_total":
            response.get("total"),

        "returned_records":
            len(results),

        "live_in_results":
            live_count,

        "inactive_in_results":
            inactive_count,

        "returned_project_ids":
            returned_project_ids,

        "missing_project_id_count":
            missing_project_id_count,

        "wrong_project_record_count":
            len(
                wrong_project_records
            ),

        "wrong_project_sample_ids":
            [
                item.get(
                    "listing_id"
                )
                for item
                in wrong_project_records[:10]
            ],

        "filter_honored":
            len(
                wrong_project_records
            ) == 0,
    }

def main():
    listings = load_results(
        LISTINGS_PATH
    )

    projects = load_results(
        PROJECTS_PATH
    )

    projects_by_id = {
        project["project_id"]:
            project
        for project in projects
    }

    local_all = Counter()

    local_live = Counter()

    for listing in listings:
        project_id = listing.get(
            "project_id"
        )

        if not project_id:
            continue

        local_all[
            project_id
        ] += 1

        if (
            listing.get("is_live")
            is True
        ):
            local_live[
                project_id
            ] += 1

    token = login()

    print(
        "=== Q10 project_id Filter Verification ==="
    )

    print()
    print(
        "IMPORTANT: token obtained successfully "
        "but is not printed."
    )

    samples = (
        [
            (
                "DECLARED_MATCHES_LOCAL_LIVE",
                project_id,
            )
            for project_id
            in MATCH_SAMPLES
        ]
        +
        [
            (
                "DECLARED_DIFFERS_FROM_LOCAL_LIVE",
                project_id,
            )
            for project_id
            in MISMATCH_SAMPLES
        ]
    )

    for category, project_id in samples:
        project = projects_by_id[
            project_id
        ]

        print()
        print("=" * 76)

        print(
            f"Category: {category}"
        )

        print(
            f"Project: {project_id}"
        )

        print(
            f"Name: "
            f"{project.get('apartment_name')}"
        )

        print(
            "Declared total_listings: "
            f"{project.get('total_listings')}"
        )

        print(
            "Local all listing count: "
            f"{local_all.get(project_id, 0)}"
        )

        print(
            "Local live listing count: "
            f"{local_live.get(project_id, 0)}"
        )

        normal_response = (
            get_listings(
                token,
                project_id,
            )
        )

        normal_summary = (
            summarize_response(
                project_id,
                normal_response,
            )
        )

        print()
        print(
            "project_id filter only:"
        )

        print(
            normal_summary
        )

        live_response = (
            get_listings(
                token,
                project_id,
                live_filter="true",
            )
        )

        live_summary = (
            summarize_response(
                project_id,
                live_response,
            )
        )

        print()
        print(
            "project_id + is_live=true:"
        )

        print(
            live_summary
        )

    print()
    print(
        "Do not finalize Q10 until "
        "filter behavior is reviewed."
    )


if __name__ == "__main__":
    main()