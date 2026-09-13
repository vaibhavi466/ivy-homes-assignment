import json
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import math
from collections import defaultdict
from itertools import combinations

load_dotenv()


# ---------------------------------------------------------------------
# Raw data snapshots
# ---------------------------------------------------------------------

LISTINGS_PATH = Path("data/raw/listings.json")
RENTALS_PATH = Path("data/raw/rentals.json")
PROJECTS_PATH = Path("data/raw/projects.json")


# ---------------------------------------------------------------------
# Assignment configuration
# ---------------------------------------------------------------------

ASSIGNED_LOCALITY = os.getenv("IVY_ASSIGNED_LOCALITY")


# ---------------------------------------------------------------------
# Observed project-price unit conversion
# ---------------------------------------------------------------------

LAKH_TO_INR = 100_000
CRORE_TO_INR = 10_000_000

# Full project analysis showed:
#
# values < 10  -> crore
# values >= 10 -> lakh
#
# Observed clusters:
# max below 10  = 5.83
# min above 10  = 41.5
PROJECT_UNIT_THRESHOLD = 10


IST = timezone(
    timedelta(
        hours=5,
        minutes=30,
    )
)

REFERENCE = datetime.fromisoformat(
    "2026-09-10T00:00:00+05:30"
)

Q8_WINDOW_START = (
    REFERENCE - timedelta(days=7)
)


SQFT_PER_SQM = 10.7639104167
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



def compute_q8():
    snapshot = load_snapshot(
        LISTINGS_PATH
    )

    metadata = snapshot["metadata"]
    listings = snapshot["results"]

    if (
        len(listings)
        != metadata["records_retrieved"]
    ):
        raise RuntimeError(
            "Listing snapshot metadata does not "
            "match stored records."
        )

    if metadata["final_has_more"] is not False:
        raise RuntimeError(
            "Listing snapshot did not reach "
            "the end of pagination."
        )

    qualifying = 0

    for listing in listings:
        listing_id = listing.get(
            "listing_id"
        )

        raw = listing.get(
            "posted_at"
        )

        if not isinstance(raw, str):
            raise RuntimeError(
                f"{listing_id}: invalid posted_at"
            )

        parsed = datetime.fromisoformat(
            raw
        )

        if parsed.tzinfo is not None:
            raise RuntimeError(
                f"{listing_id}: expected naive "
                "posted_at for observed dataset."
            )

        posted_at = parsed.replace(
            tzinfo=IST
        )

        if (
            Q8_WINDOW_START
            <= posted_at
            < REFERENCE
        ):
            qualifying += 1

    return qualifying

def compute_q9():
    snapshot = load_snapshot(
        LISTINGS_PATH
    )

    fake_ids = sorted(
        listing["listing_id"]
        for listing
        in snapshot["results"]
        if (
            is_number(
                listing.get("price")
            )
            and 0
            < listing["price"]
            < 100_000
        )
    )

    return fake_ids


