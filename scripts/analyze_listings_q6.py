import json
from collections import Counter
from pathlib import Path
from statistics import mean, median


LISTINGS_PATH = Path(
    "data/raw/listings.json"
)

SQFT_PER_SQM = 10.7639104167


CORRUPT_IDS = {
    "100-6000323",
    "100-6000338",
    "100-6001461",
    "100-6001968",
    "100-6002071",
    "DWE-6000010",
    "DWE-6001015",
    "DWE-6002663",
    "DWE-6002846",
    "MAG-6000453",
    "MAG-6000527",
    "MAG-6000631",
    "MAG-6001135",
    "MAG-6002834",
    "SQU-6001477",
    "SQU-6003044",
    "ZER-6000468",
    "ZER-6000669",
}


FAKE_IDS = {
    "100-6000578",
    "100-6000678",
    "100-6001599",
    "MAG-6002472",
    "MAG-6002941",
    "SQU-6000395",
}


def load_listings():
    with LISTINGS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(
            file
        )["results"]


def is_number(value):
    return (
        isinstance(
            value,
            (int, float),
        )
        and not isinstance(
            value,
            bool,
        )
    )


def is_magic_sqm_record(
    listing,
):
    carpet = listing.get(
        "carpet_area"
    )

    super_area = listing.get(
        "super_built_up_area"
    )

    return (
        listing.get("website")
        == "magichomes"
        and is_number(carpet)
        and is_number(super_area)
        and carpet < 300
        and super_area < 400
    )


def normalized_carpet_sqft(
    listing,
):
    carpet = listing.get(
        "carpet_area"
    )

    if not is_number(carpet):
        return None

    if is_magic_sqm_record(
        listing
    ):
        return (
            float(carpet)
            * SQFT_PER_SQM
        )

    return float(carpet)


def percentile(
    values,
    fraction,
):
    ordered = sorted(values)

    if not ordered:
        return None

    index = round(
        (
            len(ordered)
            - 1
        )
        * fraction
    )

    return ordered[index]


