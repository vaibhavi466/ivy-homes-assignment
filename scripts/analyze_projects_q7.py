import json
from pathlib import Path


PROJECTS_PATH = Path("data/raw/projects.json")

LAKH_TO_INR = 100_000
CRORE_TO_INR = 10_000_000

# Observed data forms two clearly separated numeric clusters:
# low single-digit values and high tens.
UNIT_THRESHOLD = 10


def load_projects():
    with PROJECTS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)["results"]


def price_to_inr(value):
    """
    Observed project-price encoding:

    value < 10  -> crores
    value >= 10 -> lakhs

    This rule is being tested against the complete
    dataset before being accepted.
    """

    if not isinstance(
        value,
        (int, float),
    ):
        raise ValueError(
            f"Non-numeric price value: {value}"
        )

    if value < UNIT_THRESHOLD:
        return round(
            value * CRORE_TO_INR
        )

    return round(
        value * LAKH_TO_INR
    )


def main():
    projects = load_projects()

    print(
        "=== Q7 Unit-Normalization Test ==="
    )
    print(
        f"Projects loaded: {len(projects)}"
    )

    all_values = []

    raw_inverted = []
    normalized_inverted = []

    low_cluster = []
    high_cluster = []

    normalized_projects = []

    for project in projects:
        project_id = project.get(
            "project_id"
        )

        price_min = project.get(
            "price_min"
        )

        price_max = project.get(
            "price_max"
        )

        if not isinstance(
            price_min,
            (int, float),
        ):
            raise RuntimeError(
                f"{project_id}: invalid price_min"
            )

        if not isinstance(
            price_max,
            (int, float),
        ):
            raise RuntimeError(
                f"{project_id}: invalid price_max"
            )

        all_values.extend(
            [price_min, price_max]
        )

        if price_min < 10:
            low_cluster.append(
                price_min
            )
        else:
            high_cluster.append(
                price_min
            )

        if price_max < 10:
            low_cluster.append(
                price_max
            )
        else:
            high_cluster.append(
                price_max
            )

        if price_min > price_max:
            raw_inverted.append(
                project_id
            )

        price_min_inr = price_to_inr(
            price_min
        )

        price_max_inr = price_to_inr(
            price_max
        )

        if (
            price_min_inr
            > price_max_inr
        ):
            normalized_inverted.append(
                project_id
            )

        normalized_projects.append(
            {
                "project_id": project_id,
                "apartment_name":
                    project.get(
                        "apartment_name"
                    ),
                "locality":
                    project.get(
                        "locality"
                    ),
                "raw_price_min":
                    price_min,
                "raw_price_max":
                    price_max,
                "price_min_inr":
                    price_min_inr,
                "price_max_inr":
                    price_max_inr,
            }
        )

    print()
    print("=== Observed Numeric Clusters ===")

    print(
        f"Values < 10: "
        f"{len(low_cluster)}"
    )

    print(
        f"Maximum value < 10: "
        f"{max(low_cluster)}"
    )

    print(
        f"Values >= 10: "
        f"{len(high_cluster)}"
    )

    print(
        f"Minimum value >= 10: "
        f"{min(high_cluster)}"
    )

    print()
    print("=== Range Consistency ===")

    print(
        f"Raw price_min > price_max: "
        f"{len(raw_inverted)}"
    )

    print(
        "After lakh/crore normalization: "
        f"{len(normalized_inverted)}"
    )

    if normalized_inverted:
        print(
            "Still inverted project IDs:"
        )

        for project_id in (
            normalized_inverted[:20]
        ):
            print(project_id)

    sorted_projects = sorted(
        normalized_projects,
        key=lambda project:
            project["price_max_inr"],
        reverse=True,
    )

    print()
    print(
        "=== Top 10 by normalized price_max ==="
    )

    for project in sorted_projects[:10]:
        print(project)

    winner = sorted_projects[0]

    print()
    print("=== Q7 Candidate ===")

    print(
        f"project_id: "
        f"{winner['project_id']}"
    )

    print(
        f"raw price_max: "
        f"{winner['raw_price_max']}"
    )

    print(
        f"price_max_inr: "
        f"{winner['price_max_inr']}"
    )


if __name__ == "__main__":
    main()