
import csv
import json
import sys
from collections import Counter, defaultdict
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


def active(value):
    return str(value).strip().lower() in {"1", "true", "yes"}


def main():
    global passed, failed

    print("=" * 70)
    print("PHASE 3: DECISION AND APPEAL VALIDATION")
    print("=" * 70)

    decisions = read_csv("decisions.csv")
    appeals = read_csv("appeals.csv")
    reviews = read_csv("appeal_reviews.csv")
    cases = read_csv("cases.csv")
    assignments = read_csv("reviewer_assignments.csv")
    conflicts = read_csv("reviewer_conflicts.csv")
    submissions = read_csv("submissions.csv")
    reviewers = read_csv("reviewers.csv")
    events = read_csv("case_events.csv")
    audits = read_csv("audit_logs.csv")
    ground_truth = read_json("ground_truth.json")
    decision_truth = read_csv("decision_ground_truth.csv")
    summary = read_json("decision_appeal_summary.json")

    case_map = {r["case_id"]: r for r in cases}
    assignment_map = {r["case_id"]: r for r in assignments}
    submission_map = {r["submission_id"]: r for r in submissions}
    reviewer_map = {r["reviewer_id"]: r for r in reviewers}
    truth_map = {r["report_id"]: r for r in ground_truth}
    decision_truth_map = {
        r["case_id"]: r for r in decision_truth
    }

    decision_map = {
        r["decision_id"]: r for r in decisions
    }
    appeal_map = {
        r["appeal_id"]: r for r in appeals
    }

    # --------------------------------------------------------
    # 1. RECORD COUNTS AND PRIMARY KEYS
    # --------------------------------------------------------

    print("\n1. RECORD COUNT AND PRIMARY KEY VALIDATION")

    initial_decisions = [
        r for r in decisions
        if r["decision_stage"] == "INITIAL"
    ]

    reassessments = [
        r for r in decisions
        if r["decision_stage"] == "REASSESSMENT"
    ]

    check("Exactly 300 initial decisions exist",
          len(initial_decisions) == 300)

    check("Decision count matches summary",
          len(decisions) == summary["total_decision_records"])

    check("Decision IDs are unique",
          len({r["decision_id"] for r in decisions}) == len(decisions))

    check("Every case has exactly one initial decision",
          len(initial_decisions) == len(cases)
          and {r["case_id"] for r in initial_decisions}
          == set(case_map))

    check("Appeal IDs are unique",
          len({r["appeal_id"] for r in appeals}) == len(appeals))

    check("Appeal review IDs are unique",
          len({r["appeal_review_id"] for r in reviews}) == len(reviews))

    check("Every appeal has exactly one review",
          len(reviews) == len(appeals)
          and Counter(r["appeal_id"] for r in reviews)
          == Counter({r["appeal_id"]: 1 for r in appeals}))

    check("Reassessment count equals appeal count",
          len(reassessments) == len(appeals))

    # --------------------------------------------------------
    # 2. DECISION RELATIONSHIPS AND RATIONALES
    # --------------------------------------------------------

    print("\n2. DECISION RELATIONSHIP VALIDATION")

    decision_types = {
        "NO_VIOLATION",
        "ACADEMIC_MISCONDUCT",
        "INSUFFICIENT_EVIDENCE",
        "REQUEST_MORE_EVIDENCE",
        "UPHELD",
        "OVERTURNED",
        "MODIFIED",
    }

    decision_stages = {"INITIAL", "REASSESSMENT"}

    check("Every decision references an existing case",
          all(r["case_id"] in case_map for r in decisions))

    check("Every decision references an existing reviewer",
          all(r["reviewer_id"] in reviewer_map for r in decisions))

    check("Decision types use permitted values",
          all(r["decision_type"] in decision_types for r in decisions))

    check("Decision stages use permitted values",
          all(r["decision_stage"] in decision_stages for r in decisions))

    check("Every decision has a non-empty rationale",
          all(r["rationale"].strip() for r in decisions))

    check("Every decision has a valid timestamp",
          all(parse_date(r["decided_at"]) for r in decisions))

    initial_reviewer_correct = all(
        r["reviewer_id"] == assignment_map[r["case_id"]]["reviewer_id"]
        for r in initial_decisions
    )

    check("Initial decisions belong to assigned reviewers",
          initial_reviewer_correct)

    reassessment_links_valid = all(
        r["supersedes_decision_id"] in decision_map
        and decision_map[r["supersedes_decision_id"]]["case_id"]
        == r["case_id"]
        and decision_map[r["supersedes_decision_id"]]["decision_stage"]
        == "INITIAL"
        for r in reassessments
    )

    check("Reassessment decisions reference their original decisions",
          reassessment_links_valid)

    # --------------------------------------------------------
    # 3. GROUND TRUTH AND DECISION LOGIC
    # --------------------------------------------------------

    print("\n3. GROUND TRUTH AND DECISION LOGIC")

    initial_by_case = {
        r["case_id"]: r for r in initial_decisions
    }

    truth_mapping_valid = True

    for case in cases:
        truth = truth_map.get(case["report_id"])
        initial = initial_by_case.get(case["case_id"])

        if not truth or not initial:
            truth_mapping_valid = False
            continue

        if truth["expected_outcome"] == "ACADEMIC_MISCONDUCT":
            if initial["decision_type"] != "ACADEMIC_MISCONDUCT":
                truth_mapping_valid = False

        elif truth["expected_outcome"] == "NO_VIOLATION":
            # A documented initial error is allowed only when labelled.
            if initial["decision_type"] not in {
                "NO_VIOLATION", "ACADEMIC_MISCONDUCT"
            }:
                truth_mapping_valid = False

        elif truth["expected_outcome"] == "INSUFFICIENT_EVIDENCE":
            if initial["decision_type"] != "INSUFFICIENT_EVIDENCE":
                truth_mapping_valid = False

    check("Initial decisions follow documented scenario rules",
          truth_mapping_valid)

    check("Decision ground truth covers all 300 cases",
          len(decision_truth) == 300
          and set(decision_truth_map) == set(case_map))

    check("Decision ground truth remains separate from decisions",
          "true_violation" not in decisions[0]
          and "synthetic_label" not in decisions[0])

    documented_errors = [
        r for r in decision_truth
        if r["initial_decision_error"].lower() == "true"
    ]

    actual_errors = []

    for row in decision_truth:
        case = case_map[row["case_id"]]
        initial = initial_by_case[row["case_id"]]
        truth = truth_map[case["report_id"]]

        if (
            truth["expected_outcome"] == "NO_VIOLATION"
            and initial["decision_type"] == "ACADEMIC_MISCONDUCT"
        ):
            actual_errors.append(row["case_id"])

    check("Every initial-review error is explicitly labelled",
          set(actual_errors) == {r["case_id"] for r in documented_errors})

    check("Expected initial-review error count is 17",
          len(documented_errors) == 17)

    # --------------------------------------------------------
    # 4. APPEAL RELATIONSHIPS
    # --------------------------------------------------------

    print("\n4. APPEAL RELATIONSHIP VALIDATION")

    appeal_statuses = {
        "SUBMITTED", "ELIGIBILITY_REVIEW", "ASSIGNED",
        "UNDER_REVIEW", "RESOLVED", "REJECTED", "WITHDRAWN",
    }

    appeal_outcomes = {"UPHELD", "OVERTURNED", "MODIFIED"}

    appeal_relationships_valid = True
    appeal_eligibility_valid = True
    appeal_dates_valid = True

    for appeal in appeals:
        case_id = appeal["case_id"]
        original_id = appeal["original_decision_id"]
        learner_id = appeal["submitted_by_learner_id"]

        original = decision_map.get(original_id)

        if case_id not in case_map:
            appeal_relationships_valid = False
            continue

        if not original or original["case_id"] != case_id:
            appeal_relationships_valid = False
            continue

        if learner_id != submission_map[
            case_map[case_id]["submission_id"]
        ]["learner_id"]:
            appeal_relationships_valid = False

        if original["decision_type"] != "ACADEMIC_MISCONDUCT":
            appeal_eligibility_valid = False

        if appeal["appeal_status"] not in appeal_statuses:
            appeal_relationships_valid = False

        if appeal["appeal_status"] != "RESOLVED":
            appeal_relationships_valid = False

        if appeal["outcome"] not in appeal_outcomes:
            appeal_relationships_valid = False

        if not appeal["appeal_reason"].strip():
            appeal_relationships_valid = False

        if not appeal["resolved_at"] or not appeal["submitted_at"]:
            appeal_dates_valid = False
        else:
            submitted = parse_date(appeal["submitted_at"])
            due = parse_date(appeal["due_at"])
            resolved = parse_date(appeal["resolved_at"])
            decided = parse_date(original["decided_at"])

            if not (decided < submitted <= due and submitted < resolved):
                appeal_dates_valid = False

    check("Every appeal references a valid case and original decision",
          appeal_relationships_valid)

    check("Appeals are submitted only against misconduct decisions",
          appeal_eligibility_valid)

    check("Appeal statuses and outcomes are valid",
          all(
              r["appeal_status"] == "RESOLVED"
              and r["outcome"] in appeal_outcomes
              for r in appeals
          ))

    check("Appeal dates follow the correct sequence",
          appeal_dates_valid)

    # --------------------------------------------------------
    # 5. INDEPENDENT REVIEW AND CONFLICT PREVENTION
    # --------------------------------------------------------

    print("\n5. INDEPENDENT APPEAL REVIEW VALIDATION")

    review_map = {r["appeal_id"]: r for r in reviews}
    independent_review_valid = True
    appeal_conflict_free = True
    review_outcomes_valid = True

    active_conflicts = [
        r for r in conflicts if active(r["is_active"])
    ]

    for appeal in appeals:
        review = review_map.get(appeal["appeal_id"])

        if not review:
            independent_review_valid = False
            continue

        original = decision_map[appeal["original_decision_id"]]
        case = case_map[appeal["case_id"]]
        submission = submission_map[case["submission_id"]]

        original_reviewer = original["reviewer_id"]
        appeal_reviewer = review["reviewer_id"]

        if appeal_reviewer == original_reviewer:
            independent_review_valid = False

        if appeal_reviewer not in reviewer_map:
            independent_review_valid = False
            continue

        if not active(reviewer_map[appeal_reviewer]["is_active"]):
            independent_review_valid = False

        for conflict in active_conflicts:
            if conflict["reviewer_id"] != appeal_reviewer:
                continue

            if (
                conflict["learner_id"]
                and conflict["learner_id"] == submission["learner_id"]
            ):
                appeal_conflict_free = False

            if (
                conflict["assessment_id"]
                and conflict["assessment_id"] == submission["assessment_id"]
            ):
                appeal_conflict_free = False

        if review["outcome"] != appeal["outcome"]:
            review_outcomes_valid = False

        if not review["rationale"].strip():
            review_outcomes_valid = False

        if parse_date(review["reviewed_at"]) < parse_date(
            appeal["submitted_at"]
        ):
            review_outcomes_valid = False

    check("Every appeal has an independent reviewer",
          independent_review_valid)

    check("Appeal reviewers have no active conflicts",
          appeal_conflict_free)

    check("Appeal review outcomes match resolved appeals",
          review_outcomes_valid)

    # --------------------------------------------------------
    # 6. APPEAL OUTCOME AND REASSESSMENT
    # --------------------------------------------------------

    print("\n6. APPEAL OUTCOME VALIDATION")

    reassessment_by_case = {
        r["case_id"]: r for r in reassessments
    }

    appeal_outcome_valid = True
    successful_appeals_valid = True

    for appeal in appeals:
        case_id = appeal["case_id"]
        reassessment = reassessment_by_case.get(case_id)
        expected = decision_truth_map[case_id]["appeal_expected_outcome"]

        if not reassessment:
            appeal_outcome_valid = False
            continue

        if reassessment["decision_type"] != appeal["outcome"]:
            appeal_outcome_valid = False

        if reassessment["supersedes_decision_id"] != (
            appeal["original_decision_id"]
        ):
            appeal_outcome_valid = False

        if appeal["outcome"] != expected:
            appeal_outcome_valid = False

        if (
            decision_truth_map[case_id]["initial_decision_error"] == "true"
            and appeal["outcome"] != "OVERTURNED"
        ):
            successful_appeals_valid = False

    check("Appeal outcomes have corresponding reassessment decisions",
          appeal_outcome_valid)

    check("All documented initial errors are overturned on appeal",
          successful_appeals_valid)

    # --------------------------------------------------------
    # 7. CASE CLOSURE AND ASSIGNMENTS
    # --------------------------------------------------------

    print("\n7. CASE LIFECYCLE VALIDATION")

    check("All 300 cases are CLOSED",
          len(cases) == 300
          and all(r["case_status"] == "CLOSED" for r in cases))

    check("Every closed case has closure timestamp and reason",
          all(
              r["closed_at"] and r["closure_reason"]
              for r in cases
          ))

    check("All original reviewer assignments are COMPLETED",
          all(
              r["assignment_status"] == "COMPLETED"
              and r["ended_at"]
              and r["end_reason"]
              for r in assignments
          ))

    closure_after_review = True

    for appeal in appeals:
        case = case_map[appeal["case_id"]]
        review = review_map[appeal["appeal_id"]]

        if parse_date(case["closed_at"]) < parse_date(
            review["reviewed_at"]
        ):
            closure_after_review = False

    check("Appealed cases close only after independent review",
          closure_after_review)

    no_appeal_cases_valid = True

    appealed_cases = {r["case_id"] for r in appeals}

    for case in cases:
        if case["case_id"] not in appealed_cases:
            if case["closure_reason"] != "CLOSED_AFTER_INITIAL_DECISION":
                no_appeal_cases_valid = False

    check("Non-appealed cases close after initial decisions",
          no_appeal_cases_valid)

    # --------------------------------------------------------
    # 8. TIMELINE VALIDATION
    # --------------------------------------------------------

    print("\n8. CASE TIMELINE VALIDATION")

    events_by_case = defaultdict(list)

    for event in events:
        events_by_case[event["case_id"]].append(event)

    required_event_types = {
        "DECISION_RECORDED",
        "CASE_STATUS_CHANGED",
        "REVIEWER_ASSIGNMENT_COMPLETED",
        "CASE_CLOSED",
    }

    timeline_valid = True
    chronology_valid = True

    for case in cases:
        case_id = case["case_id"]
        case_events = events_by_case[case_id]
        event_types = {r["event_type"] for r in case_events}

        if not required_event_types.issubset(event_types):
            timeline_valid = False

        timestamps = [
            parse_date(r["occurred_at"]) for r in case_events
        ]

        if timestamps != sorted(timestamps):
            chronology_valid = False

        if case_id in appealed_cases:
            required_appeal_events = {
                "APPEAL_SUBMITTED",
                "INDEPENDENT_APPEAL_REVIEW_STARTED",
                "APPEAL_REVIEW_COMPLETED",
                "APPEAL_RESOLVED",
            }

            if not required_appeal_events.issubset(event_types):
                timeline_valid = False

    check("Every case has decision and closure timeline events",
          timeline_valid)

    check("Case events are chronologically ordered",
          chronology_valid)

    check("All timeline events reference existing cases",
          all(r["case_id"] in case_map for r in events))

    # --------------------------------------------------------
    # 9. AUDIT VALIDATION
    # --------------------------------------------------------

    print("\n9. AUDIT HISTORY VALIDATION")

    event_counts = Counter(r["case_id"] for r in events)
    audit_counts = Counter(r["case_id"] for r in audits)

    check("Timeline event and audit record totals match",
          len(events) == len(audits))

    check("Every case has matching event and audit counts",
          all(
              event_counts[case_id] == audit_counts[case_id]
              for case_id in case_map
          ))

    check("Every audit record references an existing case",
          all(r["case_id"] in case_map for r in audits))

    required_actions = {
        "RECORD_INITIAL_DECISION",
        "COMPLETE_REVIEWER_ASSIGNMENT",
        "CLOSE_CASE",
    }

    audit_actions_by_case = defaultdict(set)

    for audit in audits:
        audit_actions_by_case[audit["case_id"]].add(audit["action"])

    audit_valid = all(
        required_actions.issubset(audit_actions_by_case[case_id])
        for case_id in case_map
    )

    check("Every case has decision, assignment and closure audit records",
          audit_valid)

    # --------------------------------------------------------
    # 10. SUMMARY RECONCILIATION
    # --------------------------------------------------------

    print("\n10. SUMMARY RECONCILIATION")

    check("Summary decision count matches generated decisions",
          summary["total_decision_records"] == len(decisions))

    check("Summary appeal count matches generated appeals",
          summary["appeals_created"] == len(appeals))

    check("Summary independent review count matches review records",
          summary["independent_appeal_reviews"] == len(reviews))

    check("Summary closed-case count matches actual cases",
          summary["closed_cases"] == 300)

    check("Summary timeline count matches actual events",
          summary["timeline_event_count"] == len(events))

    check("Summary audit count matches actual audit records",
          summary["audit_record_count"] == len(audits))

    # --------------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("PHASE 3 VALIDATION SUMMARY")
    print("=" * 70)

    print(f"Checks passed: {passed}")
    print(f"Checks failed: {failed}")

    print("\nKey generated counts:")
    print(f"  Initial decisions: {len(initial_decisions)}")
    print(f"  Reassessment decisions: {len(reassessments)}")
    print(f"  Appeals: {len(appeals)}")
    print(f"  Independent reviews: {len(reviews)}")
    print(f"  Overturned appeals: {sum(1 for r in appeals if r['outcome'] == 'OVERTURNED')}")
    print(f"  Closed cases: {sum(1 for r in cases if r['case_status'] == 'CLOSED')}")

    if failed:
        print("\nPHASE 3 VALIDATION FAILED")
        sys.exit(1)

    print("\nALL PHASE 3 VALIDATION CHECKS PASSED")


if __name__ == "__main__":
    main()
