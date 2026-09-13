import base64
import json
import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv


load_dotenv()


BASE_URL = os.environ["IVY_BASE_URL"].rstrip("/")
API_KEY = os.environ["IVY_API_KEY"]
EMAIL = os.environ["IVY_DEMO_USER_1"]
PASSWORD = os.environ["IVY_DEMO_PASSWORD"]


def safe_payload(payload):
    """
    Remove secret token values before printing.
    """
    if not isinstance(payload, dict):
        return payload

    cleaned = {}

    for key, value in payload.items():
        if "token" in key.lower():
            cleaned[key] = "<redacted>"
        else:
            cleaned[key] = value

    return cleaned


def decode_jwt_payload(token):
    """
    Decode JWT payload without verifying the signature.
    This is only for inspecting iat/exp metadata.
    """
    try:
        parts = token.split(".")

        if len(parts) != 3:
            return None

        encoded = parts[1]

        padding = "=" * (
            (-len(encoded)) % 4
        )

        decoded = base64.urlsafe_b64decode(
            encoded + padding
        )

        return json.loads(
            decoded.decode("utf-8")
        )

    except Exception:
        return None


def show_token_metadata(
    label,
    token,
):
    print()
    print(f"=== {label} ===")

    payload = decode_jwt_payload(
        token
    )

    if payload is None:
        print(
            "Token is not a decodable JWT "
            "or has an unexpected format."
        )
        return

    print(
        "JWT claim keys:",
        sorted(payload.keys()),
    )

    issued_at = payload.get("iat")
    expires_at = payload.get("exp")

    print(
        "iat:",
        issued_at,
    )

    print(
        "exp:",
        expires_at,
    )

    if isinstance(
        issued_at,
        (int, float),
    ):
        print(
            "issued_at UTC:",
            datetime.fromtimestamp(
                issued_at,
                tz=timezone.utc,
            ).isoformat(),
        )

    if isinstance(
        expires_at,
        (int, float),
    ):
        print(
            "expires_at UTC:",
            datetime.fromtimestamp(
                expires_at,
                tz=timezone.utc,
            ).isoformat(),
        )

    if (
        isinstance(
            issued_at,
            (int, float),
        )
        and isinstance(
            expires_at,
            (int, float),
        )
    ):
        print(
            "JWT lifetime seconds:",
            expires_at - issued_at,
        )

        print(
            "JWT lifetime minutes:",
            (
                expires_at
                - issued_at
            ) / 60,
        )


def protected_request(
    session,
    access_token,
    label,
):
    response = session.get(
        f"{BASE_URL}/v1/listings",
        headers={
            "X-API-Key": API_KEY,
            "Authorization":
                f"Bearer {access_token}",
        },
        params={
            "limit": 1,
            "offset": 0,
        },
        timeout=30,
    )

    print()
    print(
        f"=== {label} ==="
    )

    print(
        "Status:",
        response.status_code,
    )

    try:
        payload = response.json()

        if response.status_code == 200:
            print(
                "Protected endpoint works:",
                True,
            )

            print(
                "Response count:",
                payload.get("count"),
            )

        else:
            print(
                "Payload:",
                safe_payload(payload),
            )

    except ValueError:
        print(
            "Body:",
            response.text[:500],
        )

    return response.status_code


def refresh_session(
    session,
    refresh_token,
):
    print()
    print(
        "=" * 72
    )

    print(
        "REFRESH TOKEN TEST"
    )

    print(
        "=" * 72
    )

    # First try the most conventional
    # observed contract:
    # POST /auth/refresh
    # {"refresh_token": "..."}
    response = session.post(
        f"{BASE_URL}/auth/refresh",
        headers={
            "X-API-Key": API_KEY,
        },
        json={
            "refresh_token":
                refresh_token,
        },
        timeout=30,
    )

    print()
    print(
        "Attempt 1:"
    )

    print(
        "POST /auth/refresh"
    )

    print(
        "X-API-Key header + "
        "refresh_token JSON body"
    )

    print(
        "Status:",
        response.status_code,
    )

    try:
        payload = response.json()
    except ValueError:
        payload = None

    if payload is not None:
        print(
            "Payload:",
            safe_payload(payload),
        )

    if response.status_code == 200:
        return payload

    # Only try a Bearer-style refresh
    # if the JSON form failed.
    response = session.post(
        f"{BASE_URL}/auth/refresh",
        headers={
            "X-API-Key": API_KEY,
            "Authorization":
                f"Bearer {refresh_token}",
        },
        timeout=30,
    )

    print()
    print(
        "Attempt 2:"
    )

    print(
        "POST /auth/refresh"
    )

    print(
        "X-API-Key + refresh token "
        "as Bearer"
    )

    print(
        "Status:",
        response.status_code,
    )

    try:
        payload = response.json()
    except ValueError:
        payload = None

    if payload is not None:
        print(
            "Payload:",
            safe_payload(payload),
        )

    if response.status_code == 200:
        return payload

    return None


