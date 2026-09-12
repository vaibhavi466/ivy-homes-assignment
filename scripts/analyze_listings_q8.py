import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


LISTINGS_PATH = Path("data/raw/listings.json")

IST = timezone(
    timedelta(
        hours=5,
        minutes=30,
    )
)

UTC = timezone.utc

REFERENCE = datetime.fromisoformat(
    "2026-09-10T00:00:00+05:30"
)

WINDOW_START = REFERENCE - timedelta(days=7)
WINDOW_END = REFERENCE


def load_listings():
    with LISTINGS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        snapshot = json.load(file)

    return (
        snapshot["metadata"],
        snapshot["results"],
    )


def parse_naive_timestamp(value):
    if not isinstance(value, str):
        raise ValueError(
            f"Timestamp is not a string: {value!r}"
        )

    parsed = datetime.fromisoformat(
        value.strip()
    )

    if parsed.tzinfo is not None:
        raise ValueError(
            f"Expected naive timestamp but got "
            f"timezone-aware value: {value}"
        )

    return parsed


def classify(records, assumed_timezone):
    qualifying = []
    before = []
    at_or_after = []

    for record in records:
        aware = record["naive"].replace(
            tzinfo=assumed_timezone
        )

        if aware < WINDOW_START:
            before.append(record)

        elif aware >= WINDOW_END:
            at_or_after.append(record)

        else:
            qualifying.append(record)

    return (
        before,
        qualifying,
        at_or_after,
    )


def main():
    metadata, listings = load_listings()

    print(
        "=== Q8 Timestamp Interpretation Analysis ==="
    )

    print()
    print(
        f"Listings loaded: {len(listings)}"
    )

    if (
        len(listings)
        != metadata["records_retrieved"]
    ):
        raise RuntimeError(
            "Snapshot metadata does not match "
            "stored listings."
        )

    if metadata["final_has_more"] is not False:
        raise RuntimeError(
            "Listings snapshot did not reach "
            "the end of pagination."
        )

    print()
    print("=== Fixed Assignment Window ===")

    print(
        f"Window start inclusive: "
        f"{WINDOW_START.isoformat()}"
    )

    print(
        f"Window end exclusive: "
        f"{WINDOW_END.isoformat()}"
    )

    parsed_records = []
    failures = []

    for listing in listings:
        listing_id = listing.get(
            "listing_id"
        )

        value = listing.get(
            "posted_at"
        )

        try:
            naive = parse_naive_timestamp(
                value
            )
        except Exception as exc:
            failures.append(
                {
                    "listing_id": listing_id,
                    "posted_at": value,
                    "error": str(exc),
                }
            )
            continue

        parsed_records.append(
            {
                "listing_id": listing_id,
                "raw": value,
                "naive": naive,
            }
        )

    print()
    print("=== Timestamp Validation ===")

    print(
        f"Successfully parsed naive timestamps: "
        f"{len(parsed_records)}"
    )

    print(
        f"Parse failures: "
        f"{len(failures)}"
    )

    if failures:
        print()
        print("First 10 failures:")

        for failure in failures[:10]:
            print(failure)

        return

    naive_values = [
        record["naive"]
        for record in parsed_records
    ]

    print()
    print("=== Raw Naive Timestamp Range ===")

    print(
        f"Earliest raw posted_at: "
        f"{min(naive_values).isoformat()}"
    )

    print(
        f"Latest raw posted_at: "
        f"{max(naive_values).isoformat()}"
    )

    (
        ist_before,
        ist_inside,
        ist_after,
    ) = classify(
        parsed_records,
        IST,
    )

    (
        utc_before,
        utc_inside,
        utc_after,
    ) = classify(
        parsed_records,
        UTC,
    )

    print()
    print(
        "=== Interpretation A: "
        "Naive timestamps are Asia/Kolkata ==="
    )

    print(
        f"Before window: "
        f"{len(ist_before)}"
    )

    print(
        f"Inside Q8 window: "
        f"{len(ist_inside)}"
    )

    print(
        f"At/after reference: "
        f"{len(ist_after)}"
    )

    print()
    print(
        "=== Interpretation B: "
        "Naive timestamps are UTC ==="
    )

    print(
        f"Before window: "
        f"{len(utc_before)}"
    )

    print(
        f"Inside Q8 window: "
        f"{len(utc_inside)}"
    )

    print(
        f"At/after reference: "
        f"{len(utc_after)}"
    )

    ist_ids = {
        record["listing_id"]
        for record in ist_inside
    }

    utc_ids = {
        record["listing_id"]
        for record in utc_inside
    }

    only_ist = sorted(
        ist_ids - utc_ids
    )

    only_utc = sorted(
        utc_ids - ist_ids
    )

    print()
    print("=== Boundary Sensitivity ===")

    print(
        f"Count if IST: "
        f"{len(ist_inside)}"
    )

    print(
        f"Count if UTC: "
        f"{len(utc_inside)}"
    )

    print(
        f"Difference in counts: "
        f"{abs(len(ist_inside) - len(utc_inside))}"
    )

    print(
        f"Records only qualifying under IST: "
        f"{len(only_ist)}"
    )

    print(
        f"Records only qualifying under UTC: "
        f"{len(only_utc)}"
    )

    if only_ist:
        print()
        print(
            "First 20 IDs only qualifying under IST:"
        )

        for listing_id in only_ist[:20]:
            print(listing_id)

    if only_utc:
        print()
        print(
            "First 20 IDs only qualifying under UTC:"
        )

        for listing_id in only_utc[:20]:
            print(listing_id)

    print()
    print("=== Q8 Decision Check ===")

    if len(ist_inside) == len(utc_inside):
        print(
            "Q8 count is timezone-insensitive "
            "for the two tested interpretations."
        )

        print(
            f"Candidate listings_last_7_days: "
            f"{len(ist_inside)}"
        )

    else:
        print(
            "Q8 count depends on timezone "
            "interpretation."
        )

        print(
            "Do not finalize Q8 yet."
        )


if __name__ == "__main__":
    main()