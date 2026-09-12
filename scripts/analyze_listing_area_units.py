import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median


LISTINGS_PATH = Path("data/raw/listings.json")

SQFT_PER_SQM = 10.7639104167


def load_listings():
    with LISTINGS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["results"]


def is_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
    )


def main():
    listings = load_listings()

    print(
        "=== Listing Area Unit Investigation ==="
    )

    print()
    print(
        f"Listings loaded: {len(listings)}"
    )

    by_website = defaultdict(list)

    for listing in listings:
        by_website[
            listing.get("website")
        ].append(listing)

    # -------------------------------------------------
    # Magnitude buckets by website
    # -------------------------------------------------

    print()
    print(
        "=== Carpet Area Magnitude by Website ==="
    )

    for website in sorted(by_website):
        records = by_website[website]

        values = [
            record.get("carpet_area")
            for record in records
            if is_number(
                record.get("carpet_area")
            )
        ]

        buckets = Counter()

        for value in values:
            if value < 100:
                buckets["<100"] += 1
            elif value < 300:
                buckets["100-299"] += 1
            elif value < 500:
                buckets["300-499"] += 1
            else:
                buckets[">=500"] += 1

        print()
        print(
            f"{website}: {len(values)} records"
        )
        print(
            f"  <100: {buckets['<100']}"
        )
        print(
            f"  100-299: {buckets['100-299']}"
        )
        print(
            f"  300-499: {buckets['300-499']}"
        )
        print(
            f"  >=500: {buckets['>=500']}"
        )
        print(
            f"  median: {median(values):.2f}"
        )

    print()
    print(
        "=== Super Built-up Area Magnitude by Website ==="
    )

    for website in sorted(by_website):
        records = by_website[website]

        values = [
            record.get(
                "super_built_up_area"
            )
            for record in records
            if is_number(
                record.get(
                    "super_built_up_area"
                )
            )
        ]

        buckets = Counter()

        for value in values:
            if value < 150:
                buckets["<150"] += 1
            elif value < 400:
                buckets["150-399"] += 1
            elif value < 600:
                buckets["400-599"] += 1
            else:
                buckets[">=600"] += 1

        print()
        print(
            f"{website}: {len(values)} records"
        )
        print(
            f"  <150: {buckets['<150']}"
        )
        print(
            f"  150-399: {buckets['150-399']}"
        )
        print(
            f"  400-599: {buckets['400-599']}"
        )
        print(
            f"  >=600: {buckets['>=600']}"
        )
        print(
            f"  median: {median(values):.2f}"
        )

    # -------------------------------------------------
    # BHK-specific medians
    # -------------------------------------------------

    print()
    print(
        "=== Carpet Area Median by Website and BHK ==="
    )

    for bedroom in range(1, 6):
        print()
        print(
            f"--- {bedroom} BHK ---"
        )

        for website in sorted(by_website):
            values = [
                listing["carpet_area"]
                for listing in by_website[
                    website
                ]
                if (
                    listing.get("bedroom")
                    == bedroom
                    and is_number(
                        listing.get(
                            "carpet_area"
                        )
                    )
                )
            ]

            if not values:
                continue

            print(
                f"{website}: "
                f"n={len(values)}, "
                f"median={median(values):.2f}"
            )

    # -------------------------------------------------
    # Small-area records
    # -------------------------------------------------

    small_carpet = [
        listing
        for listing in listings
        if (
            is_number(
                listing.get("carpet_area")
            )
            and listing["carpet_area"] < 300
        )
    ]

    print()
    print(
        "=== Records With carpet_area < 300 ==="
    )

    print(
        f"Count: {len(small_carpet)}"
    )

    small_by_website = Counter(
        listing.get("website")
        for listing in small_carpet
    )

    print(
        "By website:"
    )

    for website, count in sorted(
        small_by_website.items()
    ):
        print(
            f"  {website}: {count}"
        )

    print()
    print(
        "First 30 small-area records:"
    )

    for listing in sorted(
        small_carpet,
        key=lambda item:
            item["carpet_area"],
    )[:30]:
        carpet = listing["carpet_area"]

        super_area = listing.get(
            "super_built_up_area"
        )

        print(
            {
                "listing_id":
                    listing.get("listing_id"),
                "website":
                    listing.get("website"),
                "bedroom":
                    listing.get("bedroom"),
                "carpet_area":
                    carpet,
                "carpet_if_sqm_to_sqft":
                    round(
                        carpet
                        * SQFT_PER_SQM,
                        2,
                    ),
                "super_built_up_area":
                    super_area,
                "super_if_sqm_to_sqft":
                    (
                        round(
                            super_area
                            * SQFT_PER_SQM,
                            2,
                        )
                        if is_number(
                            super_area
                        )
                        else None
                    ),
            }
        )

    # -------------------------------------------------
    # Look for natural gaps
    # -------------------------------------------------

    carpet_values = sorted(
        {
            listing["carpet_area"]
            for listing in listings
            if is_number(
                listing.get("carpet_area")
            )
        }
    )

    gaps = []

    for left, right in zip(
        carpet_values,
        carpet_values[1:],
    ):
        gaps.append(
            (
                right - left,
                left,
                right,
            )
        )

    gaps.sort(
        reverse=True
    )

    print()
    print(
        "=== Largest Carpet-Area Value Gaps ==="
    )

    for gap, left, right in gaps[:15]:
        print(
            f"{left} -> {right} "
            f"(gap {gap})"
        )


if __name__ == "__main__":
    main()