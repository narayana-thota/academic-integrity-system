
import csv
import json
import sys
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "output"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

passed = 0
failed = 0


def check(description, condition):
    global passed, failed

    if condition:
        passed += 1
        print(f"[PASS] {description}")
    else:
        failed += 1
        print(f"[FAIL] {description}")


def read_csv(filename):
    path = OUTPUT_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def read_json(filename):
    path = OUTPUT_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_date(value):
    return datetime.strptime(value, DATE_FORMAT)


def is_active(value):
    return str(value).strip().lower() in {"1", "true", "yes"}


def main():
    global passed, failed

    print("=" * 70)
    print("PHASE 4: EDGE-CASE VALIDATION")
    print("=" * 70)

    edge_cases = read_csv("edge_cases.csv")
    evidence_simulations = read_csv(
        "edge_case_evidence_simulations.csv"
    )
    result_json = read_json("edge_case_results.json")
    summary = read_json("edge_case_summary.json")

    cases = read_csv("cases.csv")
    submissions = read_csv("submissions.csv")
    reports = read_csv("similarity_reports.csv")
    evidence_items = read_csv("evidence_items.csv")
    case_evidence = read_csv("case_evidence.csv")
    decisions = read_csv("decisions.csv")
    appeals = read_csv("appeals.csv")
    appeal_reviews = read_csv("appeal_reviews.csv")
    conflicts = read_csv("reviewer_conflicts.csv")
    assignments = read_csv("reviewer_assignments.csv")

    case_map = {r["case_id"]: r for r in cases}
    submission_map = {
        r["submission_id"]: r for r in submissions
    }
    report_map = {r["report_id"]: r for r in reports}
    decision_map = {
        r["decision_id"]: r for r in decisions
    }
    appeal_map = {
        r["appeal_id"]: r for r in appeals
    }
    review_map = {
        r["appeal_id"]: r for r in appeal_reviews
    }
    assignment_map = {
        r["case_id"]: r for r in assignments
    }

    edge_map = {
        r["edge_case_id"]: r for r in edge_cases
    }

    required_ids = {
        "EDGE-001",
        "EDGE-002",
        "EDGE-003",
        "EDGE-004",
    }

    # --------------------------------------------------------
    # 1. OUTPUT AND RECORD VALIDATION
    # --------------------------------------------------------

    print("\n1. EDGE-CASE OUTPUT VALIDATION")

    check(
        "Exactly four edge cases were generated",
        len(edge_cases) == 4,
    )

    check(
        "All four required edge-case IDs exist",
        set(edge_map) == required_ids,
    )

    check(
        "Edge-case IDs are unique",
        len(edge_map) == len(edge_cases),
    )

    check(
        "Every edge-case result is PASS",
        all(r["result"] == "PASS" for r in edge_cases),
    )

    check(
        "JSON results match CSV results",
        {
            r["edge_case_id"]: r["result"] for r in result_json
        } == {
            r["edge_case_id"]: r["result"] for r in edge_cases
        },
    )

    # --------------------------------------------------------
    # 2. EDGE CASE 1: NO AUTOMATIC GUILT
    # --------------------------------------------------------

    print("\n2. AUTOMATIC GUILT PREVENTION")

    edge1 = edge_map.get("EDGE-001")
    edge1_valid = False

    if edge1:
        report = report_map.get(edge1["related_reference"])
        case = case_map.get(edge1["case_id"])

        edge1_valid = (
            report is not None
            and case is not None
            and case["report_id"] == edge1["related_reference"]
            and edge1["attempted_action"]
            == "AUTOMATICALLY_MARK_AS_GUILTY"
            and edge1["actual_behavior"] == "BLOCKED"
            and edge1["result"] == "PASS"
            and "human review" in edge1["expected_behavior"].lower()
        )

    check(
        "Similarity flag cannot automatically establish guilt",
        edge1_valid,
    )

    # --------------------------------------------------------
    # 3. EDGE CASE 2: CONFLICT OF INTEREST
    # --------------------------------------------------------

    print("\n3. REVIEWER CONFLICT PREVENTION")

    edge2 = edge_map.get("EDGE-002")
    edge2_valid = False

    if edge2:
        reviewer_id = edge2["related_reference"].replace(
            "REVIEWER_", ""
        )

        case = case_map.get(edge2["case_id"])

        if case:
            submission = submission_map[case["submission_id"]]
            assignment = assignment_map.get(case["case_id"])

            matching_conflicts = []

            for conflict in conflicts:
                if (
                    conflict["reviewer_id"] != reviewer_id
                    or not is_active(conflict["is_active"])
                ):
                    continue

                learner_match = (
                    conflict.get("learner_id", "")
                    and conflict["learner_id"]
                    == submission["learner_id"]
                )

                assessment_match = (
                    conflict.get("assessment_id", "")
                    and conflict["assessment_id"]
                    == submission["assessment_id"]
                )

                if learner_match or assessment_match:
                    matching_conflicts.append(conflict)

            edge2_valid = (
                bool(matching_conflicts)
                and assignment is not None
                and assignment["reviewer_id"] != reviewer_id
                and edge2["actual_behavior"] == "BLOCKED"
                and edge2["result"] == "PASS"
            )

    check(
        "Conflicted reviewer assignment is blocked",
        edge2_valid,
    )

    # --------------------------------------------------------
    # 4. EDGE CASE 3: EVIDENCE HISTORY PRESERVATION
    # --------------------------------------------------------

    print("\n4. POST-DECISION EVIDENCE HISTORY")

    edge3 = edge_map.get("EDGE-003")
    evidence_valid = False

    if edge3 and len(evidence_simulations) == 1:
        simulation = evidence_simulations[0]

        original_decision = decision_map.get(
            simulation["original_decision_id"]
        )

        existing_versions = [
            int(item["version"])
            for item in evidence_items
            if item["evidence_id"] in {
                link["evidence_id"]
                for link in case_evidence
                if link["case_id"] == simulation["case_id"]
            }
        ]

        evidence_valid = (
            original_decision is not None
            and original_decision["case_id"] == simulation["case_id"]
            and simulation["added_after_decision"].lower() == "true"
            and simulation["history_preserved"].lower() == "true"
            and int(simulation["version"])
            > max(existing_versions, default=0)
            and simulation["original_decision_hash"].strip() != ""
            and edge3["actual_behavior"] == "HISTORY_PRESERVED"
            and edge3["result"] == "PASS"
        )

    check(
        "New evidence uses a separate version and preserves decision history",
        evidence_valid,
    )

    check(
        "Original operational evidence records remain unchanged",
        all(
            simulation["evidence_id"]
            not in {item["evidence_id"] for item in evidence_items}
            for simulation in evidence_simulations
        ),
    )

    # --------------------------------------------------------
    # 5. EDGE CASE 4: APPEAL CANNOT CLOSE WITHOUT REVIEW
    # --------------------------------------------------------

    print("\n5. APPEAL REVIEW REQUIREMENT")

    edge4 = edge_map.get("EDGE-004")
    edge4_valid = False

    if edge4:
        appeal = appeal_map.get(edge4["related_reference"])
        review = review_map.get(edge4["related_reference"])

        if appeal and review:
            attempted_time = parse_date(edge4["tested_at"])
            review_time = parse_date(review["reviewed_at"])

            edge4_valid = (
                appeal["case_id"] == edge4["case_id"]
                and attempted_time < review_time
                and edge4["attempted_action"]
                == "RESOLVE_APPEAL_WITHOUT_INDEPENDENT_REVIEW"
                and edge4["actual_behavior"] == "BLOCKED"
                and edge4["result"] == "PASS"
            )

    check(
        "Appeal closure before independent review is blocked",
        edge4_valid,
    )

    # --------------------------------------------------------
    # 6. BASELINE PRESERVATION
    # --------------------------------------------------------

    print("\n6. BASELINE DATASET PRESERVATION")

    check(
        "All baseline cases remain closed",
        len(cases) == 300
        and all(r["case_status"] == "CLOSED" for r in cases),
    )

    check(
        "Baseline decisions remain present",
        len(decisions) == 341,
    )

    check(
        "Baseline appeals remain present",
        len(appeals) == 41,
    )

    check(
        "Baseline appeal reviews remain present",
        len(appeal_reviews) == 41,
    )

    check(
        "Baseline reviewer assignments remain completed",
        len(assignments) == 300
        and all(
            r["assignment_status"] == "COMPLETED"
            for r in assignments
        ),
    )

    # --------------------------------------------------------
    # 7. SUMMARY VALIDATION
    # --------------------------------------------------------

    print("\n7. EDGE-CASE SUMMARY VALIDATION")

    check(
        "Summary contains four edge cases",
        summary["total_edge_cases"] == 4,
    )

    check(
        "Summary passed count matches CSV",
        summary["passed"] == sum(
            1 for r in edge_cases if r["result"] == "PASS"
        ),
    )

    check(
        "Summary failed count matches CSV",
        summary["failed"] == sum(
            1 for r in edge_cases if r["result"] == "FAIL"
        ),
    )

    check(
        "Summary confirms baseline files were not modified",
        summary["baseline_operational_files_modified"] is False,
    )

    # --------------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("PHASE 4 VALIDATION SUMMARY")
    print("=" * 70)

    print(f"Checks passed: {passed}")
    print(f"Checks failed: {failed}")

    for row in edge_cases:
        print(
            f"{row['edge_case_id']} | "
            f"{row['issue_type']} | {row['result']}"
        )

    if failed:
        print("\nPHASE 4 VALIDATION FAILED")
        sys.exit(1)

    print("\nALL PHASE 4 VALIDATION CHECKS PASSED")


if __name__ == "__main__":
    main()

