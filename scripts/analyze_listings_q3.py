import json
from collections import Counter
from pathlib import Path


LISTINGS_PATH = Path("data/raw/listings.json")


def load_listings():
    with LISTINGS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        snapshot = json.load(file)

    return (
        snapshot["metadata"],
        snapshot["results"],
    )


def main():
    metadata, listings = load_listings()

    print("=== Q3 Active Listings Analysis ===")

    print()
    print(f"Listings loaded: {len(listings)}")

    if len(listings) != metadata["records_retrieved"]:
        raise RuntimeError(
            "Snapshot metadata does not match stored listings."
        )

    if metadata["final_has_more"] is not False:
        raise RuntimeError(
            "Listings snapshot did not reach the end "
            "of pagination."
        )

    missing_is_live = []
    non_boolean_is_live = []

    active_ids = []
    inactive_ids = []

    raw_values = Counter()

    for listing in listings:
        listing_id = listing.get("listing_id")

        if "is_live" not in listing:
            missing_is_live.append(
                listing_id
            )
            continue

        value = listing["is_live"]

        raw_values[
            f"{type(value).__name__}:{repr(value)}"
        ] += 1

        if type(value) is not bool:
            non_boolean_is_live.append(
                listing_id
            )
            continue

        if value is True:
            active_ids.append(
                listing_id
            )
        else:
            inactive_ids.append(
                listing_id
            )

    print()
    print("=== is_live Validation ===")

    print(
        f"Missing is_live: "
        f"{len(missing_is_live)}"
    )

    print(
        f"Non-boolean is_live: "
        f"{len(non_boolean_is_live)}"
    )

    print()
    print("Observed raw values:")

    for value, count in sorted(
        raw_values.items()
    ):
        print(
            f"{value}: {count}"
        )

    print()
    print("=== Listing Status Counts ===")

    print(
        f"Active listings (is_live is True): "
        f"{len(active_ids)}"
    )

    print(
        f"Inactive listings (is_live is False): "
        f"{len(inactive_ids)}"
    )

    print()

    if inactive_ids:
        print(
            "First 20 inactive listing IDs:"
        )

        for listing_id in inactive_ids[:20]:
            print(listing_id)

    print()
    print("=== Q3 Candidate Answer ===")

    print(
        f"active_listings: {len(active_ids)}"
    )


if __name__ == "__main__":
    main()