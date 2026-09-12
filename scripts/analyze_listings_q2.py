import json
from collections import Counter, defaultdict
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


def normalize_text(value):
    if value is None:
        return None

    return " ".join(
        str(value)
        .strip()
        .lower()
        .split()
    )


def rounded_coordinate(value):
    if not isinstance(value, (int, float)):
        return None

    return round(value, 5)


def physical_signature_strict(listing):
    """
    A deliberately strict property fingerprint.

    Excludes:
    - listing_id
    - website
    - listing_url
    - seller information
    - price
    - description
    - posted_at
    - is_live

    Includes physical/property attributes.
    """

    return (
        normalize_text(
            listing.get("locality")
        ),
        normalize_text(
            listing.get("apartment_name")
        ),
        normalize_text(
            listing.get("property_type")
        ),
        listing.get("bedroom"),
        listing.get("bathroom"),
        listing.get("balcony"),
        listing.get("floor"),
        listing.get("total_floors"),
        listing.get("carpet_area"),
        listing.get("super_built_up_area"),
        rounded_coordinate(
            listing.get("latitude")
        ),
        rounded_coordinate(
            listing.get("longitude")
        ),
    )


def physical_signature_without_name(listing):
    """
    Same idea, but does not depend on apartment_name.
    Useful if names vary across websites.
    """

    return (
        normalize_text(
            listing.get("locality")
        ),
        normalize_text(
            listing.get("property_type")
        ),
        listing.get("bedroom"),
        listing.get("bathroom"),
        listing.get("balcony"),
        listing.get("floor"),
        listing.get("total_floors"),
        listing.get("carpet_area"),
        listing.get("super_built_up_area"),
        rounded_coordinate(
            listing.get("latitude")
        ),
        rounded_coordinate(
            listing.get("longitude")
        ),
    )


def coordinate_signature(listing):
    return (
        rounded_coordinate(
            listing.get("latitude")
        ),
        rounded_coordinate(
            listing.get("longitude")
        ),
    )


