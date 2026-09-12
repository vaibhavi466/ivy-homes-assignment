import os
import json

import requests
from dotenv import load_dotenv


# Load local environment variables from .env
load_dotenv()

BASE_URL = os.getenv("IVY_BASE_URL")


def main():
    if not BASE_URL:
        raise RuntimeError("IVY_BASE_URL is missing from .env")

    url = f"{BASE_URL.rstrip('/')}/health"

    print("=== Ivy Homes Health Probe ===")
    print(f"Request URL: {url}")
    print("Authentication: none")
    print()

    try:
        response = requests.get(
            url,
            timeout=10,
        )
    except requests.RequestException as exc:
        print(f"Request failed: {exc}")
        return

    print(f"Status code: {response.status_code}")

    content_type = response.headers.get("content-type", "")
    print(f"Content-Type: {content_type}")
    print()

    print("Raw response:")
    print(response.text)
    print()

    try:
        data = response.json()

        print("Parsed JSON:")
        print(json.dumps(data, indent=2))

    except ValueError:
        print("Response is not valid JSON.")


if __name__ == "__main__":
    main()