import json
import os
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

ASSIGNED_LOCALITY = os.getenv("IVY_ASSIGNED_LOCALITY")

RENTALS_PATH = Path("data/raw/rentals.json")


def load_rentals():
    with RENTALS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        snapshot = json.load(file)

    return snapshot["results"]


def normalize_text(value):
    if value is None:
        return None

    return " ".join(
        str(value)
        .strip()
        .lower()
        .split()
    )


def main():
    if not ASSIGNED_LOCALITY:
        raise RuntimeError(
            "IVY_ASSIGNED_LOCALITY is missing from .env"
        )

    rentals = load_rentals()

    print("=== Q5 Rental Analysis ===")
    print(
        f"Assigned locality from email: "
        f"{ASSIGNED_LOCALITY}"
    )

    normalized_assigned = normalize_text(
        ASSIGNED_LOCALITY
    )

    locality_counts = Counter(
        normalize_text(
            rental.get("locality")
        )
        for rental in rentals
        if rental.get("locality") is not None
    )

    print()
    print("Normalized assigned locality:")
    print(normalized_assigned)

    print()
    print("Matching locality count:")
    print(
        locality_counts.get(
            normalized_assigned,
            0
        )
    )

    print()
    print("Nearby / similar locality values:")

    similar = [
        (locality, count)
        for locality, count
        in locality_counts.items()
        if (
            normalized_assigned in locality
            or locality in normalized_assigned
        )
    ]

    for locality, count in sorted(
        similar
    ):
        print(
            f"{locality}: {count}"
        )

    matching_rentals = [
        rental
        for rental in rentals
        if normalize_text(
            rental.get("locality")
        ) == normalized_assigned
    ]

    print()
    print(
        f"Exact normalized matches: "
        f"{len(matching_rentals)}"
    )

    if not matching_rentals:
        print(
            "No exact normalized matches found."
        )
        return

    prices = [
        rental.get("price")
        for rental in matching_rentals
    ]

    missing_prices = [
        rental.get("listing_id")
        for rental in matching_rentals
        if rental.get("price") is None
    ]

    non_numeric_prices = [
        rental.get("listing_id")
        for rental in matching_rentals
        if (
            rental.get("price") is not None
            and not isinstance(
                rental.get("price"),
                (int, float)
            )
        )
    ]

    non_positive_prices = [
        rental.get("listing_id")
        for rental in matching_rentals
        if (
            isinstance(
                rental.get("price"),
                (int, float)
            )
            and rental.get("price") <= 0
        )
    ]

    numeric_prices = [
        price
        for price in prices
        if isinstance(
            price,
            (int, float)
        )
    ]

    print()
    print("=== Price Validation ===")
    print(
        f"Matching rental records: "
        f"{len(matching_rentals)}"
    )
    print(
        f"Numeric price values: "
        f"{len(numeric_prices)}"
    )
    print(
        f"Missing prices: "
        f"{len(missing_prices)}"
    )
    print(
        f"Non-numeric prices: "
        f"{len(non_numeric_prices)}"
    )
    print(
        f"Non-positive prices: "
        f"{len(non_positive_prices)}"
    )

    if (
        missing_prices
        or non_numeric_prices
        or non_positive_prices
    ):
        print()
        print(
            "Q5 NOT computed because price "
            "validation failed."
        )
        return

    minimum_price = min(numeric_prices)
    maximum_price = max(numeric_prices)

    average_price = (
        sum(numeric_prices)
        / len(numeric_prices)
    )

    total_monthly_rent = sum(
        numeric_prices
    )

    print()
    print("=== Price Distribution ===")
    print(
        f"Minimum price: {minimum_price}"
    )
    print(
        f"Maximum price: {maximum_price}"
    )
    print(
        f"Average price: "
        f"{average_price:.2f}"
    )

    print()
    print("=== Q5 Candidate Answer ===")
    print(
        "total_monthly_rent: "
        f"{total_monthly_rent}"
    )

    print()
    print("Validation equation:")
    print(
        f"SUM(price) across "
        f"{len(numeric_prices)} "
        f"retrievable rentals where "
        f"normalized locality == "
        f"'{normalized_assigned}'"
    )


if __name__ == "__main__":
    main()