import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median


LISTINGS_PATH = Path("data/raw/listings.json")


ULTRA_LOW_IDS = {
    "100-6000578",
    "100-6000678",
    "100-6001599",
    "MAG-6002472",
    "MAG-6002941",
    "SQU-6000395",
}


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


def peer_key(listing):
    return (
        normalize_text(
            listing.get("locality")
        ),
        listing.get("bedroom"),
        normalize_text(
            listing.get("property_type")
        ),
    )


def main():
    listings = load_listings()

    # -----------------------------------------
    # Build normal-price peer groups.
    #
    # Ignore non-positive prices and the six
    # ultra-low candidates while constructing
    # the reference medians.
    # -----------------------------------------

    peer_prices = defaultdict(list)

    for listing in listings:
        price = listing.get("price")

        if (
            listing["listing_id"]
            in ULTRA_LOW_IDS
        ):
            continue

        if (
            not is_number(price)
            or price < 1_000_000
        ):
            continue

        peer_prices[
            peer_key(listing)
        ].append(price)

    peer_medians = {
        key: median(values)
        for key, values
        in peer_prices.items()
        if len(values) >= 10
    }

    scored = []

    for listing in listings:
        price = listing.get("price")

        if (
            not is_number(price)
            or price <= 0
        ):
            continue

        key = peer_key(listing)

        expected = peer_medians.get(
            key
        )

        if expected is None:
            continue

        ratio = price / expected

        scored.append(
            {
                "listing":
                    listing,
                "expected":
                    expected,
                "ratio":
                    ratio,
            }
        )

    scored.sort(
        key=lambda item:
            item["ratio"]
    )

    print(
        "=== Q9 Contact / Bait-Price Investigation ==="
    )

    print()
    print(
        f"Scored listings: {len(scored)}"
    )

    # -----------------------------------------
    # Overall ratio distribution
    # -----------------------------------------

    print()
    print(
        "=== Lowest 40 Price-to-Peer-Median Ratios ==="
    )

    for item in scored[:40]:
        listing = item[
            "listing"
        ]

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
                "property_type":
                    listing.get(
                        "property_type"
                    ),
                "bedroom":
                    listing.get(
                        "bedroom"
                    ),
                "price":
                    listing.get(
                        "price"
                    ),
                "peer_median":
                    round(
                        item[
                            "expected"
                        ],
                        2,
                    ),
                "price_ratio":
                    round(
                        item[
                            "ratio"
                        ],
                        4,
                    ),
                "contact":
                    listing.get(
                        "posted_by_contact"
                    ),
                "is_live":
                    listing.get(
                        "is_live"
                    ),
                "is_verified":
                    listing.get(
                        "is_verified"
                    ),
            }
        )

    # -----------------------------------------
    # Adjacent ratio gaps
    # -----------------------------------------

    print()
    print(
        "=== Largest Adjacent Ratio Gaps ==="
    )

    ratio_gaps = []

    for left, right in zip(
        scored,
        scored[1:],
    ):
        left_ratio = left[
            "ratio"
        ]

        right_ratio = right[
            "ratio"
        ]

        if left_ratio <= 0:
            continue

        ratio_gaps.append(
            (
                right_ratio
                / left_ratio,
                left,
                right,
            )
        )

    ratio_gaps.sort(
        key=lambda item:
            item[0],
        reverse=True,
    )

    for gap, left, right in (
        ratio_gaps[:15]
    ):
        print(
            f"{left['listing']['listing_id']} "
            f"{left['ratio']:.4f} "
            f"-> "
            f"{right['listing']['listing_id']} "
            f"{right['ratio']:.4f} "
            f"(x{gap:.2f})"
        )

    # -----------------------------------------
    # Define a broad inspection set.
    #
    # This is NOT the fake rule.
    # It is intentionally broad so we can see
    # whether suspicious contacts emerge.
    # -----------------------------------------

    suspicious = [
        item
        for item in scored
        if item["ratio"] < 0.65
    ]

    print()
    print(
        "=== Broad Underpricing Inspection Set ==="
    )

    print(
        f"Listings with "
        f"price/peer-median < 0.65: "
        f"{len(suspicious)}"
    )

    # -----------------------------------------
    # Aggregate suspicious records by contact
    # -----------------------------------------

    total_by_contact = Counter(
        listing.get(
            "posted_by_contact"
        )
        for listing in listings
        if listing.get(
            "posted_by_contact"
        )
    )

    suspicious_by_contact = (
        defaultdict(list)
    )

    for item in suspicious:
        contact = item[
            "listing"
        ].get(
            "posted_by_contact"
        )

        suspicious_by_contact[
            contact
        ].append(item)

    ranked_contacts = sorted(
        suspicious_by_contact.items(),
        key=lambda pair: (
            -len(pair[1]),
            pair[0] or "",
        ),
    )

    print()
    print(
        "=== Contacts With Multiple Underpriced Listings ==="
    )

    for contact, items in (
        ranked_contacts
    ):
        if len(items) < 2:
            continue

        ratios = [
            item["ratio"]
            for item in items
        ]

        websites = sorted(
            {
                item["listing"].get(
                    "website"
                )
                for item in items
            }
        )

        print(
            {
                "contact":
                    contact,
                "total_listings":
                    total_by_contact[
                        contact
                    ],
                "underpriced_count":
                    len(items),
                "median_ratio":
                    round(
                        median(ratios),
                        4,
                    ),
                "websites":
                    websites,
                "listing_ids":
                    [
                        item[
                            "listing"
                        ][
                            "listing_id"
                        ]
                        for item in items
                    ],
            }
        )

    # -----------------------------------------
    # Inspect every listing belonging to
    # contacts with >=2 underpriced records.
    # -----------------------------------------

    suspect_contacts = {
        contact
        for contact, items
        in suspicious_by_contact.items()
        if len(items) >= 2
    }

    print()
    print(
        "=== Full Listings For Repeated Suspicious Contacts ==="
    )

    for contact in sorted(
        suspect_contacts
    ):
        print()
        print(
            "=" * 72
        )

        print(
            f"Contact: {contact}"
        )

        contact_listings = [
            listing
            for listing in listings
            if listing.get(
                "posted_by_contact"
            )
            == contact
        ]

        contact_listings.sort(
            key=lambda listing:
                listing[
                    "listing_id"
                ]
        )

        for listing in (
            contact_listings
        ):
            key = peer_key(
                listing
            )

            expected = (
                peer_medians.get(
                    key
                )
            )

            price = listing.get(
                "price"
            )

            ratio = None

            if (
                expected is not None
                and is_number(price)
                and price > 0
            ):
                ratio = (
                    price / expected
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
                    "bedroom":
                        listing.get(
                            "bedroom"
                        ),
                    "price":
                        listing.get(
                            "price"
                        ),
                    "peer_ratio":
                        (
                            round(
                                ratio,
                                4,
                            )
                            if ratio
                            is not None
                            else None
                        ),
                    "is_live":
                        listing.get(
                            "is_live"
                        ),
                    "is_verified":
                        listing.get(
                            "is_verified"
                        ),
                    "posted_by":
                        listing.get(
                            "posted_by"
                        ),
                    "posted_by_name":
                        listing.get(
                            "posted_by_name"
                        ),
                }
            )

    # -----------------------------------------
    # Where do the 6 ultra-low candidates sit?
    # -----------------------------------------

    print()
    print(
        "=== Six Ultra-Low Candidate Ratios ==="
    )

    scored_by_id = {
        item[
            "listing"
        ][
            "listing_id"
        ]: item
        for item in scored
    }

    for listing_id in sorted(
        ULTRA_LOW_IDS
    ):
        item = scored_by_id.get(
            listing_id
        )

        if item is None:
            print(
                f"{listing_id}: "
                "no peer reference"
            )

            continue

        print(
            {
                "listing_id":
                    listing_id,
                "price":
                    item[
                        "listing"
                    ][
                        "price"
                    ],
                "peer_median":
                    item[
                        "expected"
                    ],
                "ratio":
                    round(
                        item[
                            "ratio"
                        ],
                        6,
                    ),
                "contact":
                    item[
                        "listing"
                    ].get(
                        "posted_by_contact"
                    ),
            }
        )

    print()
    print(
        "Do not finalize Q9 yet."
    )


if __name__ == "__main__":
    main()