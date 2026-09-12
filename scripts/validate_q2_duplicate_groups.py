import json
import math
from collections import Counter, defaultdict
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


def pair_key(a, b):
    return tuple(
        sorted(
            [
                a["listing_id"],
                b["listing_id"],
            ]
        )
    )


def distance_meters(a, b):
    lat1 = a.get("latitude")
    lon1 = a.get("longitude")
    lat2 = b.get("latitude")
    lon2 = b.get("longitude")

    if not all(
        is_number(value)
        for value in [
            lat1,
            lon1,
            lat2,
            lon2,
        ]
    ):
        return None

    earth_radius = 6371000.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_phi = math.radians(
        lat2 - lat1
    )

    delta_lambda = math.radians(
        lon2 - lon1
    )

    hav = (
        math.sin(
            delta_phi / 2
        ) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(
            delta_lambda / 2
        ) ** 2
    )

    return (
        2
        * earth_radius
        * math.atan2(
            math.sqrt(hav),
            math.sqrt(1 - hav),
        )
    )


def pair_metrics(a, b):
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

    return {
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
            (
                abs(
                    a.get("floor")
                    - b.get("floor")
                )
                if (
                    is_number(
                        a.get("floor")
                    )
                    and is_number(
                        b.get("floor")
                    )
                )
                else None
            ),
        "carpet_diff":
            relative_difference(
                carpet_a,
                carpet_b,
            ),
        "super_diff":
            relative_difference(
                super_a,
                super_b,
            ),
        "distance_m":
            distance_meters(
                a,
                b,
            ),
        "same_website":
            a.get("website")
            == b.get("website"),
    }


def rule_a(metrics):
    return (
        metrics["same_property_type"]
        and metrics["same_bedroom"]
        and metrics["same_bathroom"]
        and metrics["same_balcony"]
        and metrics["same_floor"]
        and metrics["same_total_floors"]
        and metrics["carpet_diff"]
        is not None
        and metrics["super_diff"]
        is not None
        and metrics["distance_m"]
        is not None
        and metrics["carpet_diff"]
        <= 0.05
        and metrics["super_diff"]
        <= 0.05
        and metrics["distance_m"]
        <= 150
    )

def rule_b(metrics):
    return (
        metrics["same_bedroom"]
        and metrics["same_bathroom"]
        and metrics["same_balcony"]
        and metrics["same_total_floors"]
        and metrics["floor_diff"]
        is not None
        and metrics["floor_diff"]
        <= 1
        and metrics["carpet_diff"]
        is not None
        and metrics["super_diff"]
        is not None
        and metrics["carpet_diff"]
        <= 0.05
        and metrics["super_diff"]
        <= 0.05
    )


def rule_c(metrics):
    return (
        metrics["same_bedroom"]
        and metrics["same_bathroom"]
        and metrics["same_total_floors"]
        and metrics["floor_diff"]
        is not None
        and metrics["floor_diff"]
        <= 1
        and metrics["carpet_diff"]
        is not None
        and metrics["super_diff"]
        is not None
        and metrics["carpet_diff"]
        <= 0.10
        and metrics["super_diff"]
        <= 0.10
    )


def build_components(
    listing_ids,
    duplicate_pairs,
):
    parent = {
        listing_id: listing_id
        for listing_id in listing_ids
    }

    def find(x):
        while parent[x] != x:
            parent[x] = parent[
                parent[x]
            ]
            x = parent[x]

        return x

    def union(a, b):
        root_a = find(a)
        root_b = find(b)

        if root_a != root_b:
            parent[root_b] = root_a

    for a, b in duplicate_pairs:
        union(a, b)

    components = defaultdict(list)

    for listing_id in listing_ids:
        components[
            find(listing_id)
        ].append(listing_id)

    return list(
        components.values()
    )


