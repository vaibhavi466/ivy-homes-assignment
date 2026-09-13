import json
import re
from collections import Counter, defaultdict
from pathlib import Path


SUBMISSION = Path("submission.json")

DATA_FILES = {
    "listings": Path("data/raw/listings.json"),
    "rentals": Path("data/raw/rentals.json"),
    "projects": Path("data/raw/projects.json"),
}

ALLOWED_CATEGORIES = {
    "auth",
    "pagination",
    "units",
    "filters",
    "sorting",
    "timestamps",
    "duplicates",
    "completeness",
    "data_quality",
    "fraud",
    "consistency",
    "missing_endpoint",
    "undocumented_endpoint",
}

ROOT_KEYS = {
    "api_key",
    "candidate",
    "answers",
    "findings",
}

CANDIDATE_KEYS = {
    "name",
    "email",
    "repo_url",
    "demo_url",
}

ANSWER_KEYS = {
    "total_listing_records",
    "unique_properties",
    "active_listings",
    "corrupt_listing_ids",
    "total_monthly_rent",
    "avg_price_per_sqft_2bhk",
    "costliest_project",
    "listings_last_7_days",
    "fake_listing_ids",
    "projects_with_wrong_listing_count",
}

FINDING_KEYS = {
    "endpoint",
    "category",
    "documented",
    "actual",
    "how_found",
    "impact",
    "evidence",
}

RECORD_LEVEL_CATEGORIES = {
    "units",
    "duplicates",
    "completeness",
    "data_quality",
    "fraud",
    "consistency",
}


