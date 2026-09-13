import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()


BASE_URL = os.environ["IVY_BASE_URL"].rstrip("/")
API_KEY = os.environ["IVY_API_KEY"]

USER_1 = os.environ["IVY_DEMO_USER_1"]
USER_2 = os.environ.get("IVY_DEMO_USER_2")
PASSWORD = os.environ["IVY_DEMO_PASSWORD"]

LISTINGS_PATH = Path(
    "data/raw/listings.json"
)


def load_listings():
    with LISTINGS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["results"]


def login(email):
    session = requests.Session()

    response = session.post(
        f"{BASE_URL}/auth/login",
        headers={
            "X-API-Key": API_KEY,
        },
        json={
            "email": email,
            "password": PASSWORD,
        },
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    return (
        session,
        payload["access_token"],
    )


def auth_headers(token):
    return {
        "X-API-Key": API_KEY,
        "Authorization":
            f"Bearer {token}",
    }


def get_favourites(
    session,
    token,
    label,
):
    response = session.get(
        f"{BASE_URL}/v1/favourites",
        headers=auth_headers(token),
        timeout=30,
    )

    print()
    print(
        f"=== GET favourites: {label} ==="
    )

    print(
        "Status:",
        response.status_code,
    )

    try:
        payload = response.json()
    except ValueError:
        print(
            "Non-JSON body:",
            response.text[:500],
        )

        return None, set()

    print(
        "Top-level payload type:",
        type(payload).__name__,
    )

    if isinstance(payload, dict):
        print(
            "Top-level keys:",
            sorted(payload.keys()),
        )

        results = payload.get(
            "results",
            [],
        )

        print(
            "count field:",
            payload.get("count"),
        )

        print(
            "actual results length:",
            len(results)
            if isinstance(results, list)
            else "<not a list>",
        )

        print(
            "count matches results length:",
            (
                isinstance(results, list)
                and payload.get("count")
                == len(results)
            ),
        )
    else:
        results = []

    ids = set()

    if isinstance(results, list):
        for item in results:
            if isinstance(item, dict):
                item_id = (
                    item.get("listing_id")
                    or item.get("id")
                )

                if item_id:
                    ids.add(item_id)

        print(
            "Results are objects:",
            all(
                isinstance(item, dict)
                for item in results
            ),
        )

        if results:
            print(
                "First result keys:",
                sorted(
                    results[0].keys()
                )
                if isinstance(
                    results[0],
                    dict,
                )
                else "<not object>",
            )

    print(
        "Extracted favourite IDs:",
        len(ids),
    )

    return payload, ids


def add_favourite(
    session,
    token,
    listing_id,
):
    response = session.post(
        f"{BASE_URL}/v1/favourites",
        headers={
            **auth_headers(token),
            "Content-Type":
                "application/json",
        },
        json={
            "id": listing_id,
        },
        timeout=30,
    )

    print()
    print(
        "=== POST favourite ==="
    )

    print(
        "Test listing:",
        listing_id,
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


def delete_favourite(
    session,
    token,
    listing_id,
    label,
):
    response = session.delete(
        (
            f"{BASE_URL}/v1/favourites/"
            f"{listing_id}"
        ),
        headers=auth_headers(token),
        timeout=30,
    )

    print()
    print(
        f"=== DELETE favourite: {label} ==="
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


def logout(
    session,
    token,
):
    response = session.post(
        f"{BASE_URL}/auth/logout",
        headers=auth_headers(token),
        timeout=30,
    )

    print()
    print(
        "=== Logout user 1 ==="
    )

    print(
        "Status:",
        response.status_code,
    )

    return response


def choose_test_listing(
    listings,
    blocked_ids,
):
    # Prefer a normal, live listing
    # that is not already favourited
    # by either test user.
    for listing in listings:
        listing_id = listing.get(
            "listing_id"
        )

        if (
            listing_id
            and listing_id
            not in blocked_ids
            and listing.get("is_live")
            is True
        ):
            return listing_id

    raise RuntimeError(
        "Could not find a safe listing "
        "for the favourites test."
    )


def main():
    if not USER_2:
        raise RuntimeError(
            "IVY_DEMO_USER_2 is missing "
            "from .env. Add the second "
            "provided demo account before "
            "running this isolation test."
        )

    listings = load_listings()

    print(
        "=== Favourites Contract Probe ==="
    )

    print(
        "This test restores the test "
        "favourite before finishing."
    )

    print(
        "Passwords, API keys and tokens "
        "are not printed."
    )

    # ---------------------------------
    # Login both users
    # ---------------------------------

    session_1, token_1 = login(
        USER_1
    )

    session_2, token_2 = login(
        USER_2
    )

    # ---------------------------------
    # Capture initial state
    # ---------------------------------

    _, initial_user_1 = (
        get_favourites(
            session_1,
            token_1,
            "user 1 initial",
        )
    )

    _, initial_user_2 = (
        get_favourites(
            session_2,
            token_2,
            "user 2 initial",
        )
    )

    blocked_ids = (
        initial_user_1
        | initial_user_2
    )

    test_listing = (
        choose_test_listing(
            listings,
            blocked_ids,
        )
    )

    print()
    print(
        "=== SAFE TEST LISTING ==="
    )

    print(
        "listing_id:",
        test_listing,
    )

    print(
        "Initially in user 1:",
        test_listing
        in initial_user_1,
    )

    print(
        "Initially in user 2:",
        test_listing
        in initial_user_2,
    )

    added = False

    try:
        # -----------------------------
        # Add to user 1
        # -----------------------------

        add_response = (
            add_favourite(
                session_1,
                token_1,
                test_listing,
            )
        )

        added = (
            200
            <= add_response.status_code
            < 300
        )

        _, after_add_user_1 = (
            get_favourites(
                session_1,
                token_1,
                "user 1 after add",
            )
        )

        print()
        print(
            "Favourite appears for user 1:",
            test_listing
            in after_add_user_1,
        )

        print(
            "User 1 count increased by 1:",
            len(after_add_user_1)
            == len(initial_user_1) + 1,
        )

        # -----------------------------
        # Simulate page reload:
        # new HTTP session, same token.
        # -----------------------------

        reload_session = (
            requests.Session()
        )

        _, reload_ids = (
            get_favourites(
                reload_session,
                token_1,
                (
                    "user 1 simulated "
                    "page reload"
                ),
            )
        )

        print()
        print(
            "Persists across reload:",
            test_listing
            in reload_ids,
        )

        # -----------------------------
        # Check user isolation
        # -----------------------------

        _, after_add_user_2 = (
            get_favourites(
                session_2,
                token_2,
                (
                    "user 2 after "
                    "user 1 add"
                ),
            )
        )

        print()
        print(
            "Test listing absent "
            "from user 2:",
            test_listing
            not in after_add_user_2,
        )

        print(
            "User 2 state unchanged:",
            after_add_user_2
            == initial_user_2,
        )

        # -----------------------------
        # Logout / login persistence
        # -----------------------------

        logout(
            session_1,
            token_1,
        )

        relogin_session, (
            relogin_token
        ) = login(
            USER_1
        )

        _, relogin_ids = (
            get_favourites(
                relogin_session,
                relogin_token,
                (
                    "user 1 after "
                    "logout and relogin"
                ),
            )
        )

        print()
        print(
            "Persists after logout/login:",
            test_listing
            in relogin_ids,
        )

        # -----------------------------
        # Delete
        # -----------------------------

        delete_response = (
            delete_favourite(
                relogin_session,
                relogin_token,
                test_listing,
                "normal cleanup",
            )
        )

        if (
            200
            <= delete_response.status_code
            < 300
        ):
            added = False

        _, after_delete = (
            get_favourites(
                relogin_session,
                relogin_token,
                "user 1 after delete",
            )
        )

        print()
        print(
            "Removed from user 1:",
            test_listing
            not in after_delete,
        )

        print(
            "User 1 restored to "
            "initial ID set:",
            after_delete
            == initial_user_1,
        )

        _, final_user_2 = (
            get_favourites(
                session_2,
                token_2,
                "user 2 final",
            )
        )

        print()
        print(
            "User 2 still unchanged:",
            final_user_2
            == initial_user_2,
        )

    finally:
        # Emergency cleanup if the
        # normal path failed after add.
        if added:
            print()
            print(
                "=== EMERGENCY CLEANUP ==="
            )

            try:
                cleanup_session, (
                    cleanup_token
                ) = login(
                    USER_1
                )

                cleanup_response = (
                    delete_favourite(
                        cleanup_session,
                        cleanup_token,
                        test_listing,
                        "emergency cleanup",
                    )
                )

                print(
                    "Emergency cleanup "
                    "successful:",
                    (
                        200
                        <= cleanup_response
                        .status_code
                        < 300
                    ),
                )

            except Exception as error:
                print(
                    "WARNING: emergency "
                    "cleanup failed:"
                )

                print(
                    repr(error)
                )

    print()
    print(
        "Do not update the audit "
        "or commit yet."
    )

    print(
        "Review the complete "
        "behaviour first."
    )


if __name__ == "__main__":
    main()