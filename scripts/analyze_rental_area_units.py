import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median


RENTALS_PATH = Path(
    "data/raw/rentals.json"
)


def load_rentals():
    with RENTALS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["results"]


def percentile(values, fraction):
    ordered = sorted(values)

    if not ordered:
        return None

    index = round(
        (len(ordered) - 1)
        * fraction
    )

    return ordered[index]


def summarize(values):
    if not values:
        return None

    return {
        "min":
            min(values),
        "p05":
            percentile(
                values,
                0.05,
            ),
        "median":
            median(values),
        "p95":
            percentile(
                values,
                0.95,
            ),
        "max":
            max(values),
    }


def main():
    rentals = load_rentals()

    print(
        "=== Rental Area Unit Investigation ==="
    )

    print(
        f"Rentals loaded: "
        f"{len(rentals)}"
    )

    # ---------------------------------
    # Basic validation
    # ---------------------------------

    missing_carpet = []
    missing_super = []

    nonpositive_carpet = []
    nonpositive_super = []

    carpet_gt_super = []

    noninteger_carpet = []
    noninteger_super = []

    for rental in rentals:
        listing_id = rental[
            "listing_id"
        ]

        carpet = rental.get(
            "carpet_area"
        )

        super_area = rental.get(
            "super_builtup_area"
        )

        if not isinstance(
            carpet,
            (int, float),
        ):
            missing_carpet.append(
                listing_id
            )
        else:
            if carpet <= 0:
                nonpositive_carpet.append(
                    listing_id
                )

            if not isinstance(
                carpet,
                int,
            ):
                noninteger_carpet.append(
                    listing_id
                )

        if not isinstance(
            super_area,
            (int, float),
        ):
            missing_super.append(
                listing_id
            )
        else:
            if super_area <= 0:
                nonpositive_super.append(
                    listing_id
                )

            if not isinstance(
                super_area,
                int,
            ):
                noninteger_super.append(
                    listing_id
                )

        if (
            isinstance(
                carpet,
                (int, float),
            )
            and isinstance(
                super_area,
                (int, float),
            )
            and carpet > super_area
        ):
            carpet_gt_super.append(
                listing_id
            )

    print()
    print(
        "=== Basic Validation ==="
    )

    print(
        "Missing/non-numeric carpet:",
        len(missing_carpet),
    )

    print(
        "Missing/non-numeric super:",
        len(missing_super),
    )

    print(
        "Non-positive carpet:",
        len(nonpositive_carpet),
    )

    print(
        "Non-positive super:",
        len(nonpositive_super),
    )

    print(
        "carpet > super:",
        len(carpet_gt_super),
    )

    print(
        "Non-integer carpet values:",
        len(noninteger_carpet),
    )

    print(
        "Non-integer super values:",
        len(noninteger_super),
    )

    # ---------------------------------
    # Website distributions
    # ---------------------------------

    by_website = defaultdict(
        list
    )

    for rental in rentals:
        by_website[
            rental.get("website")
        ].append(rental)

    print()
    print(
        "=== Website Area Distributions ==="
    )

    for website in sorted(
        by_website
    ):
        records = by_website[
            website
        ]

        carpets = [
            record[
                "carpet_area"
            ]
            for record in records
            if isinstance(
                record.get(
                    "carpet_area"
                ),
                (int, float),
            )
        ]

        supers = [
            record[
                "super_builtup_area"
            ]
            for record in records
            if isinstance(
                record.get(
                    "super_builtup_area"
                ),
                (int, float),
            )
        ]

        low_both = [
            record
            for record in records
            if (
                isinstance(
                    record.get(
                        "carpet_area"
                    ),
                    (int, float),
                )
                and isinstance(
                    record.get(
                        "super_builtup_area"
                    ),
                    (int, float),
                )
                and record[
                    "carpet_area"
                ] < 300
                and record[
                    "super_builtup_area"
                ] < 400
            )
        ]

        print()
        print(
            f"Website: {website}"
        )

        print(
            f"records: {len(records)}"
        )

        print(
            "carpet:",
            summarize(carpets),
        )

        print(
            "super:",
            summarize(supers),
        )

        print(
            "both carpet<300 "
            "and super<400:",
            len(low_both),
        )

    # ---------------------------------
    # Threshold counts
    # ---------------------------------

    print()
    print(
        "=== Low-Area Thresholds ==="
    )

    thresholds = [
        (250, 350),
        (300, 400),
        (350, 450),
        (400, 500),
    ]

    for (
        carpet_limit,
        super_limit,
    ) in thresholds:
        matches = [
            rental
            for rental in rentals
            if (
                isinstance(
                    rental.get(
                        "carpet_area"
                    ),
                    (int, float),
                )
                and isinstance(
                    rental.get(
                        "super_builtup_area"
                    ),
                    (int, float),
                )
                and rental[
                    "carpet_area"
                ] < carpet_limit
                and rental[
                    "super_builtup_area"
                ] < super_limit
            )
        ]

        websites = Counter(
            rental.get(
                "website"
            )
            for rental in matches
        )

        print()
        print(
            f"carpet<{carpet_limit}, "
            f"super<{super_limit}"
        )

        print(
            "count:",
            len(matches),
        )

        print(
            "by website:",
            dict(websites),
        )

    # ---------------------------------
    # Candidate low-area records
    # ---------------------------------

    low_candidates = [
        rental
        for rental in rentals
        if (
            isinstance(
                rental.get(
                    "carpet_area"
                ),
                (int, float),
            )
            and isinstance(
                rental.get(
                    "super_builtup_area"
                ),
                (int, float),
            )
            and rental[
                "carpet_area"
            ] < 300
            and rental[
                "super_builtup_area"
            ] < 400
        )
    ]

    print()
    print(
        "=== Candidate Low-Area Records ==="
    )

    print(
        "count:",
        len(low_candidates),
    )

    for rental in (
        low_candidates[:50]
    ):
        print(
            {
                "listing_id":
                    rental[
                        "listing_id"
                    ],
                "website":
                    rental.get(
                        "website"
                    ),
                "bedroom":
                    rental.get(
                        "bedroom"
                    ),
                "property_type":
                    rental.get(
                        "property_type"
                    ),
                "carpet_area":
                    rental.get(
                        "carpet_area"
                    ),
                "super_builtup_area":
                    rental.get(
                        "super_builtup_area"
                    ),
                "price":
                    rental.get(
                        "price"
                    ),
            }
        )

    # ---------------------------------
    # BHK medians by website
    # ---------------------------------

    print()
    print(
        "=== Median Carpet Area By "
        "Website And BHK ==="
    )

    for bhk in sorted(
        {
            rental.get(
                "bedroom"
            )
            for rental in rentals
            if isinstance(
                rental.get(
                    "bedroom"
                ),
                int,
            )
        }
    ):
        print()
        print(
            f"BHK: {bhk}"
        )

        for website in sorted(
            by_website
        ):
            values = [
                rental[
                    "carpet_area"
                ]
                for rental
                in by_website[
                    website
                ]
                if (
                    rental.get(
                        "bedroom"
                    )
                    == bhk
                    and isinstance(
                        rental.get(
                            "carpet_area"
                        ),
                        (int, float),
                    )
                )
            ]

            if values:
                print(
                    f"{website}: "
                    f"n={len(values)}, "
                    f"median="
                    f"{median(values):.2f}"
                )

    print()
    print(
        "Do not infer a unit conversion "
        "unless a distinct source-specific "
        "cluster is visible."
    )


if __name__ == "__main__":
    main()