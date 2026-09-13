import os

import requests
from dotenv import load_dotenv


load_dotenv()


BASE_URL = os.environ["IVY_BASE_URL"].rstrip("/")
API_KEY = os.environ["IVY_API_KEY"]
EMAIL = os.environ["IVY_DEMO_USER_1"]
PASSWORD = os.environ["IVY_DEMO_PASSWORD"]


def login():
    session = requests.Session()

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

    return (
        session,
        response.json()["access_token"],
    )


def headers(token):
    return {
        "X-API-Key": API_KEY,
        "Authorization":
            f"Bearer {token}",
    }


def probe(
    session,
    token,
    method,
    path,
    **kwargs,
):
    response = session.request(
        method,
        f"{BASE_URL}{path}",
        headers={
            **headers(token),
            **kwargs.pop(
                "headers",
                {},
            ),
        },
        timeout=30,
        **kwargs,
    )

    print()
    print(
        f"{method} {path}"
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
            response.text[:500],
        )

    return response


def main():
    session, token = login()

    print(
        "=== Favourites Path Discovery ==="
    )

    print(
        "No credentials or tokens "
        "are printed."
    )

    # Documented spelling
    probe(
        session,
        token,
        "GET",
        "/v1/favourites",
    )

    # Most plausible alternate spelling
    probe(
        session,
        token,
        "GET",
        "/v1/favorites",
    )

    # Also check singular route names,
    # but do not mutate anything.
    probe(
        session,
        token,
        "GET",
        "/v1/favourite",
    )

    probe(
        session,
        token,
        "GET",
        "/v1/favorite",
    )

    print()
    print(
        "Do not update audit yet."
    )


if __name__ == "__main__":
    main()