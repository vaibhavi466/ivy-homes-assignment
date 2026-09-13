import json
import os
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

RENTALS_PATH = Path(
    "data/raw/rentals.json"
)

PROJECTS_PATH = Path(
    "data/raw/projects.json"
)


def load_results(path):
    with path.open(
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


def summarize_object(
    label,
    response,
    expected_id=None,
    id_field=None,
):
    print()
    print(
        f"=== {label} ==="
    )

    print(
        "Status:",
        response.status_code,
    )

    print(
        "Content-Type:",
        response.headers.get(
            "content-type",
            "",
        ),
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

        return

    if response.status_code >= 400:
        print(
            "Error payload:"
        )

        print(
            json.dumps(
                payload,
                indent=2,
            )
        )

        return

    print(
        "Payload type:",
        type(payload).__name__,
    )

    if isinstance(
        payload,
        dict,
    ):
        print(
            "Top-level keys:",
            sorted(
                payload.keys()
            ),
        )

        if (
            id_field
            and id_field in payload
        ):
            actual_id = payload.get(
                id_field
            )

            print(
                f"{id_field}:",
                actual_id,
            )

            if expected_id:
                print(
                    "Correct object returned:",
                    actual_id
                    == expected_id,
                )

        if "results" in payload:
            results = payload.get(
                "results"
            )

            print(
                "results type:",
                type(
                    results
                ).__name__,
            )

            if isinstance(
                results,
                list,
            ):
                print(
                    "results length:",
                    len(results),
                )

                if results:
                    print(
                        "first result ID:",
                        results[0].get(
                            id_field
                        )
                        if id_field
                        else "<not checked>",
                    )

    elif isinstance(
        payload,
        list,
    ):
        print(
            "List length:",
            len(payload),
        )

        if payload:
            print(
                "First object keys:",
                sorted(
                    payload[0].keys()
                )
                if isinstance(
                    payload[0],
                    dict,
                )
                else "<not an object>",
            )

            if (
                id_field
                and isinstance(
                    payload[0],
                    dict,
                )
            ):
                print(
                    "First result ID:",
                    payload[0].get(
                        id_field
                    ),
                )


def get(
    session,
    headers,
    path,
):
    return session.get(
        f"{BASE_URL}{path}",
        headers=headers,
        timeout=30,
    )


def main():
    listings = load_results(
        LISTINGS_PATH
    )

    rentals = load_results(
        RENTALS_PATH
    )

    projects = load_results(
        PROJECTS_PATH
    )

    listing_ids = [
        listings[0]["listing_id"],
        listings[
            len(listings) // 2
        ]["listing_id"],
        listings[-1]["listing_id"],
    ]

    rental_ids = [
        rentals[0]["listing_id"],
        rentals[
            len(rentals) // 2
        ]["listing_id"],
        rentals[-1]["listing_id"],
    ]

    project_ids = [
        projects[0]["project_id"],
        projects[
            len(projects) // 2
        ]["project_id"],
        projects[-1]["project_id"],
    ]

    session = requests.Session()

    token = login(
        session
    )

    headers = make_headers(
        token
    )

    print(
        "=== Ivy Homes Detail Endpoint Probe ==="
    )

    print(
        "Secrets and tokens are not printed."
    )

    print()
    print(
        "Listing samples:",
        listing_ids,
    )

    print(
        "Rental samples:",
        rental_ids,
    )

    print(
        "Project samples:",
        project_ids,
    )

    # ---------------------------------
    # LISTING DETAIL
    # ---------------------------------

    for listing_id in listing_ids:
        response = get(
            session,
            headers,
            (
                "/v1/listing/"
                f"{listing_id}"
            ),
        )

        summarize_object(
            (
                "DOCUMENTED listing detail "
                f"/v1/listing/{listing_id}"
            ),
            response,
            expected_id=listing_id,
            id_field="listing_id",
        )

        # Plausible plural form.
        # This is intentionally exploratory:
        # if it exists, it would be an
        # undocumented endpoint.
        response = get(
            session,
            headers,
            (
                "/v1/listings/"
                f"{listing_id}"
            ),
        )

        summarize_object(
            (
                "CANDIDATE plural listing detail "
                f"/v1/listings/{listing_id}"
            ),
            response,
            expected_id=listing_id,
            id_field="listing_id",
        )

    # ---------------------------------
    # SIMILAR LISTINGS
    # ---------------------------------

    for listing_id in listing_ids:
        response = get(
            session,
            headers,
            (
                "/v1/listings/"
                f"{listing_id}/similar"
            ),
        )

        summarize_object(
            (
                "DOCUMENTED similar listings "
                f"/v1/listings/{listing_id}/similar"
            ),
            response,
            id_field="listing_id",
        )

    # ---------------------------------
    # RENTAL DETAIL
    # ---------------------------------

    for rental_id in rental_ids:
        response = get(
            session,
            headers,
            (
                "/v1/rentals/"
                f"{rental_id}"
            ),
        )

        summarize_object(
            (
                "DOCUMENTED rental detail "
                f"/v1/rentals/{rental_id}"
            ),
            response,
            expected_id=rental_id,
            id_field="listing_id",
        )

    # ---------------------------------
    # PROJECT DETAIL
    # ---------------------------------

    for project_id in project_ids:
        response = get(
            session,
            headers,
            (
                "/v1/projects/"
                f"{project_id}"
            ),
        )

        summarize_object(
            (
                "DOCUMENTED project detail "
                f"/v1/projects/{project_id}"
            ),
            response,
            expected_id=project_id,
            id_field="project_id",
        )

    # ---------------------------------
    # Invalid IDs — verify 404 contract
    # ---------------------------------

    invalid_tests = [
        (
            "/v1/listing/"
            "DOES-NOT-EXIST",
            "invalid listing detail",
        ),
        (
            "/v1/listings/"
            "DOES-NOT-EXIST",
            "invalid plural listing detail",
        ),
        (
            "/v1/listings/"
            "DOES-NOT-EXIST/similar",
            "invalid similar listings",
        ),
        (
            "/v1/rentals/"
            "DOES-NOT-EXIST",
            "invalid rental detail",
        ),
        (
            "/v1/projects/"
            "DOES-NOT-EXIST",
            "invalid project detail",
        ),
    ]

    print()
    print(
        "=" * 72
    )

    print(
        "INVALID-ID ERROR CONTRACT"
    )

    print(
        "=" * 72
    )

    for path, label in invalid_tests:
        response = get(
            session,
            headers,
            path,
        )

        print()
        print(
            label
        )

        print(
            "Path:",
            path,
        )

        print(
            "Status:",
            response.status_code,
        )

        try:
            print(
                "Payload:",
                response.json(),
            )
        except ValueError:
            print(
                "Body:",
                response.text[:300],
            )

    print()
    print(
        "Review before updating "
        "documentation-audit.md."
    )


if __name__ == "__main__":
    main()