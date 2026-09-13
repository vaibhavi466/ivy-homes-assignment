import json
from collections import defaultdict
from pathlib import Path
from statistics import median


LISTINGS_PATH = Path("data/raw/listings.json")
PROJECTS_PATH = Path("data/raw/projects.json")

SQFT_PER_SQM = 10.7639104167


CANDIDATE_IDS = {
    "100-6000678",
    "MAG-6002472",
    "100-6000578",
    "SQU-6000395",
    "MAG-6002941",
    "100-6001599",
}


def load_results(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["results"]


def is_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
    )


def normalize_text(value):
    if value is None:
        return None

    return " ".join(
        str(value)
        .strip()
        .lower()
        .split()
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


def normalized_carpet(listing):
    value = listing.get("carpet_area")

    if not is_number(value):
        return None

    if is_magic_sqm_record(listing):
        return (
            float(value)
            * SQFT_PER_SQM
        )

    return float(value)


def normalize_project_price(value):
    if not is_number(value):
        return None

    # Confirmed project-price unit rule.
    if value < 10:
        return (
            value
            * 10_000_000
        )

    return (
        value
        * 100_000
    )


def main():
    listings = load_results(
        LISTINGS_PATH
    )

    projects = load_results(
        PROJECTS_PATH
    )

    by_listing_id = {
        listing["listing_id"]:
            listing
        for listing in listings
    }

    by_project_id = {
        project["project_id"]:
            project
        for project in projects
    }

    print(
        "=== Q9 Candidate Semantic Validation ==="
    )

    print()
    print(
        f"Candidate count: "
        f"{len(CANDIDATE_IDS)}"
    )

    # -----------------------------------------
    # Locality/BHK peer reference
    # -----------------------------------------

    peer_groups = defaultdict(list)

    for listing in listings:
        if (
            listing["listing_id"]
            in CANDIDATE_IDS
        ):
            continue

        price = listing.get("price")

        if (
            not is_number(price)
            or price <= 0
        ):
            continue

        key = (
            normalize_text(
                listing.get("locality")
            ),
            listing.get("bedroom"),
        )

        peer_groups[key].append(
            price
        )

    website_counts = defaultdict(int)

    for listing_id in CANDIDATE_IDS:
        listing = by_listing_id[
            listing_id
        ]

        website_counts[
            listing.get("website")
        ] += 1

    print()
    print(
        "=== Candidate Website Distribution ==="
    )

    for website, count in sorted(
        website_counts.items()
    ):
        print(
            f"{website}: {count}"
        )

    print()
    print(
        "=== Candidate Validation ==="
    )

    for listing_id in sorted(
        CANDIDATE_IDS
    ):
        listing = by_listing_id[
            listing_id
        ]

        carpet = normalized_carpet(
            listing
        )

        raw_price = listing["price"]

        implied_total = (
            raw_price * carpet
        )

        key = (
            normalize_text(
                listing.get("locality")
            ),
            listing.get("bedroom"),
        )

        peers = peer_groups.get(
            key,
            [],
        )

        project_id = listing.get(
            "project_id"
        )

        project = (
            by_project_id.get(
                project_id
            )
            if project_id
            else None
        )

        print()
        print("=" * 72)

        print(
            f"Listing ID: {listing_id}"
        )

        print(
            f"website: "
            f"{listing.get('website')}"
        )

        print(
            f"locality: "
            f"{listing.get('locality')}"
        )

        print(
            f"bedroom: "
            f"{listing.get('bedroom')}"
        )

        print(
            f"raw price field: "
            f"{raw_price}"
        )

        print(
            f"normalized carpet sqft: "
            f"{carpet:.2f}"
        )

        print(
            "implied total if raw price "
            f"is PPSF: "
            f"{implied_total:.2f}"
        )

        if peers:
            peer_median = median(
                peers
            )

            print(
                "locality/BHK peer median "
                f"total price: "
                f"{peer_median:.2f}"
            )

            print(
                "implied total / peer median: "
                f"{implied_total / peer_median:.3f}"
            )

        print(
            f"project_id: {project_id}"
        )

        if project:
            raw_min = project.get(
                "price_min"
            )

            raw_max = project.get(
                "price_max"
            )

            project_min = (
                normalize_project_price(
                    raw_min
                )
            )

            project_max = (
                normalize_project_price(
                    raw_max
                )
            )

            low = min(
                project_min,
                project_max,
            )

            high = max(
                project_min,
                project_max,
            )

            print(
                "normalized project range: "
                f"{low:.2f} -> "
                f"{high:.2f}"
            )

            print(
                "raw price inside project range: "
                f"{low <= raw_price <= high}"
            )

            print(
                "implied total inside project range: "
                f"{low <= implied_total <= high}"
            )
        else:
            print(
                "No matching project record."
            )

        print(
            f"is_live: "
            f"{listing.get('is_live')}"
        )

        print(
            f"is_verified: "
            f"{listing.get('is_verified')}"
        )

        print(
            f"posted_by: "
            f"{listing.get('posted_by')}"
        )

    print()
    print(
        "Do not finalize Q9 until "
        "these six records are reviewed."
    )


if __name__ == "__main__":
    main()