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

PROJECTS_PATH = Path(
    "data/raw/projects.json"
)


DOCUMENTED_FIELDS = {
    "project_id",
    "project_url",
    "city_id",
    "apartment_name",
    "developer_name",
    "locality",
    "project_status",
    "total_units",
    "total_towers",
    "total_floors",
    "launch_date",
    "possession_date",
    "rera_number",
    "min_area_sqft",
    "max_area_sqft",
    "total_listings",
    "price_min",
    "price_max",
    "amenities",
    "latitude",
    "longitude",
}


def load_projects():
    with PROJECTS_PATH.open(
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


def request_projects(
    session,
    headers,
    params,
):
    response = session.get(
        f"{BASE_URL}/v1/projects",
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


def normalize_project_price(value):
    if not isinstance(
        value,
        (int, float),
    ):
        return None

    # Previously verified project
    # mixed-unit rule.
    if value < 10:
        return int(
            round(
                value
                * 10_000_000
            )
        )

    return int(
        round(
            value
            * 100_000
        )
    )


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
    projects,
    name,
    params,
    predicate,
):
    payload = request_projects(
        session,
        headers,
        params,
    )

    local_count = sum(
        predicate(project)
        for project in projects
    )

    results = payload[
        "results"
    ]

    mismatches = [
        project
        for project in results
        if not predicate(project)
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


def sort_check(
    session,
    headers,
    field,
):
    asc = request_projects(
        session,
        headers,
        {
            "sort_by": field,
            "order": "asc",
        },
    )

    desc = request_projects(
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
        project["project_id"]
        for project
        in asc_results
    ]

    desc_ids = [
        project["project_id"]
        for project
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

    if field in {
        "price_min",
        "price_max",
    }:
        asc_raw = [
            project.get(field)
            for project
            in asc_results
        ]

        desc_raw = [
            project.get(field)
            for project
            in desc_results
        ]

        asc_normalized = [
            normalize_project_price(
                project.get(field)
            )
            for project
            in asc_results
        ]

        desc_normalized = [
            normalize_project_price(
                project.get(field)
            )
            for project
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
            asc_normalized[:15]
        )

        print(
            "DESC first 15 raw:"
        )

        print(
            desc_raw[:15]
        )

        return

    if field == "launch_date":
        asc_values = [
            project.get(
                "launch_date"
            )
            for project
            in asc_results
        ]

        desc_values = [
            project.get(
                "launch_date"
            )
            for project
            in desc_results
        ]

        asc_dates = [
            datetime.fromisoformat(
                value
            ).date()
            if value
            else None
            for value
            in asc_values
        ]

        desc_dates = [
            datetime.fromisoformat(
                value
            ).date()
            if value
            else None
            for value
            in desc_values
        ]

        print(
            "ASC monotonic:",
            monotonic(
                asc_dates
            ),
        )

        print(
            "DESC monotonic:",
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
        project.get(field)
        for project
        in asc_results
    ]

    desc_values = [
        project.get(field)
        for project
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
    projects = load_projects()

    print(
        "=== Project API Contract Probe ==="
    )

    print(
        "Complete snapshot:",
        len(projects),
    )

    # ---------------------------------
    # Field contract
    # ---------------------------------

    print()
    print(
        "=== FIELD CONTRACT ==="
    )

    all_fields = set()

    missing_records = []

    for project in projects:
        all_fields.update(
            project.keys()
        )

        missing = (
            DOCUMENTED_FIELDS
            - set(project.keys())
        )

        if missing:
            missing_records.append(
                (
                    project[
                        "project_id"
                    ],
                    sorted(missing),
                )
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
        len(missing_records),
    )

    print(
        "Additional observed fields:"
    )

    print(
        sorted(
            all_fields
            - DOCUMENTED_FIELDS
        )
    )

    # ---------------------------------
    # Lowercase convention
    # ---------------------------------

    print()
    print(
        "=== LOWERCASE STRING CONTRACT ==="
    )

    for field in [
        "locality",
        "project_status",
    ]:
        violations = [
            project["project_id"]
            for project in projects
            if (
                isinstance(
                    project.get(field),
                    str,
                )
                and project[field]
                != project[field].lower()
            )
        ]

        print(
            f"{field} violations:",
            len(violations),
        )

        if violations:
            print(
                violations[:20]
            )

    # ---------------------------------
    # Date contract
    # ---------------------------------

    print()
    print(
        "=== DATE CONTRACT ==="
    )

    for field in [
        "launch_date",
        "possession_date",
    ]:
        invalid = []

        missing = []

        for project in projects:
            value = project.get(
                field
            )

            if value is None:
                missing.append(
                    project[
                        "project_id"
                    ]
                )
                continue

            try:
                parsed = (
                    datetime
                    .fromisoformat(
                        value
                    )
                )

                if (
                    parsed.strftime(
                        "%Y-%m-%d"
                    )
                    != value
                ):
                    invalid.append(
                        project[
                            "project_id"
                        ]
                    )

            except ValueError:
                invalid.append(
                    project[
                        "project_id"
                    ]
                )

        print()
        print(
            f"{field}:"
        )

        print(
            "missing:",
            len(missing),
        )

        print(
            "invalid YYYY-MM-DD:",
            len(invalid),
        )

        if invalid:
            print(
                invalid[:20]
            )

    # ---------------------------------
    # Area contract
    # ---------------------------------

    print()
    print(
        "=== AREA CONTRACT ==="
    )

    invalid_min_area = []
    invalid_max_area = []
    inverted_area = []

    for project in projects:
        minimum = project.get(
            "min_area_sqft"
        )

        maximum = project.get(
            "max_area_sqft"
        )

        if (
            not isinstance(
                minimum,
                (int, float),
            )
            or isinstance(
                minimum,
                bool,
            )
            or minimum <= 0
        ):
            invalid_min_area.append(
                project[
                    "project_id"
                ]
            )

        if (
            not isinstance(
                maximum,
                (int, float),
            )
            or isinstance(
                maximum,
                bool,
            )
            or maximum <= 0
        ):
            invalid_max_area.append(
                project[
                    "project_id"
                ]
            )

        if (
            isinstance(
                minimum,
                (int, float),
            )
            and isinstance(
                maximum,
                (int, float),
            )
            and minimum > maximum
        ):
            inverted_area.append(
                project[
                    "project_id"
                ]
            )

    print(
        "Invalid/non-positive min_area:",
        len(invalid_min_area),
    )

    print(
        "Invalid/non-positive max_area:",
        len(invalid_max_area),
    )

    print(
        "min_area > max_area:",
        len(inverted_area),
    )

    area_mins = [
        project[
            "min_area_sqft"
        ]
        for project in projects
        if isinstance(
            project.get(
                "min_area_sqft"
            ),
            (int, float),
        )
    ]

    area_maxs = [
        project[
            "max_area_sqft"
        ]
        for project in projects
        if isinstance(
            project.get(
                "max_area_sqft"
            ),
            (int, float),
        )
    ]

    print(
        "min_area range:",
        (
            min(area_mins),
            max(area_mins),
        ),
    )

    print(
        "max_area range:",
        (
            min(area_maxs),
            max(area_maxs),
        ),
    )

    # ---------------------------------
    # Project-price contract summary
    # ---------------------------------

    print()
    print(
        "=== PRICE UNIT SUMMARY ==="
    )

    raw_inverted = 0
    normalized_inverted = 0

    for project in projects:
        raw_min = project[
            "price_min"
        ]

        raw_max = project[
            "price_max"
        ]

        if raw_min > raw_max:
            raw_inverted += 1

        normalized_min = (
            normalize_project_price(
                raw_min
            )
        )

        normalized_max = (
            normalize_project_price(
                raw_max
            )
        )

        if (
            normalized_min
            > normalized_max
        ):
            normalized_inverted += 1

    print(
        "Raw price_min > price_max:",
        raw_inverted,
    )

    print(
        "Normalized price_min > "
        "price_max:",
        normalized_inverted,
    )

    # ---------------------------------
    # Filter values
    # ---------------------------------

    locality_counts = Counter(
        project.get("locality")
        for project in projects
        if project.get("locality")
    )

    status_counts = Counter(
        project.get(
            "project_status"
        )
        for project in projects
        if project.get(
            "project_status"
        )
    )

    localities = [
        value
        for value, _
        in locality_counts.most_common(
            2
        )
    ]

    statuses = [
        value
        for value, _
        in status_counts.most_common(
            2
        )
    ]

    print()
    print(
        "=== FILTER PROBE VALUES ==="
    )

    print(
        "localities:",
        localities,
    )

    print(
        "statuses:",
        statuses,
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
            projects,
            f"locality={locality}",
            {
                "locality":
                    locality,
            },
            lambda project,
            locality=locality:
                project.get(
                    "locality"
                )
                == locality,
        )

    for status in statuses:
        filter_check(
            session,
            auth_headers,
            projects,
            (
                "project_status="
                f"{status}"
            ),
            {
                "project_status":
                    status,
            },
            lambda project,
            status=status:
                project.get(
                    "project_status"
                )
                == status,
        )

    filter_check(
        session,
        auth_headers,
        projects,
        "combined filter",
        {
            "locality":
                localities[0],
            "project_status":
                statuses[0],
        },
        lambda project:
            (
                project.get(
                    "locality"
                )
                == localities[0]
                and project.get(
                    "project_status"
                )
                == statuses[0]
            ),
    )

    # ---------------------------------
    # Documented sorting
    # ---------------------------------

    for field in [
        "price_min",
        "price_max",
        "launch_date",
        "total_units",
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
        "Review the output first."
    )


if __name__ == "__main__":
    main()