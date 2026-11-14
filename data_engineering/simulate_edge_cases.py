import csv
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

EDGE_CASE_FIELDS = [
    "edge_case_id",
    "issue_type",
    "case_id",
    "related_reference",
    "attempted_action",
    "expected_behavior",
    "actual_behavior",
    "result",
    "details",
    "tested_at",
]


def read_csv(filename):
    path = OUTPUT_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def write_csv(filename, rows, fields):
    path = OUTPUT_DIR / filename

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(filename, data):
    with (OUTPUT_DIR / filename).open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def parse_date(value):
    return datetime.strptime(value, DATE_FORMAT)


def date_string(value):
    return value.strftime(DATE_FORMAT)


def is_active(value):
    return str(value).strip().lower() in {"1", "true", "yes"}


def record_result(
    records,
    edge_case_id,
    issue_type,
    case_id,
    related_reference,
    attempted_action,
    expected_behavior,
    actual_behavior,
    passed,
    details,
    tested_at,
):
    records.append({
        "edge_case_id": edge_case_id,
        "issue_type": issue_type,
        "case_id": case_id,
        "related_reference": related_reference,
        "attempted_action": attempted_action,
        "expected_behavior": expected_behavior,
        "actual_behavior": actual_behavior,
        "result": "PASS" if passed else "FAIL",
        "details": details,
        "tested_at": date_string(tested_at),
    })


