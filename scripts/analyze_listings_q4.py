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


def is_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
    )


def main():
    metadata, listings = load_listings()

    print("=== Q4 Corrupt Listing Investigation ===")
    print()
    print(f"Listings loaded: {len(listings)}")

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

    # Hard violations:
    # These represent things that are mathematically
    # or physically impossible under the field meaning.
    hard_violations = defaultdict(list)

    # Softer anomalies:
    # Interesting, but NOT automatically corrupt.
    suspicious = defaultdict(list)

    type_issues = defaultdict(list)
    missing_fields = defaultdict(list)

    required_fields = [
        "listing_id",
        "price",
        "carpet_area",
        "super_built_up_area",
        "bedroom",
        "bathroom",
        "floor",
        "total_floors",
        "latitude",
        "longitude",
    ]

    # The actual API may use super_builtup_area instead
    # of the documented super_built_up_area spelling.
    area_field_counts = Counter()

    for listing in listings:
        listing_id = listing.get("listing_id")

        if "super_built_up_area" in listing:
            area_field_counts[
                "super_built_up_area"
            ] += 1

        if "super_builtup_area" in listing:
            area_field_counts[
                "super_builtup_area"
            ] += 1

        for field in required_fields:
            if field == "super_built_up_area":
                continue

            if field not in listing:
                missing_fields[field].append(
                    listing_id
                )

        price = listing.get("price")
        carpet = listing.get("carpet_area")

        super_area = listing.get(
            "super_built_up_area"
        )

        if super_area is None:
            super_area = listing.get(
                "super_builtup_area"
            )

        bedroom = listing.get("bedroom")
        bathroom = listing.get("bathroom")
        balcony = listing.get("balcony")
        floor = listing.get("floor")
        total_floors = listing.get(
            "total_floors"
        )
        parking = listing.get(
            "covered_parking"
        )

        latitude = listing.get("latitude")
        longitude = listing.get(
            "longitude"
        )

        numeric_fields = {
            "price": price,
            "carpet_area": carpet,
            "super_area": super_area,
            "bedroom": bedroom,
            "bathroom": bathroom,
            "floor": floor,
            "total_floors": total_floors,
            "latitude": latitude,
            "longitude": longitude,
        }

        for field, value in numeric_fields.items():
            if (
                value is not None
                and not is_number(value)
            ):
                type_issues[field].append(
                    listing_id
                )

        # -------------------------------------------------
        # HARD IMPOSSIBILITIES
        # -------------------------------------------------

        if is_number(price) and price <= 0:
            hard_violations[
                "non_positive_price"
            ].append(listing_id)

        if is_number(carpet) and carpet <= 0:
            hard_violations[
                "non_positive_carpet_area"
            ].append(listing_id)

        if (
            is_number(super_area)
            and super_area <= 0
        ):
            hard_violations[
                "non_positive_super_area"
            ].append(listing_id)

        if (
            is_number(bedroom)
            and bedroom < 0
        ):
            hard_violations[
                "negative_bedroom"
            ].append(listing_id)

        if (
            is_number(bathroom)
            and bathroom < 0
        ):
            hard_violations[
                "negative_bathroom"
            ].append(listing_id)

        if (
            is_number(balcony)
            and balcony < 0
        ):
            hard_violations[
                "negative_balcony"
            ].append(listing_id)

        if (
            is_number(parking)
            and parking < 0
        ):
            hard_violations[
                "negative_parking"
            ].append(listing_id)

        if (
            is_number(latitude)
            and not (-90 <= latitude <= 90)
        ):
            hard_violations[
                "invalid_latitude"
            ].append(listing_id)

        if (
            is_number(longitude)
            and not (-180 <= longitude <= 180)
        ):
            hard_violations[
                "invalid_longitude"
            ].append(listing_id)

        # If both are ordinary non-negative floor numbers,
        # current floor cannot exceed the building's
        # total number of floors.
        if (
            is_number(floor)
            and is_number(total_floors)
            and floor >= 0
            and total_floors >= 0
            and floor > total_floors
        ):
            hard_violations[
                "floor_above_total_floors"
            ].append(listing_id)

        # -------------------------------------------------
        # SUSPICIOUS, BUT NOT YET CLASSIFIED AS CORRUPT
        # -------------------------------------------------

        if (
            is_number(carpet)
            and is_number(super_area)
            and carpet > 0
            and super_area > 0
            and carpet > super_area
        ):
            suspicious[
                "carpet_gt_super_area"
            ].append(listing_id)

        if (
            is_number(bedroom)
            and bedroom > 10
        ):
            suspicious[
                "bedroom_gt_10"
            ].append(listing_id)

        if (
            is_number(bathroom)
            and bathroom > 15
        ):
            suspicious[
                "bathroom_gt_15"
            ].append(listing_id)

        if (
            is_number(carpet)
            and carpet > 20_000
        ):
            suspicious[
                "carpet_area_gt_20000"
            ].append(listing_id)

        if (
            is_number(super_area)
            and super_area > 30_000
        ):
            suspicious[
                "super_area_gt_30000"
            ].append(listing_id)

        if (
            is_number(price)
            and price > 1_000_000_000
        ):
            suspicious[
                "price_gt_100_crore"
            ].append(listing_id)

    print()
    print("=== Area Field Names ===")

    for field, count in (
        area_field_counts.items()
    ):
        print(
            f"{field}: {count}"
        )

    print()
    print("=== Missing Fields ===")

    if not missing_fields:
        print("None")
    else:
        for field, ids in (
            sorted(missing_fields.items())
        ):
            print(
                f"{field}: {len(ids)}"
            )

    print()
    print("=== Numeric Type Issues ===")

    if not type_issues:
        print("None")
    else:
        for field, ids in (
            sorted(type_issues.items())
        ):
            print(
                f"{field}: {len(ids)}"
            )

    print()
    print("=== Hard Impossibility Checks ===")

    if not hard_violations:
        print("No hard violations found.")
    else:
        for rule, ids in (
            sorted(hard_violations.items())
        ):
            print()
            print(
                f"{rule}: {len(ids)}"
            )

            for listing_id in ids[:30]:
                print(
                    f"  {listing_id}"
                )

    print()
    print("=== Suspicious Checks ===")

    if not suspicious:
        print("No suspicious records found.")
    else:
        for rule, ids in (
            sorted(suspicious.items())
        ):
            print()
            print(
                f"{rule}: {len(ids)}"
            )

            for listing_id in ids[:30]:
                print(
                    f"  {listing_id}"
                )

    hard_ids = sorted(
        {
            listing_id
            for ids in hard_violations.values()
            for listing_id in ids
        }
    )

    suspicious_ids = sorted(
        {
            listing_id
            for ids in suspicious.values()
            for listing_id in ids
        }
    )

    print()
    print("=== Summary ===")

    print(
        f"Unique hard-impossibility IDs: "
        f"{len(hard_ids)}"
    )

    print(
        f"Unique suspicious IDs: "
        f"{len(suspicious_ids)}"
    )

    print()
    print(
        "Hard IDs are candidates only; "
        "do not finalize Q4 yet."
    )


if __name__ == "__main__":
    main()
    