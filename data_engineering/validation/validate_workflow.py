
import csv
import json
import sys

from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data_engineering" / "output"

passed = 0
errors = []


def read_csv(filename):
    path = OUTPUT / filename

    with open(path, "r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def parse_date(value):
    return datetime.strptime(
        value,
        "%Y-%m-%d %H:%M:%S"
    )


def check(condition, message):
    global passed

    if condition:
        passed += 1
        print(f"[PASS] {message}")
    else:
        errors.append(message)
        print(f"[FAIL] {message}")


def is_active(value):
    return str(value).lower() in ("1", "true", "yes")


def main():
    print("=" * 65)
    print("ACADEMIC INTEGRITY WORKFLOW VALIDATION")
    print("=" * 65)

    # --------------------------------------------------
    # 1. LOAD FILES
    # --------------------------------------------------

    evidence = read_csv("evidence_items.csv")
    links = read_csv("case_evidence.csv")
    conflicts = read_csv("reviewer_conflicts.csv")
    assignments = read_csv("reviewer_assignments.csv")
    cases = read_csv("cases.csv")
    learners = read_csv("learners.csv")
    assessments = read_csv("assessments.csv")
    submissions = read_csv("submissions.csv")
    reviewers = read_csv("reviewers.csv")
    events = read_csv("case_events.csv")
    audit_logs = read_csv("audit_logs.csv")

    # --------------------------------------------------
    # 2. CREATE LOOKUP STRUCTURES
    # --------------------------------------------------

    case_by_id = {
        item["case_id"]: item for item in cases
    }

    evidence_by_id = {
        item["evidence_id"]: item for item in evidence
    }

    learner_ids = {
        item["learner_id"] for item in learners
    }

    assessment_ids = {
        item["assessment_id"] for item in assessments
    }

    reviewer_by_id = {
        item["reviewer_id"]: item for item in reviewers
    }

    submission_by_id = {
        item["submission_id"]: item for item in submissions
    }

    links_by_case = defaultdict(list)

    for link in links:
        links_by_case[link["case_id"]].append(link)

    assignments_by_case = defaultdict(list)

    for assignment in assignments:
        assignments_by_case[
            assignment["case_id"]
        ].append(assignment)

    conflicts_by_reviewer = defaultdict(list)

    for conflict in conflicts:
        conflicts_by_reviewer[
            conflict["reviewer_id"]
        ].append(conflict)

    events_by_case = defaultdict(list)

    for event in events:
        events_by_case[event["case_id"]].append(event)

    audit_by_case = defaultdict(list)

    for log in audit_logs:
        if log["case_id"]:
            audit_by_case[log["case_id"]].append(log)

    # --------------------------------------------------
    # 3. RECORD COUNTS AND PRIMARY KEYS
    # --------------------------------------------------

    print("\n1. RECORD COUNT AND PRIMARY KEY VALIDATION")

    check(len(evidence) > 0, "Evidence records exist")

    check(
        len(evidence) == len(evidence_by_id),
        "Evidence IDs are unique"
    )

    check(
        len(assignments) == len(cases),
        "There is one assignment record per case"
    )

    check(
        len(set(item["case_id"] for item in assignments))
        == len(assignments),
        "Assignment records have unique case IDs"
    )

    check(
        len(conflicts) == 30,
        f"Expected 30 baseline conflicts, found {len(conflicts)}"
    )

    # --------------------------------------------------
    # 4. EVIDENCE RELATIONSHIPS
    # --------------------------------------------------

    print("\n2. EVIDENCE RELATIONSHIP VALIDATION")

    check(
        all(
            link["evidence_id"] in evidence_by_id
            for link in links
        ),
        "Every case-evidence link references existing evidence"
    )

    check(
        all(
            link["case_id"] in case_by_id
            for link in links
        ),
        "Every case-evidence link references an existing case"
    )

    evidence_pairs = [
        (link["case_id"], link["evidence_id"])
        for link in links
    ]

    check(
        len(evidence_pairs) == len(set(evidence_pairs)),
        "No duplicate case-evidence relationships"
    )

    check(
        all(
            len(links_by_case[case_id]) > 0
            for case_id in case_by_id
        ),
        "Every case has at least one evidence item"
    )

    check(
        len(links) == len(evidence),
        "Every generated evidence item is linked exactly once"
    )

    check(
        all(
            item["evidence_type"] in (
                "CODE_MATCH",
                "TEXT_MATCH",
                "DOCUMENT",
                "STATEMENT",
                "OTHER"
            )
            for item in evidence
        ),
        "Evidence types use permitted values"
    )

    check(
        all(
            int(item["version"]) >= 1
            for item in evidence
        ),
        "Evidence versions are valid"
    )

    # --------------------------------------------------
    # 5. REVIEWER CONFLICT VALIDATION
    # --------------------------------------------------

    print("\n3. REVIEWER CONFLICT VALIDATION")

    check(
        all(
            conflict["reviewer_id"] in reviewer_by_id
            for conflict in conflicts
        ),
        "Every conflict references an existing reviewer"
    )

    check(
        all(
            (
                conflict["learner_id"] in learner_ids
                if conflict["learner_id"]
                else True
            )
            for conflict in conflicts
        ),
        "Conflict learner references are valid"
    )

    check(
        all(
            (
                conflict["assessment_id"] in assessment_ids
                if conflict["assessment_id"]
                else True
            )
            for conflict in conflicts
        ),
        "Conflict assessment references are valid"
    )

    check(
        all(
            bool(conflict["learner_id"])
            or bool(conflict["assessment_id"])
            for conflict in conflicts
        ),
        "Every conflict has a learner or assessment target"
    )

    # --------------------------------------------------
    # 6. REVIEWER ASSIGNMENT VALIDATION
    # --------------------------------------------------

    print("\n4. REVIEWER ASSIGNMENT VALIDATION")

    check(
        all(
            assignment["case_id"] in case_by_id
            for assignment in assignments
        ),
        "Every assignment references an existing case"
    )

    check(
        all(
            assignment["reviewer_id"] in reviewer_by_id
            for assignment in assignments
        ),
        "Every assignment references an existing reviewer"
    )

    check(
        all(
            is_active(
                reviewer_by_id[assignment["reviewer_id"]]["is_active"]
            )
            for assignment in assignments
        ),
        "Only active reviewers are assigned"
    )

    check(
        all(
            assignment["assignment_status"] == "ACTIVE"
            for assignment in assignments
        ),
        "All baseline assignments have ACTIVE status"
    )

    check(
        all(
            len(assignments_by_case[case_id]) == 1
            for case_id in case_by_id
        ),
        "Every case has exactly one assignment"
    )

    # --------------------------------------------------
    # 7. CONFLICT-OF-INTEREST PREVENTION
    # --------------------------------------------------

    print("\n5. CONFLICT-OF-INTEREST PREVENTION")

    conflict_free = True

    for assignment in assignments:

        case = case_by_id[assignment["case_id"]]

        submission = submission_by_id[
            case["submission_id"]
        ]

        reviewer_id = assignment["reviewer_id"]

        learner_id = submission["learner_id"]
        assessment_id = submission["assessment_id"]

        for conflict in conflicts_by_reviewer[reviewer_id]:

            if not is_active(conflict["is_active"]):
                continue

            learner_conflict = (
                conflict["learner_id"] != ""
                and conflict["learner_id"] == learner_id
            )

            assessment_conflict = (
                conflict["assessment_id"] != ""
                and conflict["assessment_id"] == assessment_id
            )

            if learner_conflict or assessment_conflict:
                conflict_free = False
                print(
                    "[DETAIL] Conflict assignment found:",
                    case["case_id"],
                    reviewer_id
                )

    check(
        conflict_free,
        "No assigned reviewer has an active conflict"
    )

    # --------------------------------------------------
    # 8. REVIEWER CAPACITY
    # --------------------------------------------------

    print("\n6. REVIEWER CAPACITY VALIDATION")

    reviewer_load = Counter(
        assignment["reviewer_id"]
        for assignment in assignments
        if assignment["assignment_status"] == "ACTIVE"
    )

    capacity_valid = True

    for reviewer_id, count in reviewer_load.items():

        capacity = int(
            reviewer_by_id[reviewer_id]["max_active_cases"]
        )

        if count > capacity:
            capacity_valid = False
            print(
                "[DETAIL] Capacity exceeded:",
                reviewer_id,
                count,
                capacity
            )

    check(
        capacity_valid,
        "No reviewer exceeds maximum active-case capacity"
    )

    check(
        len(reviewer_load) == len(reviewers),
        "All reviewers participate in the baseline assignments"
    )

    # --------------------------------------------------
    # 9. CASE STATUS VALIDATION
    # --------------------------------------------------

    print("\n7. CASE STATUS VALIDATION")

    check(
        all(
            case["case_status"] == "ASSIGNED"
            for case in cases
        ),
        "All baseline cases are in ASSIGNED state"
    )

    check(
        all(
            parse_date(assignment["assigned_at"])
            >= parse_date(
                case_by_id[assignment["case_id"]]["created_at"]
            )
            for assignment in assignments
        ),
        "Assignments occur after case creation"
    )

    # --------------------------------------------------
    # 10. TIMELINE VALIDATION
    # --------------------------------------------------

    print("\n8. CASE TIMELINE VALIDATION")

    event_types = Counter(
        event["event_type"] for event in events
    )

    check(
        event_types["CASE_CREATED"] == len(cases),
        "Every case has a CASE_CREATED event"
    )

    check(
        event_types["EVIDENCE_LINKED"] == len(links),
        "Every evidence link has an EVIDENCE_LINKED event"
    )

    check(
        event_types["REVIEWER_ASSIGNED"] == len(assignments),
        "Every assignment has a REVIEWER_ASSIGNED event"
    )

    check(
        event_types["CASE_STATUS_CHANGED"] == len(cases),
        "Every assigned case has a status-change event"
    )

    check(
        event_types["REVIEWER_ASSIGNMENT_BLOCKED_CONFLICT"] > 0,
        "Conflict-blocked assignment attempts are recorded"
    )

    check(
        all(
            event["case_id"] in case_by_id
            for event in events
        ),
        "All timeline events reference existing cases"
    )

    timeline_dates_valid = True

    for case_id, case_events in events_by_case.items():

        ordered_dates = [
            parse_date(event["occurred_at"])
            for event in case_events
        ]

        if ordered_dates != sorted(ordered_dates):
            timeline_dates_valid = False

    check(
        timeline_dates_valid,
        "Events are chronologically ordered per case"
    )

    # --------------------------------------------------
    # 11. AUDIT VALIDATION
    # --------------------------------------------------

    print("\n9. AUDIT HISTORY VALIDATION")

    audit_actions = Counter(
        log["action"] for log in audit_logs
    )

    check(
        audit_actions["CREATE"] == len(cases),
        "Every case creation has an audit record"
    )

    check(
        audit_actions["LINK_TO_CASE"] == len(links),
        "Every evidence link has an audit record"
    )

    check(
        audit_actions["ASSIGN_REVIEWER"] == len(assignments),
        "Every reviewer assignment has an audit record"
    )

    check(
        audit_actions["STATUS_CHANGE"] == len(cases),
        "Every case status change has an audit record"
    )

    check(
        audit_actions["BLOCKED_CONFLICT_ASSIGNMENT"]
        == event_types["REVIEWER_ASSIGNMENT_BLOCKED_CONFLICT"],
        "Every blocked conflict attempt has an audit record"
    )

    check(
        all(
            log["case_id"] in case_by_id
            for log in audit_logs
            if log["case_id"]
        ),
        "All case-specific audit records reference valid cases"
    )

    # --------------------------------------------------
    # 12. FINAL SUMMARY
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("WORKFLOW VALIDATION SUMMARY")
    print("=" * 65)

    print("Checks passed:", passed)
    print("Checks failed:", len(errors))

    if errors:

        print("\nVALIDATION ERRORS")

        for error in errors:
            print("-", error)

        print("\nWORKFLOW VALIDATION FAILED")
        sys.exit(1)

    print("\nALL WORKFLOW VALIDATION CHECKS PASSED")


if __name__ == "__main__":
    main()
