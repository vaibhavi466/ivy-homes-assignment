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


def median_or_none(values):
    if not values:
        return None

    return median(values)


def normalize_magichomes_area(
    listing,
    field,
):
    value = listing.get(field)

    if not is_number(value):
        return None

    carpet = listing.get("carpet_area")
    super_area = listing.get(
        "super_built_up_area"
    )

    is_sqm_candidate = (
        listing.get("website")
        == "magichomes"
        and is_number(carpet)
        and is_number(super_area)
        and carpet < 300
        and super_area < 400
    )

    if is_sqm_candidate:
        return (
            value * SQFT_PER_SQM
        )

    return float(value)


def main():
    listings = load_listings()

    magic = [
        listing
        for listing in listings
        if listing.get("website")
        == "magichomes"
    ]

    print(
        "=== Magichomes Area Unit Verification ==="
    )

    print()
    print(
        f"Magichomes listings: {len(magic)}"
    )

    # -------------------------------------------------
    # Compare the two low-area conditions
    # -------------------------------------------------

    low_carpet_ids = {
        listing["listing_id"]
        for listing in magic
        if (
            is_number(
                listing.get("carpet_area")
            )
            and listing["carpet_area"] < 300
        )
    }

    low_super_ids = {
        listing["listing_id"]
        for listing in magic
        if (
            is_number(
                listing.get(
                    "super_built_up_area"
                )
            )
            and listing[
                "super_built_up_area"
            ] < 400
        )
    }

    both_ids = (
        low_carpet_ids
        & low_super_ids
    )

    print()
    print(
        "=== Candidate Set Agreement ==="
    )

    print(
        f"carpet_area < 300: "
        f"{len(low_carpet_ids)}"
    )

    print(
        f"super_built_up_area < 400: "
        f"{len(low_super_ids)}"
    )

    print(
        f"intersection: "
        f"{len(both_ids)}"
    )

    print(
        "carpet-only IDs: "
        f"{len(
            low_carpet_ids
            - low_super_ids
        )}"
    )

    print(
        "super-only IDs: "
        f"{len(
            low_super_ids
            - low_carpet_ids
        )}"
    )

    # -------------------------------------------------
    # Boundary inspection
    # -------------------------------------------------

    carpet_values = sorted(
        {
            listing["carpet_area"]
            for listing in magic
            if is_number(
                listing.get("carpet_area")
            )
        }
    )

    super_values = sorted(
        {
            listing[
                "super_built_up_area"
            ]
            for listing in magic
            if is_number(
                listing.get(
                    "super_built_up_area"
                )
            )
        }
    )

    print()
    print(
        "=== Carpet Area Boundary ==="
    )

    low_carpet_values = [
        value
        for value in carpet_values
        if value < 300
    ]

    high_carpet_values = [
        value
        for value in carpet_values
        if value >= 300
    ]

    print(
        "Largest values below 300:"
    )
    print(
        low_carpet_values[-15:]
    )

    print(
        "Smallest values >= 300:"
    )
    print(
        high_carpet_values[:15]
    )

    print()
    print(
        "=== Super Built-up Area Boundary ==="
    )

    low_super_values = [
        value
        for value in super_values
        if value < 400
    ]

    high_super_values = [
        value
        for value in super_values
        if value >= 400
    ]

    print(
        "Largest values below 400:"
    )
    print(
        low_super_values[-15:]
    )

    print(
        "Smallest values >= 400:"
    )
    print(
        high_super_values[:15]
    )

    # -------------------------------------------------
    # Candidate distribution
    # -------------------------------------------------

    candidate_records = [
        listing
        for listing in magic
        if listing["listing_id"]
        in both_ids
    ]

    print()
    print(
        "=== Candidate Distribution by BHK ==="
    )

    bedroom_counts = Counter(
        listing.get("bedroom")
        for listing in candidate_records
    )

    for bedroom, count in sorted(
        bedroom_counts.items(),
        key=lambda item:
            (
                item[0] is None,
                item[0]
                if item[0] is not None
                else -1,
            ),
    ):
        print(
            f"{bedroom} BHK: {count}"
        )

    # -------------------------------------------------
    # Compare medians after normalization
    # -------------------------------------------------

    print()
    print(
        "=== BHK Median Comparison ==="
    )

    non_magic = [
        listing
        for listing in listings
        if listing.get("website")
        != "magichomes"
    ]

    for bedroom in range(1, 6):
        reference_carpet = [
            listing["carpet_area"]
            for listing in non_magic
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

        magic_raw = [
            listing["carpet_area"]
            for listing in magic
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

        magic_normalized = [
            normalize_magichomes_area(
                listing,
                "carpet_area",
            )
            for listing in magic
            if listing.get("bedroom")
            == bedroom
        ]

        magic_normalized = [
            value
            for value
            in magic_normalized
            if value is not None
        ]

        converted_count = sum(
            1
            for listing in magic
            if (
                listing.get("bedroom")
                == bedroom
                and listing["listing_id"]
                in both_ids
            )
        )

        ref_med = median_or_none(
            reference_carpet
        )

        raw_med = median_or_none(
            magic_raw
        )

        normalized_med = median_or_none(
            magic_normalized
        )

        print()
        print(
            f"{bedroom} BHK"
        )

        print(
            f"  converted records: "
            f"{converted_count}"
        )

        print(
            f"  non-magichomes median sqft: "
            f"{ref_med:.2f}"
        )

        print(
            f"  magichomes raw median: "
            f"{raw_med:.2f}"
        )

        print(
            "  magichomes normalized "
            f"median sqft: "
            f"{normalized_med:.2f}"
        )

        difference_pct = (
            abs(
                normalized_med
                - ref_med
            )
            * 100.0
            / ref_med
        )

        print(
            "  normalized vs reference "
            f"difference: "
            f"{difference_pct:.2f}%"
        )

    # -------------------------------------------------
    # 2BHK price-per-sqft comparison
    # Important for later Q6.
    # -------------------------------------------------

    print()
    print(
        "=== 2BHK Price-per-sqft Check ==="
    )

    by_website = defaultdict(list)

    for listing in listings:
        if listing.get("bedroom") != 2:
            continue

        price = listing.get("price")

        carpet = normalize_magichomes_area(
            listing,
            "carpet_area",
        )

        if (
            not is_number(price)
            or price <= 0
            or not is_number(carpet)
            or carpet <= 0
        ):
            continue

        ppsf = (
            price / carpet
        )

        by_website[
            listing.get("website")
        ].append(ppsf)

    for website in sorted(
        by_website
    ):
        values = by_website[website]

        print(
            f"{website}: "
            f"n={len(values)}, "
            f"median_ppsf="
            f"{median(values):.2f}"
        )

    print()
    print(
        "Do not apply normalization "
        "globally yet."
    )


if __name__ == "__main__":
    main()