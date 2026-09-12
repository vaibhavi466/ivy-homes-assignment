import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path


LISTINGS_PATH = Path("data/raw/listings.json")

SQFT_PER_SQM = 10.7639104167


def load_listings():
    with LISTINGS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["results"]


def normalize_text(value):
    if value is None:
        return None

    return " ".join(
        str(value)
        .strip()
        .lower()
        .split()
    )


def is_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
    )


def is_magic_sqm_record(listing):
    carpet = listing.get("carpet_area")
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


def normalized_area(
    listing,
    field,
):
    value = listing.get(field)

    if not is_number(value):
        return None

    if is_magic_sqm_record(listing):
        return (
            float(value)
            * SQFT_PER_SQM
        )

    return float(value)


def relative_difference(a, b):
    if (
        a is None
        or b is None
        or a <= 0
        or b <= 0
    ):
        return None

    return (
        abs(a - b)
        / max(a, b)
    )


def building_key(listing):
    return (
        normalize_text(
            listing.get("locality")
        ),
        normalize_text(
            listing.get("apartment_name")
        ),
    )


def pair_details(a, b):
    carpet_a = normalized_area(
        a,
        "carpet_area",
    )

    carpet_b = normalized_area(
        b,
        "carpet_area",
    )

    super_a = normalized_area(
        a,
        "super_built_up_area",
    )

    super_b = normalized_area(
        b,
        "super_built_up_area",
    )

    carpet_diff = relative_difference(
        carpet_a,
        carpet_b,
    )

    super_diff = relative_difference(
        super_a,
        super_b,
    )

    floor_a = a.get("floor")
    floor_b = b.get("floor")

    if (
        is_number(floor_a)
        and is_number(floor_b)
    ):
        floor_diff = abs(
            floor_a - floor_b
        )
    else:
        floor_diff = None

    return {
        "a": a,
        "b": b,
        "same_website":
            a.get("website")
            == b.get("website"),
        "same_property_type":
            normalize_text(
                a.get("property_type")
            )
            == normalize_text(
                b.get("property_type")
            ),
        "same_bedroom":
            a.get("bedroom")
            == b.get("bedroom"),
        "same_bathroom":
            a.get("bathroom")
            == b.get("bathroom"),
        "same_balcony":
            a.get("balcony")
            == b.get("balcony"),
        "same_floor":
            a.get("floor")
            == b.get("floor"),
        "same_total_floors":
            a.get("total_floors")
            == b.get("total_floors"),
        "floor_diff":
            floor_diff,
        "carpet_a":
            carpet_a,
        "carpet_b":
            carpet_b,
        "carpet_diff":
            carpet_diff,
        "super_a":
            super_a,
        "super_b":
            super_b,
        "super_diff":
            super_diff,
    }


