import json
from pathlib import Path


LISTINGS_PATH = Path("data/raw/listings.json")


def load_snapshot(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Snapshot not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def main():
    snapshot = load_snapshot(LISTINGS_PATH)

    metadata = snapshot["metadata"]
    listings = snapshot["results"]

    retrieved_count = len(listings)

    unique_listing_ids = {
        listing["listing_id"]
        for listing in listings
    }

    if retrieved_count != metadata["records_retrieved"]:
        raise RuntimeError(
            "Snapshot metadata does not match stored records."
        )

    if len(unique_listing_ids) != retrieved_count:
        raise RuntimeError(
            "Duplicate listing_id values exist in the "
            "retrieved listings snapshot."
        )

    if metadata["final_has_more"] is not False:
        raise RuntimeError(
            "Snapshot did not reach the end of pagination."
        )

    print("=== Baseline Answers ===")
    print(
        f"total_listing_records: {retrieved_count}"
    )

    print()
    print("Validation:")
    print(
        f"stored records: {retrieved_count}"
    )
    print(
        f"unique listing IDs: {len(unique_listing_ids)}"
    )
    print(
        f"final has_more: {metadata['final_has_more']}"
    )
    print(
        "reported totals seen: "
        f"{metadata['reported_totals_seen']}"
    )


if __name__ == "__main__":
    main()