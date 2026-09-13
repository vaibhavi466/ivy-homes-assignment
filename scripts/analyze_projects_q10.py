import json
from collections import Counter, defaultdict
from pathlib import Path


LISTINGS_PATH = Path(
    "data/raw/listings.json"
)

PROJECTS_PATH = Path(
    "data/raw/projects.json"
)


def load_results(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["results"]


def main():
    listings = load_results(
        LISTINGS_PATH
    )

    projects = load_results(
        PROJECTS_PATH
    )

    print(
        "=== Q10 Project Listing Count Investigation ==="
    )

    print()
    print(
        f"Listings loaded: {len(listings)}"
    )

    print(
        f"Projects loaded: {len(projects)}"
    )

    # -----------------------------------------
    # Count listing records by project_id
    # -----------------------------------------

    all_counts = Counter()

    live_counts = Counter()

    for listing in listings:
        project_id = listing.get(
            "project_id"
        )

        if not project_id:
            continue

        all_counts[
            project_id
        ] += 1

        if (
            listing.get(
                "is_live"
            )
            is True
        ):
            live_counts[
                project_id
            ] += 1

    project_ids = {
        project[
            "project_id"
        ]
        for project in projects
    }

    # -----------------------------------------
    # Compare declared counts
    # -----------------------------------------

    matches_all = []
    matches_live = []

    wrong_all = []
    wrong_live = []

    for project in projects:
        project_id = project[
            "project_id"
        ]

        declared = project.get(
            "total_listings"
        )

        actual_all = all_counts.get(
            project_id,
            0,
        )

        actual_live = live_counts.get(
            project_id,
            0,
        )

        if declared == actual_all:
            matches_all.append(
                project_id
            )
        else:
            wrong_all.append(
                (
                    project,
                    actual_all,
                    actual_live,
                )
            )

        if declared == actual_live:
            matches_live.append(
                project_id
            )
        else:
            wrong_live.append(
                (
                    project,
                    actual_all,
                    actual_live,
                )
            )

    print()
    print(
        "=== Agreement Summary ==="
    )

    print(
        "Declared == all associated "
        f"listing records: "
        f"{len(matches_all)}"
    )

    print(
        "Declared != all associated "
        f"listing records: "
        f"{len(wrong_all)}"
    )

    print(
        "Declared == live associated "
        f"listing records: "
        f"{len(matches_live)}"
    )

    print(
        "Declared != live associated "
        f"listing records: "
        f"{len(wrong_live)}"
    )

    # -----------------------------------------
    # Totals
    # -----------------------------------------

    declared_sum = sum(
        project.get(
            "total_listings",
            0,
        )
        for project
        in projects
    )

    all_sum = sum(
        all_counts.get(
            project[
                "project_id"
            ],
            0,
        )
        for project
        in projects
    )

    live_sum = sum(
        live_counts.get(
            project[
                "project_id"
            ],
            0,
        )
        for project
        in projects
    )

    print()
    print(
        "=== Aggregate Counts ==="
    )

    print(
        f"Sum declared total_listings: "
        f"{declared_sum}"
    )

    print(
        "Actual associated listing "
        f"records: {all_sum}"
    )

    print(
        "Actual associated live "
        f"listing records: {live_sum}"
    )

    # -----------------------------------------
    # Listing-side project IDs
    # -----------------------------------------

    listing_project_ids = set(
        all_counts
    )

    unknown_project_ids = sorted(
        listing_project_ids
        - project_ids
    )

    print()
    print(
        "=== Listing project_id integrity ==="
    )

    print(
        "Distinct project_ids used "
        f"by listings: "
        f"{len(listing_project_ids)}"
    )

    print(
        "Listing project_ids absent "
        f"from projects endpoint: "
        f"{len(unknown_project_ids)}"
    )

    print(
        "First 20 unknown IDs:"
    )

    print(
        unknown_project_ids[:20]
    )

    # -----------------------------------------
    # Mismatch direction
    # -----------------------------------------

    all_direction = Counter()

    for (
        project,
        actual_all,
        actual_live,
    ) in wrong_all:
        declared = project[
            "total_listings"
        ]

        if declared > actual_all:
            all_direction[
                "declared_too_high"
            ] += 1
        elif declared < actual_all:
            all_direction[
                "declared_too_low"
            ] += 1

    print()
    print(
        "=== All-record mismatch direction ==="
    )

    print(
        dict(all_direction)
    )

    # -----------------------------------------
    # Detailed mismatches
    # -----------------------------------------

    print()
    print(
        "=== First 50 Projects Wrong "
        "Against ALL Listings ==="
    )

    for (
        project,
        actual_all,
        actual_live,
    ) in wrong_all[:50]:
        print(
            {
                "project_id":
                    project[
                        "project_id"
                    ],
                "apartment_name":
                    project.get(
                        "apartment_name"
                    ),
                "declared":
                    project.get(
                        "total_listings"
                    ),
                "actual_all":
                    actual_all,
                "actual_live":
                    actual_live,
            }
        )

    print()
    print(
        "=== First 50 Projects Wrong "
        "Against LIVE Listings ==="
    )

    for (
        project,
        actual_all,
        actual_live,
    ) in wrong_live[:50]:
        print(
            {
                "project_id":
                    project[
                        "project_id"
                    ],
                "apartment_name":
                    project.get(
                        "apartment_name"
                    ),
                "declared":
                    project.get(
                        "total_listings"
                    ),
                "actual_all":
                    actual_all,
                "actual_live":
                    actual_live,
            }
        )

    # -----------------------------------------
    # Difference distributions
    # -----------------------------------------

    diff_all = Counter(
        project[
            "total_listings"
        ]
        - actual_all
        for (
            project,
            actual_all,
            _,
        ) in wrong_all
    )

    diff_live = Counter(
        project[
            "total_listings"
        ]
        - actual_live
        for (
            project,
            _,
            actual_live,
        ) in wrong_live
    )

    print()
    print(
        "=== Difference Distribution: "
        "declared - actual_all ==="
    )

    for diff, count in sorted(
        diff_all.items()
    ):
        print(
            f"{diff}: {count}"
        )

    print()
    print(
        "=== Difference Distribution: "
        "declared - actual_live ==="
    )

    for diff, count in sorted(
        diff_live.items()
    ):
        print(
            f"{diff}: {count}"
        )

    print()
    print(
        "Do not finalize Q10 yet."
    )


if __name__ == "__main__":
    main()