import json
from pathlib import Path


LISTINGS_PATH = Path("data/raw/listings.json")


CANDIDATE_IDS = {
    # floor > total_floors
    "100-6001968",
    "100-6000323",
    "DWE-6001015",
    "SQU-6001477",
    "MAG-6000453",
    "DWE-6002846",

    # non-positive price
    "MAG-6000631",
    "DWE-6002663",
    "100-6001461",
    "ZER-6000669",
    "SQU-6003044",
    "100-6002071",

    # carpet > super built-up area
    "MAG-6000527",
    "100-6000338",
    "ZER-6000468",
    "MAG-6001135",
    "DWE-6000010",
    "MAG-6002834",
}


def load_listings():
    with LISTINGS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        snapshot = json.load(file)

    return snapshot["results"]


def main():
    listings = load_listings()

    by_id = {
        listing["listing_id"]: listing
        for listing in listings
    }

    print("=== Q4 Candidate Inspection ===")
    print(
        f"Candidate IDs requested: "
        f"{len(CANDIDATE_IDS)}"
    )

    missing = (
        CANDIDATE_IDS - set(by_id)
    )

    print(
        f"Candidate IDs missing from snapshot: "
        f"{len(missing)}"
    )

    if missing:
        for listing_id in sorted(missing):
            print(
                f"  {listing_id}"
            )

    for listing_id in sorted(
        CANDIDATE_IDS
    ):
        listing = by_id.get(
            listing_id
        )

        if not listing:
            continue

        print()
        print("=" * 70)
        print(
            f"Listing ID: {listing_id}"
        )

        fields = {
            "title":
                listing.get("title"),
            "property_type":
                listing.get("property_type"),
            "locality":
                listing.get("locality"),
            "price":
                listing.get("price"),
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
            "is_live":
                listing.get("is_live"),
            "project_id":
                listing.get("project_id"),
        }

        for key, value in fields.items():
            print(
                f"{key}: {value}"
            )

        price = listing.get("price")
        floor = listing.get("floor")
        total_floors = listing.get(
            "total_floors"
        )
        carpet = listing.get(
            "carpet_area"
        )
        super_area = listing.get(
            "super_built_up_area"
        )

        violations = []

        if (
            isinstance(price, (int, float))
            and price <= 0
        ):
            violations.append(
                f"NON_POSITIVE_PRICE={price}"
            )

        if (
            isinstance(floor, (int, float))
            and isinstance(
                total_floors,
                (int, float),
            )
            and floor > total_floors
        ):
            violations.append(
                "FLOOR_GT_TOTAL="
                f"{floor}>{total_floors}"
            )

        if (
            isinstance(carpet, (int, float))
            and isinstance(
                super_area,
                (int, float),
            )
            and carpet > super_area
        ):
            violations.append(
                "CARPET_GT_SUPER="
                f"{carpet}>{super_area}"
            )

        print(
            "violations: "
            + (
                ", ".join(violations)
                if violations
                else "none"
            )
        )


if __name__ == "__main__":
    main()