def main():
    listings = load_listings()

    print(
        "=== Q6 Average PPSF "
        "for Live 2BHK Listings ==="
    )

    print()
    print(
        f"Listings loaded: "
        f"{len(listings)}"
    )

    # ---------------------------------
    # Step-by-step filtering
    # ---------------------------------

    two_bhk = [
        listing
        for listing in listings
        if listing.get(
            "bedroom"
        ) == 2
    ]

    print()
    print(
        f"All 2BHK records: "
        f"{len(two_bhk)}"
    )

    live_two_bhk = [
        listing
        for listing in two_bhk
        if listing.get(
            "is_live"
        )
        is True
    ]

    print(
        f"Live 2BHK records: "
        f"{len(live_two_bhk)}"
    )

    corrupt_removed = [
        listing
        for listing
        in live_two_bhk
        if listing[
            "listing_id"
        ]
        in CORRUPT_IDS
    ]

    print(
        "Live 2BHK corrupt "
        f"records excluded: "
        f"{len(corrupt_removed)}"
    )

    fake_removed = [
        listing
        for listing
        in live_two_bhk
        if listing[
            "listing_id"
        ]
        in FAKE_IDS
    ]

    print(
        "Live 2BHK fake "
        f"records excluded: "
        f"{len(fake_removed)}"
    )

    eligible = [
        listing
        for listing
        in live_two_bhk
        if (
            listing[
                "listing_id"
            ]
            not in CORRUPT_IDS
            and listing[
                "listing_id"
            ]
            not in FAKE_IDS
        )
    ]

    print(
        f"Eligible after "
        f"Q4/Q9 exclusion: "
        f"{len(eligible)}"
    )

    # ---------------------------------
    # Validate price and area
    # ---------------------------------

    invalid_price = []
    invalid_area = []

    ppsf_records = []

    converted_magic = []

    for listing in eligible:
        price = listing.get(
            "price"
        )

        carpet = (
            normalized_carpet_sqft(
                listing
            )
        )

        if (
            not is_number(price)
            or price <= 0
        ):
            invalid_price.append(
                listing[
                    "listing_id"
                ]
            )

            continue

        if (
            carpet is None
            or carpet <= 0
        ):
            invalid_area.append(
                listing[
                    "listing_id"
                ]
            )

            continue

        if is_magic_sqm_record(
            listing
        ):
            converted_magic.append(
                listing[
                    "listing_id"
                ]
            )

        ppsf = (
            float(price)
            / carpet
        )

        ppsf_records.append(
            (
                ppsf,
                listing,
            )
        )

    print()
    print(
        "=== Data Validation ==="
    )

    print(
        f"Invalid/non-positive "
        f"prices: "
        f"{len(invalid_price)}"
    )

    print(
        f"Invalid/non-positive "
        f"carpet areas: "
        f"{len(invalid_area)}"
    )

    print(
        "Magichomes m² records "
        "converted to sqft: "
        f"{len(converted_magic)}"
    )

    print(
        "Final PPSF records: "
        f"{len(ppsf_records)}"
    )

    # ---------------------------------
    # Distribution
    # ---------------------------------

    values = [
        item[0]
        for item
        in ppsf_records
    ]

    print()
    print(
        "=== PPSF Distribution ==="
    )

    print(
        f"minimum: "
        f"{min(values):.2f}"
    )

    print(
        f"5th percentile: "
        f"{percentile(
            values,
            0.05,
        ):.2f}"
    )

    print(
        f"median: "
        f"{median(values):.2f}"
    )

    print(
        f"95th percentile: "
        f"{percentile(
            values,
            0.95,
        ):.2f}"
    )

    print(
        f"maximum: "
        f"{max(values):.2f}"
    )

    # ---------------------------------
    # Website breakdown
    # ---------------------------------

    website_counts = Counter(
        listing.get(
            "website"
        )
        for _, listing
        in ppsf_records
    )

    print()
    print(
        "=== Records By Website ==="
    )

    for website, count in sorted(
        website_counts.items()
    ):
        print(
            f"{website}: "
            f"{count}"
        )

    # ---------------------------------
    # Lowest/highest values
    # ---------------------------------

    ppsf_records.sort(
        key=lambda item:
            item[0]
    )

    print()
    print(
        "=== Lowest 10 PPSF ==="
    )

    for ppsf, listing in (
        ppsf_records[:10]
    ):
        print(
            {
                "listing_id":
                    listing[
                        "listing_id"
                    ],
                "website":
                    listing.get(
                        "website"
                    ),
                "price":
                    listing.get(
                        "price"
                    ),
                "carpet_sqft":
                    round(
                        normalized_carpet_sqft(
                            listing
                        ),
                        2,
                    ),
                "ppsf":
                    round(
                        ppsf,
                        2,
                    ),
            }
        )

    print()
    print(
        "=== Highest 10 PPSF ==="
    )

    for ppsf, listing in (
        ppsf_records[-10:]
    ):
        print(
            {
                "listing_id":
                    listing[
                        "listing_id"
                    ],
                "website":
                    listing.get(
                        "website"
                    ),
                "price":
                    listing.get(
                        "price"
                    ),
                "carpet_sqft":
                    round(
                        normalized_carpet_sqft(
                            listing
                        ),
                        2,
                    ),
                "ppsf":
                    round(
                        ppsf,
                        2,
                    ),
            }
        )

    # ---------------------------------
    # Q6
    # ---------------------------------

    average_ppsf = mean(
        values
    )

    print()
    print(
        "=== Q6 Candidate Answer ==="
    )

    print(
        "avg_price_per_sqft_2bhk: "
        f"{average_ppsf:.2f}"
    )

    print()
    print(
        "Important: this is the "
        "arithmetic mean of each "
        "listing's price/carpet_area."
    )

    print(
        "It is NOT "
        "sum(price)/sum(area)."
    )

    print()
    print(
        "Do not finalize Q6 until "
        "the diagnostics are reviewed."
    )


if __name__ == "__main__":
    main()