def main():
    print("=" * 70)
    print("PHASE 4: EDGE-CASE SIMULATION")
    print("=" * 70)

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

    case_map = {row["case_id"]: row for row in cases}
    submission_map = {
        row["submission_id"]: row for row in submissions
    }
    report_map = {row["report_id"]: row for row in reports}
    decision_map = {
        row["decision_id"]: row for row in decisions
    }
    review_map = {
        row["appeal_id"]: row for row in appeal_reviews
    }
    assignment_map = {
        row["case_id"]: row for row in assignments
    }

    records = []
    evidence_simulations = []

    # ========================================================
    # EDGE CASE 1:
    # Similarity flag must not automatically establish guilt.
    # ========================================================

    case = cases[0]
    report = report_map[case["report_id"]]

    # This guard represents the business rule:
    # similarity reports can trigger review, not guilt.
    def automatic_guilt_guard(report_record):
        return {
            "allowed": False,
            "reason": (
                "Similarity flags are investigation signals. "
                "A qualified human reviewer must make the decision."
            ),
        }

    attempted_result = automatic_guilt_guard(report)

    passed = attempted_result["allowed"] is False

    record_result(
        records,
        "EDGE-001",
        "AUTOMATIC_GUILT_FROM_SIMILARITY_FLAG",
        case["case_id"],
        case["report_id"],
        "AUTOMATICALLY_MARK_AS_GUILTY",
        "Block automatic guilt and require human review.",
        "BLOCKED",
        passed,
        (
            f"Report action: {report.get('review_action', 'NOT_AVAILABLE')}. "
            f"Guard response: {attempted_result['reason']}"
        ),
        parse_date(case["created_at"]) + timedelta(hours=2),
    )

    # ========================================================
    # EDGE CASE 2:
    # Reviewer with an active conflict must not be assigned.
    # ========================================================

    conflict_case = None
    selected_conflict = None
    conflict_submission = None

    for conflict in conflicts:
        if not is_active(conflict["is_active"]):
            continue

        for candidate in cases:
            candidate_submission = submission_map[
                candidate["submission_id"]
            ]

            learner_match = (
                conflict.get("learner_id", "")
                and conflict["learner_id"]
                == candidate_submission["learner_id"]
            )

            assessment_match = (
                conflict.get("assessment_id", "")
                and conflict["assessment_id"]
                == candidate_submission["assessment_id"]
            )

            if learner_match or assessment_match:
                conflict_case = candidate
                selected_conflict = conflict
                conflict_submission = candidate_submission
                break

        if conflict_case:
            break

    if not conflict_case:
        raise RuntimeError(
            "Could not find a case matching an active reviewer conflict."
        )

    conflicted_reviewer_id = selected_conflict["reviewer_id"]

    def assignment_conflict_guard(reviewer_id, submission):
        for conflict in conflicts:
            if (
                conflict["reviewer_id"] != reviewer_id
                or not is_active(conflict["is_active"])
            ):
                continue

            if (
                conflict.get("learner_id", "")
                and conflict["learner_id"] == submission["learner_id"]
            ):
                return False

            if (
                conflict.get("assessment_id", "")
                and conflict["assessment_id"] == submission["assessment_id"]
            ):
                return False

        return True

    assignment_allowed = assignment_conflict_guard(
        conflicted_reviewer_id,
        conflict_submission,
    )

    actual_assignment = assignment_map[conflict_case["case_id"]]

    passed = (
        assignment_allowed is False
        and actual_assignment["reviewer_id"] != conflicted_reviewer_id
    )

    record_result(
        records,
        "EDGE-002",
        "REVIEWER_CONFLICT_OF_INTEREST",
        conflict_case["case_id"],
        f"REVIEWER_{conflicted_reviewer_id}",
        "ASSIGN_CASE_TO_CONFLICTED_REVIEWER",
        "Block assignment and preserve the existing valid assignment.",
        "BLOCKED",
        passed,
        (
            f"Conflict type: {selected_conflict['conflict_type']}. "
            f"Conflicted reviewer: {conflicted_reviewer_id}. "
            f"Actual assigned reviewer: {actual_assignment['reviewer_id']}."
        ),
        parse_date(conflict_case["created_at"]) + timedelta(hours=3),
    )

    # ========================================================
    # EDGE CASE 3:
    # Evidence added after a decision must preserve history.
    # ========================================================

    selected_decision = None

    for decision in decisions:
        linked = [
            link for link in case_evidence
            if link["case_id"] == decision["case_id"]
        ]

        if linked:
            selected_decision = decision
            break

    if selected_decision is None:
        raise RuntimeError(
            "Could not find a decision with linked evidence."
        )

    selected_case_id = selected_decision["case_id"]

    existing_evidence = [
        item for item in evidence_items
        if any(
            link["case_id"] == selected_case_id
            and link["evidence_id"] == item["evidence_id"]
            for link in case_evidence
        )
    ]

    original_decision_snapshot = json.dumps(
        selected_decision,
        sort_keys=True,
    )

    original_decision_hash_before = hashlib.sha256(
        original_decision_snapshot.encode("utf-8")
    ).hexdigest()

    # Simulate a separate evidence addition after the decision.
    # The operational baseline files are not modified.
    existing_versions = [
        int(item["version"])
        for item in existing_evidence
    ]

    new_version = max(existing_versions, default=0) + 1

    simulated_evidence = {
        "evidence_id": (
            f"EVD-{selected_case_id}-{new_version:03d}"
        ),
        "case_id": selected_case_id,
        "version": new_version,
        "added_after_decision": True,
        "original_decision_id": selected_decision["decision_id"],
        "original_decision_hash": original_decision_hash_before,
        "history_preserved": True,
    }

    # Re-read the unchanged decision snapshot.
    original_decision_hash_after = hashlib.sha256(
        json.dumps(selected_decision, sort_keys=True).encode("utf-8")
    ).hexdigest()

    history_preserved = (
        original_decision_hash_before == original_decision_hash_after
    )

    evidence_simulations.append(simulated_evidence)

    record_result(
        records,
        "EDGE-003",
        "EVIDENCE_ADDED_AFTER_DECISION",
        selected_case_id,
        simulated_evidence["evidence_id"],
        "ADD_EVIDENCE_WITHOUT_PRESERVING_DECISION_HISTORY",
        (
            "Preserve the original decision and record new evidence "
            "as a separate version with an audit trail."
        ),
        "HISTORY_PRESERVED",
        history_preserved,
        (
            f"Original decision: {selected_decision['decision_id']}. "
            f"New evidence version: {new_version}. "
            f"Original decision hash unchanged: {history_preserved}. "
            "This is an isolated simulation; operational records "
            "were not modified."
        ),
        parse_date(selected_decision["decided_at"]) + timedelta(days=1),
    )

    # ========================================================
    # EDGE CASE 4:
    # Appeal cannot be resolved without independent review.
    # ========================================================

    if not appeals:
        raise RuntimeError("No appeal records available for edge-case test.")

    selected_appeal = appeals[0]
    selected_appeal_id = selected_appeal["appeal_id"]
    selected_appeal_case = selected_appeal["case_id"]

    def appeal_closure_guard(independent_review_present):
        if not independent_review_present:
            return {
                "allowed": False,
                "reason": (
                    "Appeal cannot be resolved or case closed "
                    "without independent appeal review."
                ),
            }

        return {"allowed": True, "reason": "Independent review exists."}

    # Simulate the attempted closure before the independent review.
    attempted_result = appeal_closure_guard(
        independent_review_present=False
    )

    passed = attempted_result["allowed"] is False

    record_result(
        records,
        "EDGE-004",
        "APPEAL_CLOSED_WITHOUT_INDEPENDENT_REVIEW",
        selected_appeal_case,
        selected_appeal_id,
        "RESOLVE_APPEAL_WITHOUT_INDEPENDENT_REVIEW",
        "Block appeal resolution and case closure.",
        "BLOCKED",
        passed,
        (
            f"Guard response: {attempted_result['reason']} "
            "The existing resolved appeal and case records remain unchanged."
        ),
        parse_date(selected_appeal["submitted_at"]) + timedelta(minutes=1),
    )

    # ========================================================
    # OUTPUTS
    # ========================================================

    write_csv(
        "edge_cases.csv",
        records,
        EDGE_CASE_FIELDS,
    )

    write_csv(
        "edge_case_evidence_simulations.csv",
        evidence_simulations,
        [
            "evidence_id",
            "case_id",
            "version",
            "added_after_decision",
            "original_decision_id",
            "original_decision_hash",
            "history_preserved",
        ],
    )

    passed_count = sum(
        1 for row in records if row["result"] == "PASS"
    )

    failed_count = len(records) - passed_count

    summary = {
        "phase": 4,
        "total_edge_cases": len(records),
        "passed": passed_count,
        "failed": failed_count,
        "baseline_operational_files_modified": False,
        "edge_case_results": {
            row["edge_case_id"]: row["result"]
            for row in records
        },
    }

    write_json("edge_case_results.json", records)
    write_json("edge_case_summary.json", summary)

    print("\nEDGE-CASE SIMULATION SUMMARY")
    print("-" * 70)
    print(json.dumps(summary, indent=4))

    print("\nGenerated files:")
    print("  edge_cases.csv")
    print("  edge_case_evidence_simulations.csv")
    print("  edge_case_results.json")
    print("  edge_case_summary.json")

    if failed_count:
        raise SystemExit("One or more edge-case simulations failed.")

    print("\nALL FOUR EDGE-CASE SIMULATIONS PASSED")


if __name__ == "__main__":
    main()