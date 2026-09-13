import json
from collections import Counter
from pathlib import Path
from statistics import median


LISTINGS_PATH = Path("data/raw/listings.json")

SQFT_PER_SQM = 10.7639104167


def load_listings():
    with LISTINGS_PATH.open(
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


def percentile(values, fraction):
    values = sorted(values)

    if not values:
        return None

    index = round(
        (len(values) - 1)
        * fraction
    )

    return values[index]


def main():
    listings = load_listings()

    positive = [
        listing
        for listing in listings
        if (
            is_number(
                listing.get("price")
            )
            and listing["price"] > 0
        )
    ]

    positive.sort(
        key=lambda listing:
            listing["price"]
    )

    print(
        "=== Q9 Low-Price Cluster Verification ==="
    )

    print()
    print(
        f"Positive-price listings: "
        f"{len(positive)}"
    )

    print()
    print(
        "=== Total Sale Price Buckets ==="
    )

    buckets = Counter()

    for listing in positive:
        price = listing["price"]

        if price < 100_000:
            buckets["<100k"] += 1
        elif price < 1_000_000:
            buckets["100k-999k"] += 1
        elif price < 3_000_000:
            buckets["1m-2.999m"] += 1
        elif price < 5_000_000:
            buckets["3m-4.999m"] += 1
        else:
            buckets[">=5m"] += 1

    for name in [
        "<100k",
        "100k-999k",
        "1m-2.999m",
        "3m-4.999m",
        ">=5m",
    ]:
        print(
            f"{name}: {buckets[name]}"
        )

    print()
    print(
        "=== Lowest 20 Positive Sale Prices ==="
    )

    for listing in positive[:20]:
        print(
            f"{listing['listing_id']}: "
            f"{listing['price']}"
        )

    print()
    print(
        "=== Largest Adjacent Price Ratios ==="
    )

    gaps = []

    for left, right in zip(
        positive,
        positive[1:],
    ):
        left_price = left["price"]
        right_price = right["price"]

        gaps.append(
            (
                right_price / left_price,
                left,
                right,
            )
        )

    gaps.sort(
        key=lambda item:
            item[0],
        reverse=True,
    )

    for ratio, left, right in gaps[:10]:
        print(
            f"{left['listing_id']} "
            f"{left['price']} "
            f"-> "
            f"{right['listing_id']} "
            f"{right['price']} "
            f"(x{ratio:.2f})"
        )

    # -----------------------------------------
    # Candidate cluster
    # -----------------------------------------

    candidates = [
        listing
        for listing in positive
        if listing["price"] < 100_000
    ]

    candidate_ids = {
        listing["listing_id"]
        for listing in candidates
    }

    print()
    print(
        "=== Ultra-Low-Price Candidate Cluster ==="
    )

    print(
        f"Candidates: {len(candidates)}"
    )

    contact_counts = Counter(
        listing.get(
            "posted_by_contact"
        )
        for listing in listings
        if listing.get(
            "posted_by_contact"
        )
    )

    # Build normal PPSF reference distribution.
    normal_ppsf = []

    for listing in listings:
        if (
            listing["listing_id"]
            in candidate_ids
        ):
            continue

        price = listing.get("price")
        carpet = normalized_carpet(
            listing
        )

        if (
            not is_number(price)
            or price <= 0
            or carpet is None
            or carpet <= 0
        ):
            continue

        normal_ppsf.append(
            price / carpet
        )

    print()
    print(
        "=== Normal Listing PPSF Reference ==="
    )

    print(
        f"5th percentile: "
        f"{percentile(normal_ppsf, 0.05):.2f}"
    )

    print(
        f"median: "
        f"{median(normal_ppsf):.2f}"
    )

    print(
        f"95th percentile: "
        f"{percentile(normal_ppsf, 0.95):.2f}"
    )

    print()
    print(
        "=== Candidate Detail Inspection ==="
    )

    for listing in candidates:
        carpet = normalized_carpet(
            listing
        )

        raw_price = listing["price"]

        actual_ppsf = (
            raw_price / carpet
        )

        implied_total_if_ppsf = (
            raw_price * carpet
        )

        same_building_bhk = [
            other
            for other in listings
            if (
                other["listing_id"]
                not in candidate_ids
                and normalize_text(
                    other.get(
                        "locality"
                    )
                )
                == normalize_text(
                    listing.get(
                        "locality"
                    )
                )
                and normalize_text(
                    other.get(
                        "apartment_name"
                    )
                )
                == normalize_text(
                    listing.get(
                        "apartment_name"
                    )
                )
                and other.get(
                    "bedroom"
                )
                == listing.get(
                    "bedroom"
                )
                and is_number(
                    other.get(
                        "price"
                    )
                )
                and other["price"] > 0
            )
        ]

        peer_prices = [
            peer["price"]
            for peer
            in same_building_bhk
        ]

        print()
        print("=" * 70)

        print(
            f"Listing ID: "
            f"{listing['listing_id']}"
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
            f"apartment_name: "
            f"{listing.get('apartment_name')}"
        )

        print(
            f"property_type: "
            f"{listing.get('property_type')}"
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
            f"price/carpet if price is total: "
            f"{actual_ppsf:.2f}"
        )

        print(
            "implied total if raw price "
            f"is actually PPSF: "
            f"{implied_total_if_ppsf:.2f}"
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

        print(
            f"posted_by_name: "
            f"{listing.get('posted_by_name')}"
        )

        print(
            f"contact: "
            f"{listing.get('posted_by_contact')}"
        )

        print(
            "contact total listing count: "
            f"{contact_counts[
                listing.get(
                    'posted_by_contact'
                )
            ]}"
        )

        print(
            f"project_id: "
            f"{listing.get('project_id')}"
        )

        print(
            f"same-building same-BHK "
            f"normal peers: "
            f"{len(peer_prices)}"
        )

        if peer_prices:
            print(
                "peer price range: "
                f"{min(peer_prices)} "
                f"-> {max(peer_prices)}"
            )

            print(
                "peer median price: "
                f"{median(peer_prices):.2f}"
            )

        description = (
            listing.get("description")
            or ""
        )

        print(
            "description: "
            f"{description[:500]!r}"
        )

        print(
            "listing_url: "
            f"{listing.get('listing_url')}"
        )

    print()
    print(
        "Do not finalize Q9 yet."
    )


if __name__ == "__main__":
    main()