def main():
    listings = load_listings()

    buildings = defaultdict(list)

    for listing in listings:
        key = building_key(listing)

        if (
            key[0] is not None
            and key[1] is not None
        ):
            buildings[key].append(
                listing
            )

    multi_listing_buildings = {
        key: group
        for key, group
        in buildings.items()
        if len(group) > 1
    }

    print(
        "=== Q2 Normalized Near-Duplicate Search ==="
    )

    print()
    print(
        f"Listings loaded: {len(listings)}"
    )

    print(
        "Buildings with >1 listing: "
        f"{len(multi_listing_buildings)}"
    )

    pairs = []

    for group in (
        multi_listing_buildings.values()
    ):
        for a, b in combinations(
            group,
            2,
        ):
            pairs.append(
                pair_details(
                    a,
                    b,
                )
            )

    print(
        f"Within-building pairs: "
        f"{len(pairs)}"
    )

    cross_site_pairs = [
        pair
        for pair in pairs
        if not pair["same_website"]
    ]

    print(
        f"Cross-site pairs: "
        f"{len(cross_site_pairs)}"
    )

    # ---------------------------------------------
    # Progressive matching conditions
    # ---------------------------------------------

    same_bed_bath = [
        pair
        for pair in pairs
        if (
            pair["same_bedroom"]
            and pair["same_bathroom"]
        )
    ]

    same_bed_bath_floor = [
        pair
        for pair in same_bed_bath
        if pair["same_floor"]
    ]

    print()
    print(
        "=== Basic Identity Signals ==="
    )

    print(
        "Same building + bedroom + bathroom: "
        f"{len(same_bed_bath)}"
    )

    print(
        "Same building + bedroom + bathroom "
        "+ floor: "
        f"{len(same_bed_bath_floor)}"
    )

    # Rule A: extremely conservative
    rule_a = [
        pair
        for pair in pairs
        if (
            pair["same_bedroom"]
            and pair["same_bathroom"]
            and pair["same_floor"]
            and pair["same_total_floors"]
            and pair["carpet_diff"]
            is not None
            and pair["super_diff"]
            is not None
            and pair["carpet_diff"]
            <= 0.05
            and pair["super_diff"]
            <= 0.05
        )
    ]

    # Rule B: tolerate one-floor disagreement,
    # but require balcony agreement and very
    # similar normalized areas.
    rule_b = [
        pair
        for pair in pairs
        if (
            pair["same_bedroom"]
            and pair["same_bathroom"]
            and pair["same_balcony"]
            and pair["same_total_floors"]
            and pair["floor_diff"]
            is not None
            and pair["floor_diff"]
            <= 1
            and pair["carpet_diff"]
            is not None
            and pair["super_diff"]
            is not None
            and pair["carpet_diff"]
            <= 0.05
            and pair["super_diff"]
            <= 0.05
        )
    ]

    # Rule C: inspection-only wider net.
    rule_c = [
        pair
        for pair in pairs
        if (
            pair["same_bedroom"]
            and pair["same_bathroom"]
            and pair["same_total_floors"]
            and pair["floor_diff"]
            is not None
            and pair["floor_diff"]
            <= 1
            and pair["carpet_diff"]
            is not None
            and pair["super_diff"]
            is not None
            and pair["carpet_diff"]
            <= 0.10
            and pair["super_diff"]
            <= 0.10
        )
    ]

    print()
    print(
        "=== Candidate Rule Counts ==="
    )

    print(
        f"Rule A: {len(rule_a)} pairs"
    )

    print(
        f"Rule B: {len(rule_b)} pairs"
    )

    print(
        f"Rule C: {len(rule_c)} pairs"
    )

    print(
        "Rule A cross-site: "
        f"{sum(
            not pair['same_website']
            for pair in rule_a
        )}"
    )

    print(
        "Rule B cross-site: "
        f"{sum(
            not pair['same_website']
            for pair in rule_b
        )}"
    )

    print(
        "Rule C cross-site: "
        f"{sum(
            not pair['same_website']
            for pair in rule_c
        )}"
    )

    # ---------------------------------------------
    # Rank strongest candidates for inspection
    # ---------------------------------------------

    inspectable = [
        pair
        for pair in pairs
        if (
            pair["same_bedroom"]
            and pair["same_total_floors"]
            and pair["carpet_diff"]
            is not None
            and pair["super_diff"]
            is not None
        )
    ]

    inspectable.sort(
        key=lambda pair: (
            0
            if pair["same_floor"]
            else 1,
            0
            if pair["same_bathroom"]
            else 1,
            pair["floor_diff"]
            if pair["floor_diff"]
            is not None
            else 999,
            max(
                pair["carpet_diff"],
                pair["super_diff"],
            ),
            0
            if pair["same_balcony"]
            else 1,
            0
            if not pair[
                "same_website"
            ]
            else 1,
        )
    )

    print()
    print(
        "=== Top 40 Strongest Candidate Pairs ==="
    )

    for index, pair in enumerate(
        inspectable[:40],
        start=1,
    ):
        a = pair["a"]
        b = pair["b"]

        print()
        print(
            f"--- Pair {index} ---"
        )

        print(
            {
                "listing_id":
                    a.get("listing_id"),
                "website":
                    a.get("website"),
                "locality":
                    a.get("locality"),
                "apartment_name":
                    a.get(
                        "apartment_name"
                    ),
                "property_type":
                    a.get(
                        "property_type"
                    ),
                "bedroom":
                    a.get("bedroom"),
                "bathroom":
                    a.get("bathroom"),
                "balcony":
                    a.get("balcony"),
                "floor":
                    a.get("floor"),
                "total_floors":
                    a.get(
                        "total_floors"
                    ),
                "carpet_sqft":
                    round(
                        pair["carpet_a"],
                        2,
                    ),
                "super_sqft":
                    round(
                        pair["super_a"],
                        2,
                    ),
                "price":
                    a.get("price"),
                "latitude":
                    a.get("latitude"),
                "longitude":
                    a.get("longitude"),
            }
        )

        print(
            {
                "listing_id":
                    b.get("listing_id"),
                "website":
                    b.get("website"),
                "locality":
                    b.get("locality"),
                "apartment_name":
                    b.get(
                        "apartment_name"
                    ),
                "property_type":
                    b.get(
                        "property_type"
                    ),
                "bedroom":
                    b.get("bedroom"),
                "bathroom":
                    b.get("bathroom"),
                "balcony":
                    b.get("balcony"),
                "floor":
                    b.get("floor"),
                "total_floors":
                    b.get(
                        "total_floors"
                    ),
                "carpet_sqft":
                    round(
                        pair["carpet_b"],
                        2,
                    ),
                "super_sqft":
                    round(
                        pair["super_b"],
                        2,
                    ),
                "price":
                    b.get("price"),
                "latitude":
                    b.get("latitude"),
                "longitude":
                    b.get("longitude"),
            }
        )

        print(
            "comparison:",
            {
                "same_bathroom":
                    pair[
                        "same_bathroom"
                    ],
                "same_balcony":
                    pair[
                        "same_balcony"
                    ],
                "same_floor":
                    pair[
                        "same_floor"
                    ],
                "floor_diff":
                    pair[
                        "floor_diff"
                    ],
                "carpet_diff_pct":
                    round(
                        pair[
                            "carpet_diff"
                        ]
                        * 100,
                        2,
                    ),
                "super_diff_pct":
                    round(
                        pair[
                            "super_diff"
                        ]
                        * 100,
                        2,
                    ),
            },
        )

    print()
    print(
        "Do not finalize Q2 yet."
    )


if __name__ == "__main__":
    main()