def load_snapshot(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Snapshot not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def normalize_text(value):
    if value is None:
        return None

    return " ".join(
        str(value)
        .strip()
        .lower()
        .split()
    )


# ---------------------------------------------------------------------
# Q1
# total_listing_records
# ---------------------------------------------------------------------

def compute_q1():
    snapshot = load_snapshot(
        LISTINGS_PATH
    )

    metadata = snapshot["metadata"]
    listings = snapshot["results"]

    retrieved_count = len(listings)

    listing_ids = [
        listing.get("listing_id")
        for listing in listings
    ]

    if any(
        listing_id is None
        for listing_id in listing_ids
    ):
        raise RuntimeError(
            "At least one listing is missing listing_id."
        )

    unique_listing_ids = set(
        listing_ids
    )

    if (
        retrieved_count
        != metadata["records_retrieved"]
    ):
        raise RuntimeError(
            "Listing snapshot metadata does not "
            "match stored records."
        )

    if (
        len(unique_listing_ids)
        != retrieved_count
    ):
        raise RuntimeError(
            "Duplicate listing_id values exist "
            "in the listings snapshot."
        )

    if (
        metadata["final_has_more"]
        is not False
    ):
        raise RuntimeError(
            "Listings snapshot did not reach "
            "the end of pagination."
        )

    return retrieved_count


def compute_q2():
    snapshot = load_snapshot(
        LISTINGS_PATH
    )

    listings = snapshot["results"]

    buildings = defaultdict(list)

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
            buildings[key].append(
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

    for group in buildings.values():
        if len(group) < 2:
            continue

        for a, b in combinations(
            group,
            2,
        ):
            if (
                normalize_text(
                    a.get(
                        "property_type"
                    )
                )
                != normalize_text(
                    b.get(
                        "property_type"
                    )
                )
            ):
                continue

            if (
                a.get("bedroom")
                != b.get("bedroom")
            ):
                continue

            if (
                a.get("bathroom")
                != b.get("bathroom")
            ):
                continue

            if (
                a.get("balcony")
                != b.get("balcony")
            ):
                continue

            if (
                a.get("floor")
                != b.get("floor")
            ):
                continue

            if (
                a.get("total_floors")
                != b.get("total_floors")
            ):
                continue

            carpet_diff = (
                relative_difference(
                    normalized_area(
                        a,
                        "carpet_area",
                    ),
                    normalized_area(
                        b,
                        "carpet_area",
                    ),
                )
            )

            super_diff = (
                relative_difference(
                    normalized_area(
                        a,
                        "super_built_up_area",
                    ),
                    normalized_area(
                        b,
                        "super_built_up_area",
                    ),
                )
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
                continue

            if (
                carpet_diff <= 0.05
                and super_diff <= 0.05
                and distance <= 150
            ):
                union(
                    a["listing_id"],
                    b["listing_id"],
                )

    unique_roots = {
        find(
            listing["listing_id"]
        )
        for listing in listings
    }

    return len(
        unique_roots
    )

def compute_q3():
    snapshot = load_snapshot(
        LISTINGS_PATH
    )

    metadata = snapshot["metadata"]
    listings = snapshot["results"]

    if (
        len(listings)
        != metadata["records_retrieved"]
    ):
        raise RuntimeError(
            "Listing snapshot metadata does not "
            "match stored records."
        )

    if (
        metadata["final_has_more"]
        is not False
    ):
        raise RuntimeError(
            "Listing snapshot did not reach "
            "the end of pagination."
        )

    active_count = 0

    for listing in listings:
        if "is_live" not in listing:
            raise RuntimeError(
                "A listing is missing is_live."
            )

        value = listing["is_live"]

        if type(value) is not bool:
            raise RuntimeError(
                "A listing contains a non-boolean "
                "is_live value."
            )

        if value is True:
            active_count += 1

    return active_count

# ---------------------------------------------------------------------
# Q5
# total_monthly_rent
# ---------------------------------------------------------------------

def compute_q5():
    if not ASSIGNED_LOCALITY:
        raise RuntimeError(
            "IVY_ASSIGNED_LOCALITY is missing."
        )

    snapshot = load_snapshot(
        RENTALS_PATH
    )

    metadata = snapshot["metadata"]
    rentals = snapshot["results"]

    if (
        len(rentals)
        != metadata["records_retrieved"]
    ):
        raise RuntimeError(
            "Rental snapshot metadata does not "
            "match stored records."
        )

    if (
        metadata["final_has_more"]
        is not False
    ):
        raise RuntimeError(
            "Rental snapshot did not reach "
            "the end of pagination."
        )

    target_locality = normalize_text(
        ASSIGNED_LOCALITY
    )

    matching_rentals = [
        rental
        for rental in rentals
        if normalize_text(
            rental.get("locality")
        ) == target_locality
    ]

    if not matching_rentals:
        raise RuntimeError(
            "No rentals matched the assigned locality."
        )

    invalid_price_ids = []

    for rental in matching_rentals:
        price = rental.get("price")

        if (
            not isinstance(
                price,
                (int, float),
            )
            or price <= 0
        ):
            invalid_price_ids.append(
                rental.get("listing_id")
            )

    if invalid_price_ids:
        raise RuntimeError(
            "Invalid rental prices found for: "
            f"{invalid_price_ids}"
        )

    total_monthly_rent = sum(
        rental["price"]
        for rental in matching_rentals
    )

    return (
        total_monthly_rent,
        len(matching_rentals),
    )


def compute_q6():
    snapshot = load_snapshot(
        LISTINGS_PATH
    )

    listings = snapshot["results"]

    corrupt_ids = set(
        compute_q4()
    )

    fake_ids = set(
        compute_q9()
    )

    ppsf_values = []

    for listing in listings:
        if listing.get("is_live") is not True:
            continue

        if listing.get("bedroom") != 2:
            continue

        listing_id = listing[
            "listing_id"
        ]

        if listing_id in corrupt_ids:
            continue

        if listing_id in fake_ids:
            continue

        price = listing.get("price")

        carpet_sqft = normalized_area(
            listing,
            "carpet_area",
        )

        if (
            not is_number(price)
            or price <= 0
            or carpet_sqft is None
            or carpet_sqft <= 0
        ):
            continue

        ppsf_values.append(
            price / carpet_sqft
        )

    return round(
        sum(ppsf_values)
        / len(ppsf_values),
        2,
    )


# Project price normalization


def project_price_to_inr(value):
    if not isinstance(
        value,
        (int, float),
    ):
        raise RuntimeError(
            f"Invalid project price: {value}"
        )

    if value < PROJECT_UNIT_THRESHOLD:
        return round(
            value * CRORE_TO_INR
        )

    return round(
        value * LAKH_TO_INR
    )


# ---------------------------------------------------------------------
# Q7
# costliest_project
# ---------------------------------------------------------------------

def compute_q7():
    snapshot = load_snapshot(
        PROJECTS_PATH
    )

    metadata = snapshot["metadata"]
    projects = snapshot["results"]

    if (
        len(projects)
        != metadata["records_retrieved"]
    ):
        raise RuntimeError(
            "Project snapshot metadata does not "
            "match stored records."
        )

    if (
        metadata["final_has_more"]
        is not False
    ):
        raise RuntimeError(
            "Project snapshot did not reach "
            "the end of pagination."
        )

    normalized_projects = []

    for project in projects:
        project_id = project.get(
            "project_id"
        )

        if not project_id:
            raise RuntimeError(
                "A project is missing project_id."
            )

        price_min = project.get(
            "price_min"
        )

        price_max = project.get(
            "price_max"
        )

        price_min_inr = project_price_to_inr(
            price_min
        )

        price_max_inr = project_price_to_inr(
            price_max
        )

        # Our unit interpretation should restore
        # correct price-range ordering.
        if price_min_inr > price_max_inr:
            raise RuntimeError(
                "Normalized project range is "
                f"inverted for {project_id}: "
                f"{price_min_inr} > {price_max_inr}"
            )

        normalized_projects.append(
            {
                "project_id": project_id,
                "price_max_inr": price_max_inr,
            }
        )

    winner = max(
        normalized_projects,
        key=lambda project:
            project["price_max_inr"],
    )

    return winner


CORRUPT_LISTING_IDS = {
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

def compute_q4():
    snapshot = load_snapshot(
        LISTINGS_PATH
    )

    listings = snapshot["results"]

    listing_ids = {
        listing.get("listing_id")
        for listing in listings
    }

    missing = (
        CORRUPT_LISTING_IDS
        - listing_ids
    )

    if missing:
        raise RuntimeError(
            "Configured corrupt IDs are missing "
            f"from snapshot: {sorted(missing)}"
        )

    return sorted(
        CORRUPT_LISTING_IDS
    )

def main():
    q1 = compute_q1()

    q2 = compute_q2()

    q3 = compute_q3()

    q4 = compute_q4()

    q5, q5_record_count = compute_q5()

    q6 = compute_q6()

    q8 = compute_q8()

    q9 = compute_q9()

    q7 = compute_q7()

    print(
        "=== Reproducible Baseline Answers ==="
    )

    print()
    print("Q1")
    print(
        f"total_listing_records: {q1}"
    )

    print()
    print("Q4")
    print(
        f"corrupt_listing_ids: {q4}"
    )


    print()
    print("Q2")
    print(
        f"unique_properties: {q2}"
    )
    print()


    print()
    print("Q8")
    print(
        f"listings_last_7_days: {q8}"
    )

    print()
    print("Q9")
    print(
        "fake_listing_ids: "
        f"{q9}"
    )


    print()
    print("Q3")
    print(
        f"active_listings: {q3}"
    )
    print()


    print()
    print("Q5")
    print(
        f"total_monthly_rent: {q5}"
    )
    print(
        f"qualifying rental records: "
        f"{q5_record_count}"
    )

    print()
    print("Q6")
    print(
        f"avg_price_per_sqft_2bhk: {q6:.2f}"
    )

    print()
    print("Q7")
    print(
        "costliest_project: "
        f"{q7}"
    )


if __name__ == "__main__":
    main()