def refresh_after_logout(
    session,
    refresh_token,
):
    response = session.post(
        f"{BASE_URL}/auth/refresh",
        headers={
            "X-API-Key": API_KEY,
        },
        json={
            "refresh_token":
                refresh_token,
        },
        timeout=30,
    )

    print()
    print(
        "=== Refresh after logout ==="
    )

    print(
        "Status:",
        response.status_code,
    )

    try:
        print(
            "Payload:",
            safe_payload(
                response.json()
            ),
        )
    except ValueError:
        print(
            "Body:",
            response.text[:500],
        )


def main():
    session = requests.Session()

    print(
        "=== Ivy Homes Authentication "
        "Lifecycle Probe ==="
    )

    print(
        "No API key, password, or token "
        "values will be printed."
    )

    # ---------------------------------
    # Login
    # ---------------------------------

    login_response = session.post(
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

    print()
    print(
        "=" * 72
    )

    print(
        "LOGIN"
    )

    print(
        "=" * 72
    )

    print(
        "Status:",
        login_response.status_code,
    )

    login_response.raise_for_status()

    login_payload = (
        login_response.json()
    )

    print(
        "Login payload:",
        safe_payload(
            login_payload
        ),
    )

    print(
        "Login response keys:",
        sorted(
            login_payload.keys()
        ),
    )

    print(
        "token_type:",
        login_payload.get(
            "token_type"
        ),
    )

    print(
        "expires_in:",
        login_payload.get(
            "expires_in"
        ),
    )

    print(
        "refresh_url:",
        login_payload.get(
            "refresh_url"
        ),
    )

    access_token = (
        login_payload.get(
            "access_token"
        )
    )

    refresh_token = (
        login_payload.get(
            "refresh_token"
        )
    )

    print(
        "access_token present:",
        bool(access_token),
    )

    print(
        "refresh_token present:",
        bool(refresh_token),
    )

    if access_token:
        show_token_metadata(
            "ACCESS TOKEN FROM LOGIN",
            access_token,
        )

    if refresh_token:
        show_token_metadata(
            "REFRESH TOKEN FROM LOGIN",
            refresh_token,
        )

    # ---------------------------------
    # Access before refresh
    # ---------------------------------

    protected_request(
        session,
        access_token,
        "Protected request before refresh",
    )

    # ---------------------------------
    # Refresh
    # ---------------------------------

    if not refresh_token:
        print()
        print(
            "No refresh token returned; "
            "cannot continue refresh test."
        )
        return

    refresh_payload = refresh_session(
        session,
        refresh_token,
    )

    if refresh_payload is None:
        print()
        print(
            "Refresh could not be completed."
        )

        print(
            "Stop here and review output."
        )

        return

    new_access_token = (
        refresh_payload.get(
            "access_token"
        )
        or refresh_payload.get(
            "token"
        )
    )

    new_refresh_token = (
        refresh_payload.get(
            "refresh_token"
        )
        or refresh_token
    )

    print()
    print(
        "New access token present:",
        bool(new_access_token),
    )

    print(
        "Refresh token returned:",
        "refresh_token"
        in refresh_payload,
    )

    print(
        "Access token changed:",
        new_access_token
        != access_token,
    )

    print(
        "Refresh token changed:",
        new_refresh_token
        != refresh_token,
    )

    print(
        "Refresh expires_in:",
        refresh_payload.get(
            "expires_in"
        ),
    )

    if new_access_token:
        show_token_metadata(
            "ACCESS TOKEN AFTER REFRESH",
            new_access_token,
        )

        protected_request(
            session,
            new_access_token,
            "Protected request after refresh",
        )

    # ---------------------------------
    # Check old access token
    # ---------------------------------

    protected_request(
        session,
        access_token,
        "Original access token after refresh",
    )

    # ---------------------------------
    # Logout
    # ---------------------------------

    print()
    print(
        "=" * 72
    )

    print(
        "LOGOUT"
    )

    print(
        "=" * 72
    )

    logout_response = session.post(
        f"{BASE_URL}/auth/logout",
        headers={
            "X-API-Key": API_KEY,
            "Authorization":
                f"Bearer {new_access_token}",
        },
        timeout=30,
    )

    print(
        "Status:",
        logout_response.status_code,
    )

    try:
        print(
            "Payload:",
            safe_payload(
                logout_response.json()
            ),
        )
    except ValueError:
        print(
            "Body:",
            logout_response.text[:500],
        )

    # ---------------------------------
    # Access after logout
    # ---------------------------------

    protected_request(
        session,
        new_access_token,
        "Refreshed access token after logout",
    )

    protected_request(
        session,
        access_token,
        "Original access token after logout",
    )

    # ---------------------------------
    # Refresh after logout
    # ---------------------------------

    refresh_after_logout(
        session,
        new_refresh_token,
    )

    print()
    print(
        "Do not update the audit yet."
    )

    print(
        "Review the lifecycle behavior first."
    )


if __name__ == "__main__":
    main()