def load_json(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_results(path):
    return load_json(path)["results"]


def main():
    errors = []
    warnings = []

    data = load_json(
        SUBMISSION
    )

    print(
        "=== submission.json Final Validator ==="
    )

    # -----------------------------------------
    # Root schema
    # -----------------------------------------

    print()
    print("=== ROOT SCHEMA ===")

    actual_root = set(
        data.keys()
    )

    print(
        "root keys:",
        sorted(actual_root),
    )

    if actual_root != ROOT_KEYS:
        errors.append(
            "Root keys do not exactly match expected schema."
        )

    # -----------------------------------------
    # Candidate
    # -----------------------------------------

    print()
    print("=== CANDIDATE ===")

    candidate = data.get(
        "candidate",
        {},
    )

    if set(candidate.keys()) != CANDIDATE_KEYS:
        errors.append(
            "Candidate keys do not exactly match template."
        )

    for field in sorted(
        CANDIDATE_KEYS
    ):
        value = candidate.get(
            field
        )

        print(
            f"{field}:",
            "<SET>" if value else "<EMPTY>",
        )

        if not value:
            warnings.append(
                f"candidate.{field} is still empty."
            )

    api_key = data.get(
        "api_key",
        "",
    )

    if (
        not isinstance(
            api_key,
            str,
        )
        or not api_key
    ):
        errors.append(
            "api_key is missing."
        )

    elif (
        "XXXX" in api_key
        or api_key
        == "IVY26-XXXXXXXXXXXX"
    ):
        warnings.append(
            "api_key is still the template placeholder."
        )

    print(
        "api_key:",
        (
            "<PLACEHOLDER>"
            if (
                isinstance(
                    api_key,
                    str,
                )
                and "XXXX"
                in api_key
            )
            else "<SET>"
        ),
    )

    # -----------------------------------------
    # Answers
    # -----------------------------------------

    print()
    print("=== ANSWERS ===")

    answers = data.get(
        "answers",
        {},
    )

    if set(answers.keys()) != ANSWER_KEYS:
        errors.append(
            "Answer keys do not exactly match expected schema."
        )

    expected_fixed_answers = {
        "total_listing_records":
            3500,
        "unique_properties":
            3254,
        "active_listings":
            2792,
        "total_monthly_rent":
            4328000,
        "avg_price_per_sqft_2bhk":
            14230.56,
        "listings_last_7_days":
            129,
        "projects_with_wrong_listing_count":
            106,
    }

    for key, expected in (
        expected_fixed_answers.items()
    ):
        actual = answers.get(
            key
        )

        ok = (
            actual
            == expected
        )

        print(
            f"{key}:",
            actual,
            "OK" if ok else "WRONG",
        )

        if not ok:
            errors.append(
                f"{key} changed from locked answer."
            )

    expected_project = {
        "project_id":
            "P60060",
        "price_max_inr":
            58300000,
    }

    project_answer = answers.get(
        "costliest_project"
    )

    print(
        "costliest_project:",
        project_answer,
    )

    if (
        project_answer
        != expected_project
    ):
        errors.append(
            "costliest_project changed from locked answer."
        )

    for field in [
        "corrupt_listing_ids",
        "fake_listing_ids",
    ]:
        ids = answers.get(
            field,
            [],
        )

        if ids != sorted(ids):
            errors.append(
                f"{field} is not sorted."
            )

        if len(ids) != len(
            set(ids)
        ):
            errors.append(
                f"{field} contains duplicate IDs."
            )

        print(
            field,
            "count:",
            len(ids),
            "sorted:",
            ids == sorted(ids),
            "unique:",
            len(ids)
            == len(set(ids)),
        )

    # -----------------------------------------
    # Known evidence IDs
    # -----------------------------------------

    listing_records = (
        load_results(
            DATA_FILES[
                "listings"
            ]
        )
    )

    rental_records = (
        load_results(
            DATA_FILES[
                "rentals"
            ]
        )
    )

    project_records = (
        load_results(
            DATA_FILES[
                "projects"
            ]
        )
    )

    listing_ids = {
        row["listing_id"]
        for row
        in listing_records
    }

    rental_ids = {
        row["listing_id"]
        for row
        in rental_records
    }

    project_ids = {
        row["project_id"]
        for row
        in project_records
    }

    known_ids = (
        listing_ids
        | rental_ids
        | project_ids
    )

    # Evidence may also legally be
    # phone numbers.
    phone_pattern = re.compile(
        r"^\+\d+$"
    )

    # -----------------------------------------
    # Findings
    # -----------------------------------------

    print()
    print("=== FINDINGS ===")

    findings = data.get(
        "findings",
        [],
    )

    print(
        "finding count:",
        len(findings),
    )

    if not isinstance(
        findings,
        list,
    ):
        errors.append(
            "findings is not a list."
        )
        findings = []

    if len(findings) != 28:
        warnings.append(
            "Finding count is not the expected reviewed count of 28."
        )

    category_counts = Counter()

    exact_fingerprints = set()

    endpoint_category_groups = (
        defaultdict(list)
    )

    empty_evidence = []

    for index, finding in enumerate(
        findings,
        start=1,
    ):
        prefix = (
            f"Finding {index}"
        )

        if not isinstance(
            finding,
            dict,
        ):
            errors.append(
                f"{prefix} is not an object."
            )
            continue

        keys = set(
            finding.keys()
        )

        if keys != FINDING_KEYS:
            errors.append(
                f"{prefix} keys differ from required schema: "
                f"{sorted(keys)}"
            )

        endpoint = finding.get(
            "endpoint"
        )

        category = finding.get(
            "category"
        )

        documented = finding.get(
            "documented"
        )

        actual = finding.get(
            "actual"
        )

        how_found = finding.get(
            "how_found"
        )

        impact = finding.get(
            "impact"
        )

        evidence = finding.get(
            "evidence"
        )

        # Required text fields
        for field_name, value in [
            (
                "endpoint",
                endpoint,
            ),
            (
                "category",
                category,
            ),
            (
                "documented",
                documented,
            ),
            (
                "actual",
                actual,
            ),
            (
                "how_found",
                how_found,
            ),
            (
                "impact",
                impact,
            ),
        ]:
            if (
                not isinstance(
                    value,
                    str,
                )
                or not value.strip()
            ):
                errors.append(
                    f"{prefix}.{field_name} is empty or not a string."
                )

        if (
            category
            not in ALLOWED_CATEGORIES
        ):
            errors.append(
                f"{prefix} uses invalid category: {category}"
            )

        category_counts[
            category
        ] += 1

        if not isinstance(
            evidence,
            list,
        ):
            errors.append(
                f"{prefix}.evidence is not a list."
            )
            evidence = []

        if len(evidence) > 20:
            errors.append(
                f"{prefix} has {len(evidence)} evidence items; max is 20."
            )

        if len(evidence) != len(
            set(evidence)
        ):
            errors.append(
                f"{prefix} contains duplicate evidence values."
            )

        if not evidence:
            empty_evidence.append(
                index
            )

        # Record-level categories should
        # normally have evidence.
        if (
            category
            in RECORD_LEVEL_CATEGORIES
            and not evidence
        ):
            warnings.append(
                f"{prefix} is record-level category '{category}' "
                "but has empty evidence."
            )

        # Evidence must be a known ID
        # or a phone number.
        unknown = []

        for item in evidence:
            if not isinstance(
                item,
                str,
            ):
                unknown.append(
                    item
                )
                continue

            if (
                item not in known_ids
                and not phone_pattern.match(
                    item
                )
            ):
                unknown.append(
                    item
                )

        if unknown:
            errors.append(
                f"{prefix} contains unknown evidence: {unknown}"
            )

        # Catch exact duplicate findings.
        fingerprint = (
            endpoint,
            category,
            (
                documented.strip()
                if isinstance(
                    documented,
                    str,
                )
                else documented
            ),
            (
                actual.strip()
                if isinstance(
                    actual,
                    str,
                )
                else actual
            ),
        )

        if fingerprint in (
            exact_fingerprints
        ):
            errors.append(
                f"{prefix} duplicates an earlier finding exactly."
            )

        exact_fingerprints.add(
            fingerprint
        )

        endpoint_category_groups[
            (
                endpoint,
                category,
            )
        ].append(
            index
        )

        # Required path-parameter format.
        if (
            isinstance(
                endpoint,
                str,
            )
            and (
                "{listing_id}"
                in endpoint
                or "{project_id}"
                in endpoint
            )
        ):
            warnings.append(
                f"{prefix} uses a named path parameter; "
                "submission instructions request {{id}}."
            )

    print(
        "category counts:"
    )

    for category, count in sorted(
        category_counts.items()
    ):
        print(
            f"  {category}: {count}"
        )

    print()
    print(
        "findings with empty evidence:",
        empty_evidence,
    )

    print()
    print(
        "same endpoint + category groups "
        "(manual duplicate-risk review):"
    )

    multi_groups = 0

    for (
        endpoint,
        category,
    ), indices in sorted(
        endpoint_category_groups.items()
    ):
        if len(indices) > 1:
            multi_groups += 1

            print(
                f"  {endpoint} / {category}: "
                f"{indices}"
            )

    if not multi_groups:
        print(
            "  <none>"
        )

    # -----------------------------------------
    # Final result
    # -----------------------------------------

    print()
    print("=" * 72)
    print("FINAL RESULT")
    print("=" * 72)

    print(
        "Errors:",
        len(errors),
    )

    for error in errors:
        print(
            "ERROR:",
            error,
        )

    print()
    print(
        "Warnings:",
        len(warnings),
    )

    for warning in warnings:
        print(
            "WARNING:",
            warning,
        )

    print()

    if errors:
        print(
            "SUBMISSION VALIDATION: FAIL"
        )
    else:
        print(
            "SUBMISSION VALIDATION: PASS"
        )

        if warnings:
            print(
                "Technical schema/evidence checks pass, "
                "but review warnings before final submission."
            )
        else:
            print(
                "No structural or evidence issues detected."
            )


if __name__ == "__main__":
    main()