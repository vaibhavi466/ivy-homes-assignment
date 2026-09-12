import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path


LISTINGS_PATH = Path("data/raw/listings.json")


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


def coord_key(listing):
    lat = listing.get("latitude")
    lon = listing.get("longitude")

    if not isinstance(lat, (int, float)):
        return None

    if not isinstance(lon, (int, float)):
        return None

    return (
        round(lat, 5),
        round(lon, 5),
    )


def equal(a, b, field):
    return (
        a.get(field)
        == b.get(field)
    )


def normalized_equal(a, b, field):
    return (
        normalize_text(a.get(field))
        == normalize_text(b.get(field))
    )


def main():
    listings = load_listings()

    groups = defaultdict(list)

    for listing in listings:
        key = coord_key(listing)

        if key is not None:
            groups[key].append(listing)

    repeated_groups = [
        group
        for group in groups.values()
        if len(group) > 1
    ]

    print(
        "=== Q2 Repeated Coordinate Inspection ==="
    )

    print()
    print(
        f"Repeated coordinate groups: "
        f"{len(repeated_groups)}"
    )

    print(
        "Records inside repeated-coordinate groups: "
        f"{sum(len(group) for group in repeated_groups)}"
    )

    size_distribution = Counter(
        len(group)
        for group in repeated_groups
    )

    print()
    print("=== Group Size Distribution ===")

    for size, count in sorted(
        size_distribution.items()
    ):
        print(
            f"size {size}: {count} groups"
        )

    cross_website = []
    same_website_only = []

    for group in repeated_groups:
        websites = {
            listing.get("website")
            for listing in group
        }

        if len(websites) > 1:
            cross_website.append(group)
        else:
            same_website_only.append(group)

    print()
    print("=== Website Composition ===")

    print(
        f"Cross-website groups: "
        f"{len(cross_website)}"
    )

    print(
        f"Same-website-only groups: "
        f"{len(same_website_only)}"
    )

    # -------------------------------------------------
    # Pairwise equality profiling
    # -------------------------------------------------

    fields = [
        "property_type",
        "locality",
        "apartment_name",
        "project_id",
        "bedroom",
        "bathroom",
        "balcony",
        "floor",
        "total_floors",
        "carpet_area",
        "super_built_up_area",
        "price",
        "posted_by_contact",
    ]

    equality_counts = Counter()
    pair_count = 0
    cross_site_pair_count = 0

    for group in repeated_groups:
        for a, b in combinations(
            group,
            2,
        ):
            pair_count += 1

            if (
                a.get("website")
                != b.get("website")
            ):
                cross_site_pair_count += 1

            for field in fields:
                if field in {
                    "property_type",
                    "locality",
                    "apartment_name",
                }:
                    matches = normalized_equal(
                        a,
                        b,
                        field,
                    )
                else:
                    matches = equal(
                        a,
                        b,
                        field,
                    )

                if matches:
                    equality_counts[field] += 1

    print()
    print("=== Pairwise Equality Within Same Coordinates ===")

    print(
        f"Total record pairs: {pair_count}"
    )

    print(
        f"Cross-site pairs: "
        f"{cross_site_pair_count}"
    )

    for field in fields:
        count = equality_counts[field]

        percentage = (
            count * 100.0 / pair_count
            if pair_count
            else 0
        )

        print(
            f"{field}: "
            f"{count}/{pair_count} "
            f"({percentage:.2f}%)"
        )

    # -------------------------------------------------
    # Strong same-coordinate candidate rule
    #
    # Do not call these duplicates yet.
    # We only measure candidate groups.
    # -------------------------------------------------

    strong_candidate_groups = []

    for group in repeated_groups:
        candidate = False

        for a, b in combinations(
            group,
            2,
        ):
            if (
                normalize_text(
                    a.get("locality")
                )
                == normalize_text(
                    b.get("locality")
                )
                and normalize_text(
                    a.get("property_type")
                )
                == normalize_text(
                    b.get("property_type")
                )
                and a.get("bedroom")
                == b.get("bedroom")
                and a.get("bathroom")
                == b.get("bathroom")
            ):
                candidate = True
                break

        if candidate:
            strong_candidate_groups.append(
                group
            )

    print()
    print("=== Strong Same-Coordinate Candidate Groups ===")

    print(
        f"Groups: "
        f"{len(strong_candidate_groups)}"
    )

    print(
        f"Records: "
        f"{sum(
            len(group)
            for group in strong_candidate_groups
        )}"
    )

    # -------------------------------------------------
    # Inspect first 20 cross-website repeated coords
    # -------------------------------------------------

    print()
    print(
        "=== First 20 Cross-Website Coordinate Groups ==="
    )

    sorted_groups = sorted(
        cross_website,
        key=lambda group: (
            -len(group),
            group[0].get(
                "listing_id",
                "",
            ),
        ),
    )

    for index, group in enumerate(
        sorted_groups[:20],
        start=1,
    ):
        print()
        print(
            f"--- Group {index} "
            f"({len(group)} records) ---"
        )

        first = group[0]

        print(
            "coordinates:",
            round(
                first.get("latitude"),
                5,
            ),
            round(
                first.get("longitude"),
                5,
            ),
        )

        for listing in sorted(
            group,
            key=lambda item:
                item.get(
                    "listing_id",
                    "",
                ),
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
                    "project_id":
                        listing.get(
                            "project_id"
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
                    "carpet_area":
                        listing.get(
                            "carpet_area"
                        ),
                    "super_built_up_area":
                        listing.get(
                            "super_built_up_area"
                        ),
                    "price":
                        listing.get(
                            "price"
                        ),
                    "posted_by_contact":
                        listing.get(
                            "posted_by_contact"
                        ),
                }
            )

    print()
    print(
        "Do not finalize Q2 yet."
    )


if __name__ == "__main__":
    main()