import json
import os
from pathlib import Path

from dotenv import load_dotenv


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


# ---------------------------------------------------------------------
# Project price normalization
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    q1 = compute_q1()

    q5, q5_record_count = compute_q5()

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
    print("Q5")
    print(
        f"total_monthly_rent: {q5}"
    )
    print(
        f"qualifying rental records: "
        f"{q5_record_count}"
    )

    print()
    print("Q7")
    print(
        "costliest_project: "
        f"{q7}"
    )


if __name__ == "__main__":
    main()