def main():
    metadata, listings = load_listings()

    print(
        "=== Q2 Unique Property Investigation ==="
    )

    print()
    print(
        f"Listings loaded: {len(listings)}"
    )

    if (
        len(listings)
        != metadata["records_retrieved"]
    ):
        raise RuntimeError(
            "Snapshot metadata does not match "
            "stored listings."
        )

    if metadata["final_has_more"] is not False:
        raise RuntimeError(
            "Listings snapshot did not reach "
            "the end of pagination."
        )

    print()
    print("=== Website Distribution ===")

    website_counts = Counter(
        listing.get("website")
        for listing in listings
    )

    for website, count in sorted(
        website_counts.items(),
        key=lambda item: str(item[0]),
    ):
        print(
            f"{website}: {count}"
        )

    # -------------------------------------------------
    # STRICT PHYSICAL SIGNATURE
    # -------------------------------------------------

    strict_groups = defaultdict(list)

    for listing in listings:
        strict_groups[
            physical_signature_strict(
                listing
            )
        ].append(listing)

    strict_duplicate_groups = [
        group
        for group in strict_groups.values()
        if len(group) > 1
    ]

    strict_duplicate_records = sum(
        len(group)
        for group in strict_duplicate_groups
    )

    print()
    print(
        "=== Strict Physical Signature ==="
    )

    print(
        f"Unique signatures: "
        f"{len(strict_groups)}"
    )

    print(
        f"Duplicate groups: "
        f"{len(strict_duplicate_groups)}"
    )

    print(
        f"Records inside duplicate groups: "
        f"{strict_duplicate_records}"
    )

    print(
        "Duplicate records beyond one-per-group: "
        f"{sum(
            len(group) - 1
            for group in strict_duplicate_groups
        )}"
    )

    # -------------------------------------------------
    # SAME SIGNATURE WITHOUT APARTMENT NAME
    # -------------------------------------------------

    no_name_groups = defaultdict(list)

    for listing in listings:
        no_name_groups[
            physical_signature_without_name(
                listing
            )
        ].append(listing)

    no_name_duplicate_groups = [
        group
        for group in no_name_groups.values()
        if len(group) > 1
    ]

    print()
    print(
        "=== Physical Signature Without Apartment Name ==="
    )

    print(
        f"Unique signatures: "
        f"{len(no_name_groups)}"
    )

    print(
        f"Duplicate groups: "
        f"{len(no_name_duplicate_groups)}"
    )

    print(
        "Duplicate records beyond one-per-group: "
        f"{sum(
            len(group) - 1
            for group in no_name_duplicate_groups
        )}"
    )

    # -------------------------------------------------
    # COORDINATE DUPLICATION
    # -------------------------------------------------

    coordinate_groups = defaultdict(list)

    for listing in listings:
        coordinate_groups[
            coordinate_signature(
                listing
            )
        ].append(listing)

    coordinate_duplicate_groups = [
        group
        for key, group
        in coordinate_groups.items()
        if (
            key != (None, None)
            and len(group) > 1
        )
    ]

    print()
    print(
        "=== Exact Coordinate Reuse ==="
    )

    print(
        f"Coordinate groups with >1 record: "
        f"{len(coordinate_duplicate_groups)}"
    )

    print(
        "Records in repeated coordinate groups: "
        f"{sum(
            len(group)
            for group in coordinate_duplicate_groups
        )}"
    )

    # -------------------------------------------------
    # INSPECT FIRST STRICT DUPLICATE GROUPS
    # -------------------------------------------------

    print()
    print(
        "=== First 20 Strict Duplicate Groups ==="
    )

    groups_sorted = sorted(
        strict_duplicate_groups,
        key=lambda group: (
            -len(group),
            group[0].get("listing_id", ""),
        ),
    )

    for index, group in enumerate(
        groups_sorted[:20],
        start=1,
    ):
        print()
        print(
            f"--- Group {index} "
            f"({len(group)} records) ---"
        )

        for listing in sorted(
            group,
            key=lambda item:
                item.get("listing_id", ""),
        ):
            print(
                {
                    "listing_id":
                        listing.get("listing_id"),
                    "website":
                        listing.get("website"),
                    "listing_url":
                        listing.get("listing_url"),
                    "apartment_name":
                        listing.get("apartment_name"),
                    "locality":
                        listing.get("locality"),
                    "property_type":
                        listing.get("property_type"),
                    "bedroom":
                        listing.get("bedroom"),
                    "bathroom":
                        listing.get("bathroom"),
                    "floor":
                        listing.get("floor"),
                    "total_floors":
                        listing.get("total_floors"),
                    "carpet_area":
                        listing.get("carpet_area"),
                    "super_built_up_area":
                        listing.get(
                            "super_built_up_area"
                        ),
                    "latitude":
                        listing.get("latitude"),
                    "longitude":
                        listing.get("longitude"),
                    "price":
                        listing.get("price"),
                    "posted_by_contact":
                        listing.get(
                            "posted_by_contact"
                        ),
                    "project_id":
                        listing.get("project_id"),
                }
            )

    # -------------------------------------------------
    # CROSS-WEBSITE DUPLICATE GROUPS
    # -------------------------------------------------

    cross_website_groups = []

    for group in strict_duplicate_groups:
        websites = {
            listing.get("website")
            for listing in group
        }

        if len(websites) > 1:
            cross_website_groups.append(
                group
            )

    print()
    print(
        "=== Cross-Website Strict Duplicate Groups ==="
    )

    print(
        f"Groups: "
        f"{len(cross_website_groups)}"
    )

    print(
        "Records: "
        f"{sum(
            len(group)
            for group in cross_website_groups
        )}"
    )

    print()
    print(
        "Do not finalize Q2 yet."
    )


if __name__ == "__main__":
    main()