def main():
    listings = load_listings()

    by_id = {
        listing["listing_id"]:
            listing
        for listing in listings
    }

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

    pair_records = []

    for group in buildings.values():
        if len(group) < 2:
            continue

        for a, b in combinations(
            group,
            2,
        ):
            metrics = pair_metrics(
                a,
                b,
            )

            pair_records.append(
                (
                    a,
                    b,
                    metrics,
                )
            )

    set_a = set()
    set_b = set()
    set_c = set()

    metrics_by_pair = {}

    for a, b, metrics in pair_records:
        key = pair_key(
            a,
            b,
        )

        metrics_by_pair[key] = metrics

        if rule_a(metrics):
            set_a.add(key)

        if rule_b(metrics):
            set_b.add(key)

        if rule_c(metrics):
            set_c.add(key)

    print(
        "=== Q2 Duplicate Rule Validation ==="
    )

    print()
    print(
        f"Rule A pairs: {len(set_a)}"
    )

    print(
        f"Rule B pairs: {len(set_b)}"
    )

    print(
        f"Rule C pairs: {len(set_c)}"
    )

    print()
    print(
        "=== Rule Set Comparison ==="
    )

    print(
        f"A ∩ B: "
        f"{len(set_a & set_b)}"
    )

    print(
        f"Only A: "
        f"{len(set_a - set_b)}"
    )

    print(
        f"Only B: "
        f"{len(set_b - set_a)}"
    )

    print(
        f"C not in A: "
        f"{len(set_c - set_a)}"
    )

    print()

    # -----------------------------------------
    # Validate Rule A with independent signals
    # -----------------------------------------

    property_type_mismatches = []
    balcony_mismatches = []
    far_pairs = []

    distances = []

    for key in sorted(set_a):
        metrics = metrics_by_pair[key]

        if not metrics[
            "same_property_type"
        ]:
            property_type_mismatches.append(
                key
            )

        if not metrics[
            "same_balcony"
        ]:
            balcony_mismatches.append(
                key
            )

        distance = metrics[
            "distance_m"
        ]

        if distance is not None:
            distances.append(
                distance
            )

            if distance > 150:
                far_pairs.append(
                    (
                        key,
                        distance,
                    )
                )

    print(
        "=== Independent Validation of Rule A ==="
    )

    print(
        "Property-type mismatches: "
        f"{len(property_type_mismatches)}"
    )

    print(
        "Balcony mismatches: "
        f"{len(balcony_mismatches)}"
    )

    print(
        "Pairs >150m apart: "
        f"{len(far_pairs)}"
    )

    if far_pairs:
        print()
        print(
            "=== Rule A Geographic Outliers ==="
        )

        for key, distance in far_pairs:
            a = by_id[key[0]]
            b = by_id[key[1]]

            print()
            print(
                f"Distance: {distance:.2f} m"
            )

            for listing in [a, b]:
                print(
                    {
                        "listing_id":
                            listing.get(
                                "listing_id"
                            ),
                        "website":
                            listing.get(
                                "website"
                            ),
                        "locality":
                            listing.get(
                                "locality"
                            ),
                        "apartment_name":
                            listing.get(
                                "apartment_name"
                            ),
                        "property_type":
                            listing.get(
                                "property_type"
                            ),
                        "bedroom":
                            listing.get(
                                "bedroom"
                            ),
                        "bathroom":
                            listing.get(
                                "bathroom"
                            ),
                        "balcony":
                            listing.get(
                                "balcony"
                            ),
                        "floor":
                            listing.get(
                                "floor"
                            ),
                        "total_floors":
                            listing.get(
                                "total_floors"
                            ),
                        "carpet_sqft":
                            round(
                                normalized_area(
                                    listing,
                                    "carpet_area",
                                ),
                                2,
                            ),
                        "super_sqft":
                            round(
                                normalized_area(
                                    listing,
                                    "super_built_up_area",
                                ),
                                2,
                            ),
                        "price":
                            listing.get(
                                "price"
                            ),
                        "latitude":
                            listing.get(
                                "latitude"
                            ),
                        "longitude":
                            listing.get(
                                "longitude"
                            ),
                        "project_id":
                            listing.get(
                                "project_id"
                            ),
                        "posted_by_contact":
                            listing.get(
                                "posted_by_contact"
                            ),
                    }
                )

        key_building = building_key(a)

        print()
        print(
            "Other listings in same "
            "normalized building:"
        )

        for listing in buildings[
            key_building
        ]:
            print(
                {
                    "listing_id":
                        listing.get(
                            "listing_id"
                        ),
                    "website":
                        listing.get(
                            "website"
                        ),
                    "bedroom":
                        listing.get(
                            "bedroom"
                        ),
                    "bathroom":
                        listing.get(
                            "bathroom"
                        ),
                    "floor":
                        listing.get(
                            "floor"
                        ),
                    "carpet_sqft":
                        round(
                            normalized_area(
                                listing,
                                "carpet_area",
                            ),
                            2,
                        ),
                    "latitude":
                        listing.get(
                            "latitude"
                        ),
                    "longitude":
                        listing.get(
                            "longitude"
                        ),
                }
            )

    if distances:
        distances_sorted = sorted(
            distances
        )

        print(
            "Minimum distance (m): "
            f"{distances_sorted[0]:.2f}"
        )

        print(
            "Median distance (m): "
            f"{distances_sorted[
                len(distances_sorted) // 2
            ]:.2f}"
        )

        print(
            "Maximum distance (m): "
            f"{distances_sorted[-1]:.2f}"
        )

    # -----------------------------------------
    # Connected components
    # -----------------------------------------

    all_ids = {
        listing["listing_id"]
        for listing in listings
    }

    components_a = build_components(
        all_ids,
        set_a,
    )

    duplicate_components_a = [
        component
        for component in components_a
        if len(component) > 1
    ]

    component_sizes = Counter(
        len(component)
        for component
        in duplicate_components_a
    )

    unique_properties_a = len(
        components_a
    )

    duplicate_records_removed = (
        len(listings)
        - unique_properties_a
    )

    print()
    print(
        "=== Rule A Property Components ==="
    )

    print(
        "Duplicate property groups: "
        f"{len(duplicate_components_a)}"
    )

    print(
        "Listings participating in "
        "duplicate groups: "
        f"{sum(
            len(component)
            for component
            in duplicate_components_a
        )}"
    )

    print(
        "Duplicate records collapsed: "
        f"{duplicate_records_removed}"
    )

    print(
        "Candidate unique_properties: "
        f"{unique_properties_a}"
    )

    print()
    print(
        "Component size distribution:"
    )

    for size, count in sorted(
        component_sizes.items()
    ):
        print(
            f"size {size}: "
            f"{count} groups"
        )

    # -----------------------------------------
    # Inspect groups with >2 listings
    # -----------------------------------------

    large_components = sorted(
        [
            component
            for component
            in duplicate_components_a
            if len(component) > 2
        ],
        key=lambda component: (
            -len(component),
            sorted(component)[0],
        ),
    )

    print()
    print(
        "=== Components With More Than 2 Listings ==="
    )

    print(
        f"Count: {len(large_components)}"
    )

    for index, component in enumerate(
        large_components[:20],
        start=1,
    ):
        print()
        print(
            f"--- Component {index} "
            f"({len(component)} listings) ---"
        )

        for listing_id in sorted(
            component
        ):
            listing = by_id[
                listing_id
            ]

            print(
                {
                    "listing_id":
                        listing_id,
                    "website":
                        listing.get(
                            "website"
                        ),
                    "locality":
                        listing.get(
                            "locality"
                        ),
                    "apartment_name":
                        listing.get(
                            "apartment_name"
                        ),
                    "property_type":
                        listing.get(
                            "property_type"
                        ),
                    "bedroom":
                        listing.get(
                            "bedroom"
                        ),
                    "bathroom":
                        listing.get(
                            "bathroom"
                        ),
                    "balcony":
                        listing.get(
                            "balcony"
                        ),
                    "floor":
                        listing.get(
                            "floor"
                        ),
                    "total_floors":
                        listing.get(
                            "total_floors"
                        ),
                    "carpet_sqft":
                        round(
                            normalized_area(
                                listing,
                                "carpet_area",
                            ),
                            2,
                        ),
                    "super_sqft":
                        round(
                            normalized_area(
                                listing,
                                "super_built_up_area",
                            ),
                            2,
                        ),
                    "price":
                        listing.get(
                            "price"
                        ),
                }
            )

    # -----------------------------------------
    # Inspect all pairs admitted by C but not A
    # -----------------------------------------

    print()
    print(
        "=== Rule C Pairs Not In Rule A ==="
    )

    extra_c = sorted(
        set_c - set_a
    )

    print(
        f"Count: {len(extra_c)}"
    )

    for index, key in enumerate(
        extra_c,
        start=1,
    ):
        a = by_id[key[0]]
        b = by_id[key[1]]

        metrics = metrics_by_pair[
            key
        ]

        print()
        print(
            f"--- Extra Pair {index} ---"
        )

        for listing in [
            a,
            b,
        ]:
            print(
                {
                    "listing_id":
                        listing.get(
                            "listing_id"
                        ),
                    "website":
                        listing.get(
                            "website"
                        ),
                    "locality":
                        listing.get(
                            "locality"
                        ),
                    "apartment_name":
                        listing.get(
                            "apartment_name"
                        ),
                    "property_type":
                        listing.get(
                            "property_type"
                        ),
                    "bedroom":
                        listing.get(
                            "bedroom"
                        ),
                    "bathroom":
                        listing.get(
                            "bathroom"
                        ),
                    "balcony":
                        listing.get(
                            "balcony"
                        ),
                    "floor":
                        listing.get(
                            "floor"
                        ),
                    "total_floors":
                        listing.get(
                            "total_floors"
                        ),
                    "carpet_sqft":
                        round(
                            normalized_area(
                                listing,
                                "carpet_area",
                            ),
                            2,
                        ),
                    "super_sqft":
                        round(
                            normalized_area(
                                listing,
                                "super_built_up_area",
                            ),
                            2,
                        ),
                    "price":
                        listing.get(
                            "price"
                        ),
                }
            )

        print(
            "comparison:",
            {
                "floor_diff":
                    metrics[
                        "floor_diff"
                    ],
                "same_balcony":
                    metrics[
                        "same_balcony"
                    ],
                "same_property_type":
                    metrics[
                        "same_property_type"
                    ],
                "carpet_diff_pct":
                    round(
                        metrics[
                            "carpet_diff"
                        ]
                        * 100,
                        2,
                    ),
                "super_diff_pct":
                    round(
                        metrics[
                            "super_diff"
                        ]
                        * 100,
                        2,
                    ),
                "distance_m":
                    round(
                        metrics[
                            "distance_m"
                        ],
                        2,
                    )
                    if metrics[
                        "distance_m"
                    ]
                    is not None
                    else None,
            }
        )

    print()
    print(
        "Do not finalize Q2 until "
        "the component and boundary "
        "checks are reviewed."
    )


if __name__ == "__main__":
    main()
