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


def is_same_property(a, b):
    if (
        normalize_text(
            a.get("locality")
        )
        != normalize_text(
            b.get("locality")
        )
    ):
        return False

    if (
        normalize_text(
            a.get("apartment_name")
        )
        != normalize_text(
            b.get("apartment_name")
        )
    ):
        return False

    if (
        normalize_text(
            a.get("property_type")
        )
        != normalize_text(
            b.get("property_type")
        )
    ):
        return False

    exact_fields = [
        "bedroom",
        "bathroom",
        "balcony",
        "floor",
        "total_floors",
    ]

    for field in exact_fields:
        if (
            a.get(field)
            != b.get(field)
        ):
            return False

    carpet_diff = relative_difference(
        normalized_area(
            a,
            "carpet_area",
        ),
        normalized_area(
            b,
            "carpet_area",
        ),
    )

    super_diff = relative_difference(
        normalized_area(
            a,
            "super_built_up_area",
        ),
        normalized_area(
            b,
            "super_built_up_area",
        ),
    )

    distance = distance_meters(
        a,
        b,
    )

    if (
        carpet_diff is None
        or super_diff is None
        or distance is None
    ):
        return False

    return (
        carpet_diff <= 0.05
        and super_diff <= 0.05
        and distance <= 150
    )


def build_property_components(listings):
    by_building = defaultdict(list)

    for listing in listings:
        key = (
            normalize_text(
                listing.get("locality")
            ),
            normalize_text(
                listing.get(
                    "apartment_name"
                )
            ),
        )

        if (
            key[0] is not None
            and key[1] is not None
        ):
            by_building[key].append(
                listing
            )

    parent = {
        listing["listing_id"]:
            listing["listing_id"]
        for listing in listings
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

    for group in by_building.values():
        for a, b in combinations(
            group,
            2,
        ):
            if is_same_property(
                a,
                b,
            ):
                union(
                    a["listing_id"],
                    b["listing_id"],
                )

    components = defaultdict(list)

    for listing in listings:
        components[
            find(
                listing["listing_id"]
            )
        ].append(listing)

    return [
        group
        for group in components.values()
        if len(group) > 1
    ]


def main():
    listings = load_listings()

    print(
        "=== Q9 Fake Listing Investigation ==="
    )

    print()
    print(
        f"Listings loaded: {len(listings)}"
    )

    print()
    print(
        "=== Available Listing Fields ==="
    )

    all_fields = sorted(
        {
            key
            for listing in listings
            for key in listing.keys()
        }
    )

    print(all_fields)

    # -----------------------------------------
    # Contact reuse
    # -----------------------------------------

    contact_counts = Counter(
        listing.get(
            "posted_by_contact"
        )
        for listing in listings
        if listing.get(
            "posted_by_contact"
        )
    )

    print()
    print(
        "=== Contact Reuse ==="
    )

    print(
        "Unique contacts: "
        f"{len(contact_counts)}"
    )

    print(
        "Contacts used on >1 listing: "
        f"{sum(
            count > 1
            for count in contact_counts.values()
        )}"
    )

    print()
    print(
        "Top 20 contacts by listing count:"
    )

    for contact, count in (
        contact_counts.most_common(20)
    ):
        print(
            f"{contact}: {count}"
        )

    # -----------------------------------------
    # Duplicate physical properties
    # -----------------------------------------

    components = (
        build_property_components(
            listings
        )
    )

    print()
    print(
        "=== Duplicate Physical Property Groups ==="
    )

    print(
        f"Groups: {len(components)}"
    )

    print(
        "Listings inside groups: "
        f"{sum(
            len(group)
            for group in components
        )}"
    )

    # -----------------------------------------
    # Price disagreement within same property
    # -----------------------------------------

    price_groups = []

    for group in components:
        valid = [
            listing
            for listing in group
            if (
                is_number(
                    listing.get("price")
                )
                and listing["price"] > 0
            )
        ]

        if len(valid) < 2:
            continue

        prices = [
            listing["price"]
            for listing in valid
        ]

        minimum = min(prices)
        maximum = max(prices)

        ratio = (
            minimum / maximum
        )

        price_groups.append(
            (
                ratio,
                valid,
            )
        )

    price_groups.sort(
        key=lambda item:
            item[0]
    )

    print()
    print(
        "=== Largest Same-Property Price Disagreements ==="
    )

    for index, (
        ratio,
        group,
    ) in enumerate(
        price_groups[:40],
        start=1,
    ):
        prices = [
            listing["price"]
            for listing in group
        ]

        print()
        print(
            f"--- Group {index} ---"
        )

        print(
            "min/max price ratio: "
            f"{ratio:.4f}"
        )

        print(
            "price spread: "
            f"{min(prices)} -> "
            f"{max(prices)}"
        )

        for listing in sorted(
            group,
            key=lambda item:
                item["price"],
        ):
            carpet = normalized_area(
                listing,
                "carpet_area",
            )

            ppsf = (
                listing["price"]
                / carpet
                if (
                    carpet is not None
                    and carpet > 0
                )
                else None
            )

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
                    "floor":
                        listing.get(
                            "floor"
                        ),
                    "price":
                        listing.get(
                            "price"
                        ),
                    "price_per_sqft":
                        (
                            round(
                                ppsf,
                                2,
                            )
                            if ppsf
                            is not None
                            else None
                        ),
                    "contact":
                        listing.get(
                            "posted_by_contact"
                        ),
                    "is_live":
                        listing.get(
                            "is_live"
                        ),
                }
            )

    # -----------------------------------------
    # Global low-price-per-sqft outliers
    # -----------------------------------------

    ppsf_records = []

    for listing in listings:
        price = listing.get("price")

        carpet = normalized_area(
            listing,
            "carpet_area",
        )

        if (
            not is_number(price)
            or price <= 0
            or carpet is None
            or carpet <= 0
        ):
            continue

        ppsf_records.append(
            (
                price / carpet,
                listing,
            )
        )

    ppsf_records.sort(
        key=lambda item:
            item[0]
    )

    print()
    print(
        "=== Lowest 40 Normalized Price-per-sqft Listings ==="
    )

    for ppsf, listing in (
        ppsf_records[:40]
    ):
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
                "bedroom":
                    listing.get(
                        "bedroom"
                    ),
                "price":
                    listing.get(
                        "price"
                    ),
                "carpet_sqft":
                    round(
                        normalized_area(
                            listing,
                            "carpet_area",
                        ),
                        2,
                    ),
                "ppsf":
                    round(
                        ppsf,
                        2,
                    ),
                "contact":
                    listing.get(
                        "posted_by_contact"
                    ),
                "is_live":
                    listing.get(
                        "is_live"
                    ),
            }
        )

    print()
    print(
        "Do not finalize Q9 yet."
    )


if __name__ == "__main__":
    main()