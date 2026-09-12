import os
import json

import requests
from dotenv import load_dotenv


load_dotenv()

BASE_URL = os.getenv("IVY_BASE_URL")
API_KEY = os.getenv("IVY_API_KEY")
DEMO_USER = os.getenv("IVY_DEMO_USER_1")
DEMO_PASSWORD = os.getenv("IVY_DEMO_PASSWORD")


SENSITIVE_KEYS = {
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "password",
}


def redact_sensitive_data(value):
    if isinstance(value, dict):
        return {
            key: (
                "<REDACTED>"
                if key.lower() in SENSITIVE_KEYS
                else redact_sensitive_data(item)
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]

    return value


def print_response(label, response):
    print(f"\n=== {label} ===")
    print(f"Status code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', '')}")

    try:
        data = response.json()
        safe_data = redact_sensitive_data(data)

        print("\nRedacted response:")
        print(json.dumps(safe_data))

        print("\nParsed JSON:")
        print(json.dumps(safe_data, indent=2))

    except ValueError:
        print("\nRaw response:")
        print(response.text)

        print("\nResponse is not valid JSON.")


def main():
    required = {
        "IVY_BASE_URL": BASE_URL,
        "IVY_API_KEY": API_KEY,
        "IVY_DEMO_USER_1": DEMO_USER,
        "IVY_DEMO_PASSWORD": DEMO_PASSWORD,
    }

    missing = [name for name, value in required.items() if not value]

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    url = f"{BASE_URL.rstrip('/')}/auth/login"

    api_headers = {
        "X-API-Key": API_KEY
    }

    print("=== Ivy Homes Authentication Probe ===")
    print(f"Request URL: {url}")
    print(f"Demo user: {DEMO_USER}")
    print("Passwords/tokens/API keys will not be printed.")

    valid_payload = {
        "email": DEMO_USER,
        "password": DEMO_PASSWORD,
    }

    # Test A — no API key
    response = requests.post(
        url,
        json=valid_payload,
        timeout=10,
    )

    print_response(
        "A — Valid credentials, no API key",
        response,
    )

    # Test B — documented query-parameter API key
    response = requests.post(
        url,
        params={"api_key": API_KEY},
        json=valid_payload,
        timeout=10,
    )

    print_response(
        "B — Valid credentials, API key as query parameter",
        response,
    )

    # Test C — observed X-API-Key header
    response = requests.post(
        url,
        headers=api_headers,
        json=valid_payload,
        timeout=10,
    )

    print_response(
        "C — Valid credentials, X-API-Key header",
        response,
    )

    # Test D — wrong password using observed key mechanism
    wrong_password_payload = {
        "email": DEMO_USER,
        "password": "definitely-wrong-password",
    }

    response = requests.post(
        url,
        headers=api_headers,
        json=wrong_password_payload,
        timeout=10,
    )

    print_response(
        "D — Invalid password, X-API-Key header",
        response,
    )

    # Test E — nonexistent user using observed key mechanism
    invalid_user_payload = {
        "email": "nonexistent-user@ivy.homes",
        "password": DEMO_PASSWORD,
    }

    response = requests.post(
        url,
        headers=api_headers,
        json=invalid_user_payload,
        timeout=10,
    )

    print_response(
        "E — Invalid user, X-API-Key header",
        response,
    )


if __name__ == "__main__":
    main()