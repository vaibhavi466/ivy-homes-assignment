import json
from pathlib import Path


FILES = {
    "listings": Path("data/raw/listings.json"),
    "rentals": Path("data/raw/rentals.json"),
    "projects": Path("data/raw/projects.json"),
}

FIELDS = {
    "listings": [
        "locality",
        "furnishing",
        "property_type",
    ],
    "rentals": [
        "locality",
        "furnishing",
        "property_type",
    ],
    "projects": [
        "locality",
        "project_status",
    ],
}


def load_results(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["results"]


def main():
    print(
        "=== Global Lowercase String "
        "Convention Audit ==="
    )

    total_violations = 0

    for collection, path in FILES.items():
        records = load_results(path)

        print()
        print(
            "=" * 70
        )
        print(
            collection.upper()
        )
        print(
            "=" * 70
        )

        print(
            "records:",
            len(records),
        )

        for field in FIELDS[
            collection
        ]:
            missing = []
            non_string = []
            violations = []

            distinct_values = set()

            for record in records:
                record_id = (
                    record.get(
                        "listing_id"
                    )
                    or record.get(
                        "project_id"
                    )
                )

                value = record.get(
                    field
                )

                if value is None:
                    missing.append(
                        record_id
                    )
                    continue

                if not isinstance(
                    value,
                    str,
                ):
                    non_string.append(
                        record_id
                    )
                    continue

                distinct_values.add(
                    value
                )

                if (
                    value
                    != value.lower()
                ):
                    violations.append(
                        (
                            record_id,
                            value,
                        )
                    )

            total_violations += (
                len(violations)
            )

            print()
            print(
                f"field: {field}"
            )

            print(
                "missing:",
                len(missing),
            )

            print(
                "non-string:",
                len(non_string),
            )

            print(
                "mixed/uppercase violations:",
                len(violations),
            )

            print(
                "distinct values:",
                sorted(
                    distinct_values
                ),
            )

            if violations:
                print(
                    "first 20 violations:"
                )

                for item in (
                    violations[:20]
                ):
                    print(item)

    print()
    print(
        "=" * 70
    )

    print(
        "FINAL RESULT"
    )

    print(
        "=" * 70
    )

    print(
        "Total lowercase violations:",
        total_violations,
    )

    print(
        "Convention holds globally:",
        total_violations == 0,
    )


if __name__ == "__main__":
    main()