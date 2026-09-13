import json
import os

import requests
from dotenv import load_dotenv


load_dotenv()


BASE_URL = os.environ["IVY_BASE_URL"].rstrip("/")
API_KEY = os.environ["IVY_API_KEY"]
EMAIL = os.environ["IVY_DEMO_USER_1"]
PASSWORD = os.environ["IVY_DEMO_PASSWORD"]


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


def print_matching_paths(
    paths,
    keyword,
):
    matches = [
        path
        for path in paths
        if keyword.lower()
        in path.lower()
    ]

    print()
    print(
        f"=== Paths containing "
        f"'{keyword}' ==="
    )

    if not matches:
        print(
            "<none>"
        )
        return

    for path in sorted(matches):
        methods = sorted(
            key.upper()
            for key in paths[
                path
            ].keys()
            if key.lower()
            in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
            }
        )

        print(
            path,
            methods,
        )


def main():
    session = requests.Session()

    print(
        "=== OpenAPI Route Discovery ==="
    )

    # Try unauthenticated first.
    response = session.get(
        f"{BASE_URL}/openapi.json",
        timeout=30,
    )

    print()
    print(
        "Unauthenticated /openapi.json:"
    )

    print(
        "Status:",
        response.status_code,
    )

    if response.status_code != 200:
        token = login(
            session
        )

        response = session.get(
            f"{BASE_URL}/openapi.json",
            headers={
                "X-API-Key": API_KEY,
                "Authorization":
                    f"Bearer {token}",
            },
            timeout=30,
        )

        print()
        print(
            "Authenticated /openapi.json:"
        )

        print(
            "Status:",
            response.status_code,
        )

    if response.status_code != 200:
        try:
            print(
                "Payload:",
                response.json(),
            )
        except ValueError:
            print(
                "Body:",
                response.text[:500],
            )

        return

    try:
        spec = response.json()
    except ValueError:
        print(
            "OpenAPI response is not JSON."
        )
        return

    paths = spec.get(
        "paths",
        {},
    )

    print()
    print(
        "OpenAPI title:",
        spec.get(
            "info",
            {},
        ).get(
            "title"
        ),
    )

    print(
        "OpenAPI version:",
        spec.get(
            "openapi"
        ),
    )

    print(
        "Number of registered paths:",
        len(paths),
    )

    print()
    print(
        "=== ALL REGISTERED PATHS ==="
    )

    for path in sorted(paths):
        methods = sorted(
            key.upper()
            for key in paths[
                path
            ].keys()
            if key.lower()
            in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
            }
        )

        print(
            path,
            methods,
        )

    for keyword in [
        "analytics",
        "summary",
        "favour",
        "favor",
        "listing",
        "rental",
        "project",
        "auth",
    ]:
        print_matching_paths(
            paths,
            keyword,
        )

    # Explicitly test whether the
    # documented problematic paths are
    # present in the route table.
    expected = [
        "/v1/analytics/summary",
        "/v1/favourites",
        "/v1/listing/{listing_id}",
        "/v1/listings/{listing_id}",
        "/v1/listings/{listing_id}/similar",
        "/auth/refresh",
        "/auth/logout",
    ]

    print()
    print(
        "=== DOCUMENTED / DISCOVERED "
        "PATH CHECK ==="
    )

    for path in expected:
        print(
            f"{path}:",
            path in paths,
        )


if __name__ == "__main__":
    main()