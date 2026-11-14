
import csv
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================
# PHASE 3: DECISION AND APPEAL RECORD GENERATOR
# Seed: 20261024
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
SNAPSHOT_DIR = OUTPUT_DIR / "phase2_snapshot"

SEED = 20261024
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

FILES = {
    "cases": "cases.csv",
    "assignments": "reviewer_assignments.csv",
    "conflicts": "reviewer_conflicts.csv",
    "learners": "learners.csv",
    "submissions": "submissions.csv",
    "reviewers": "reviewers.csv",
    "events": "case_events.csv",
    "audits": "audit_logs.csv",
    "ground_truth": "ground_truth.json",
}

DECISION_FIELDS = [
    "decision_id",
    "case_id",
    "reviewer_id",
    "decision_type",
    "decision_stage",
    "rationale",
    "decided_at",
    "supersedes_decision_id",
]

APPEAL_FIELDS = [
    "appeal_id",
    "case_id",
    "original_decision_id",
    "submitted_by_learner_id",
    "appeal_reason",
    "appeal_status",
    "submitted_at",
    "due_at",
    "outcome",
    "resolved_at",
]

APPEAL_REVIEW_FIELDS = [
    "appeal_review_id",
    "appeal_id",
    "reviewer_id",
    "outcome",
    "rationale",
    "reviewed_at",
]

DECISION_GROUND_TRUTH_FIELDS = [
    "case_id",
    "report_id",
    "scenario_type",
    "expected_outcome",
    "initial_decision_error",
    "appeal_expected_outcome",
]


def read_csv(filename):
    path = OUTPUT_DIR / filename
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def write_csv(filename, rows, fieldnames=None):
    path = OUTPUT_DIR / filename

    if fieldnames is None:
        if not rows:
            raise ValueError(f"Cannot determine CSV columns for {filename}")
        fieldnames = list(rows[0].keys())

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def parse_date(value):
    return datetime.strptime(value, DATE_FORMAT)


def format_date(value):
    return value.strftime(DATE_FORMAT)


def is_active(value):
    return str(value).strip().lower() in {"1", "true", "yes"}


def load_inputs():
    data = {}

    for key, filename in FILES.items():
        if key == "ground_truth":
            with (OUTPUT_DIR / filename).open(
                "r", encoding="utf-8"
            ) as file:
                data[key] = json.load(file)
        else:
            data[key] = read_csv(filename)

    return data


def validate_inputs(data):
    required_files = [
        OUTPUT_DIR / filename
        for filename in FILES.values()
    ]

    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Required Phase 1/2 files are missing:\n" + "\n".join(missing)
        )

    if OUTPUT_DIR.joinpath("decisions.csv").exists():
        raise FileExistsError(
            "Phase 3 outputs already exist. Do not run this generator again "
            "on modified Phase 3 data. Restore the Phase 2 snapshot first "
            "if you intentionally need a clean regeneration."
        )

    cases = data["cases"]
    assignments = data["assignments"]

    if len(cases) != 300:
        raise ValueError(f"Expected 300 cases, found {len(cases)}")

    if len(assignments) != len(cases):
        raise ValueError("Every case must have one reviewer assignment")

    for case in cases:
        if case["case_status"] != "ASSIGNED":
            raise ValueError(
                f"Case {case['case_id']} is not ASSIGNED"
            )

    for assignment in assignments:
        if assignment["assignment_status"] != "ACTIVE":
            raise ValueError(
                f"Assignment for {assignment['case_id']} is not ACTIVE"
            )


def create_phase2_snapshot():
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    for filename in [
        "cases.csv",
        "reviewer_assignments.csv",
        "case_events.csv",
        "audit_logs.csv",
    ]:
        source = OUTPUT_DIR / filename
        destination = SNAPSHOT_DIR / filename
        shutil.copy2(source, destination)


def main():
    print("=" * 68)
    print("PHASE 3: DECISION AND APPEAL RECORD GENERATION")
    print("=" * 68)

    data = load_inputs()
    validate_inputs(data)
    create_phase2_snapshot()

    cases = sorted(data["cases"], key=lambda row: row["case_id"])
    assignments = {
        row["case_id"]: row for row in data["assignments"]
    }
    submissions = {
        row["submission_id"]: row for row in data["submissions"]
    }
    reviewers = {
        row["reviewer_id"]: row for row in data["reviewers"]
    }
    ground_truth = {
        row["report_id"]: row for row in data["ground_truth"]
    }

    # --------------------------------------------------------
    # Build active conflict lookup
    # --------------------------------------------------------

    active_conflicts = defaultdict(list)

    for conflict in data["conflicts"]:
        if is_active(conflict["is_active"]):
            active_conflicts[conflict["reviewer_id"]].append(conflict)

    def reviewer_has_conflict(reviewer_id, learner_id, assessment_id):
        for conflict in active_conflicts.get(reviewer_id, []):
            learner_conflict = conflict.get("learner_id", "")
            assessment_conflict = conflict.get("assessment_id", "")

            if learner_conflict and learner_conflict == learner_id:
                return True

            if assessment_conflict and assessment_conflict == assessment_id:
                return True

        return False

    active_reviewers = [
        reviewer
        for reviewer in data["reviewers"]
        if is_active(reviewer["is_active"])
    ]

    # --------------------------------------------------------
    # Prepare output collections
    # --------------------------------------------------------

    decisions = []
    appeals = []
    appeal_reviews = []
    decision_ground_truth = []

    updated_cases = [dict(row) for row in data["cases"]]
    updated_assignments = [
        dict(row) for row in data["assignments"]
    ]
    events = [dict(row) for row in data["events"]]
    audits = [dict(row) for row in data["audits"]]

    case_lookup = {
        row["case_id"]: row for row in updated_cases
    }
    assignment_lookup = {
        row["case_id"]: row for row in updated_assignments
    }

    next_decision_id = 1
    next_appeal_review_id = 1

    appeal_reviewer_load = Counter()
    decision_counts = Counter()
    appeal_counts = Counter()
    initial_error_count = 0

    # --------------------------------------------------------
    # Timeline and audit helpers
    # --------------------------------------------------------

    def add_event(case_id, event_type, description, actor, timestamp, payload):
        events.append({
            "case_id": case_id,
            "event_type": event_type,
            "event_description": description,
            "actor_reference": actor,
            "event_data": json.dumps(payload, sort_keys=True),
            "occurred_at": format_date(timestamp),
        })

    def add_audit(
        case_id,
        actor_type,
        actor,
        entity_type,
        entity_reference,
        action,
        timestamp,
        payload,
    ):
        audits.append({
            "case_id": case_id,
            "actor_type": actor_type,
            "actor_reference": actor,
            "entity_type": entity_type,
            "entity_reference": entity_reference,
            "action": action,
            "event_data": json.dumps(payload, sort_keys=True),
            "created_at": format_date(timestamp),
        })

    def change_case_status(case, new_status, timestamp, actor):
        old_status = case["case_status"]
        case["case_status"] = new_status

        add_event(
            case["case_id"],
            "CASE_STATUS_CHANGED",
            f"Case status changed from {old_status} to {new_status}.",
            actor,
            timestamp,
            {"previous_status": old_status, "new_status": new_status},
        )

        add_audit(
            case["case_id"],
            "SYSTEM",
            actor,
            "CASE",
            case["case_id"],
            "STATUS_CHANGE",
            timestamp,
            {"previous_status": old_status, "new_status": new_status},
        )

    # --------------------------------------------------------
    # Independent appeal reviewer selection
    # --------------------------------------------------------

    def select_appeal_reviewer(
        original_reviewer_id,
        learner_id,
        assessment_id,
    ):
        eligible = []

        for reviewer in active_reviewers:
            reviewer_id = reviewer["reviewer_id"]

            if reviewer_id == original_reviewer_id:
                continue

            if reviewer_has_conflict(
                reviewer_id, learner_id, assessment_id
            ):
                continue

            eligible.append(reviewer)

        if not eligible:
            raise RuntimeError(
                "No independent conflict-free reviewer available "
                f"for learner {learner_id}, assessment {assessment_id}"
            )

        eligible.sort(
            key=lambda reviewer: (
                appeal_reviewer_load[reviewer["reviewer_id"]],
                int(reviewer["reviewer_id"]),
            )
        )

        selected = eligible[0]
        appeal_reviewer_load[selected["reviewer_id"]] += 1

        return selected["reviewer_id"]

    # --------------------------------------------------------
    # Main case processing
    # --------------------------------------------------------

    false_positive_counter = 0
    true_violation_counter = 0

    for case in cases:
        case_id = case["case_id"]
        submission_id = case["submission_id"]
        report_id = case["report_id"]

        assignment = assignment_lookup[case_id]
        original_reviewer_id = assignment["reviewer_id"]

        submission = submissions[submission_id]
        learner_id = submission["learner_id"]
        assessment_id = submission["assessment_id"]

        truth = ground_truth.get(report_id)

        if truth is None:
            raise ValueError(
                f"No ground-truth record for report {report_id}"
            )

        expected_outcome = truth["expected_outcome"]
        scenario_type = truth["scenario_type"]

        assignment_time = parse_date(assignment["assigned_at"])
        decision_time = assignment_time + timedelta(days=2)

        # Every case enters human review before a decision.
        change_case_status(
            case_lookup[case_id],
            "UNDER_REVIEW",
            decision_time - timedelta(minutes=5),
            "REVIEW_WORKFLOW",
        )

        # ----------------------------------------------------
        # Documented synthetic initial-review error injection
        # ----------------------------------------------------

        initial_decision_error = False

        if expected_outcome == "ACADEMIC_MISCONDUCT":
            true_violation_counter += 1
            initial_decision = "ACADEMIC_MISCONDUCT"

        elif expected_outcome == "NO_VIOLATION":
            false_positive_counter += 1

            # Every tenth eligible false-positive case is deliberately
            # assigned an incorrect initial decision for appeal testing.
            if false_positive_counter % 10 == 0:
                initial_decision = "ACADEMIC_MISCONDUCT"
                initial_decision_error = True
                initial_error_count += 1
            else:
                initial_decision = "NO_VIOLATION"

        elif expected_outcome == "INSUFFICIENT_EVIDENCE":
            initial_decision = "INSUFFICIENT_EVIDENCE"

        else:
            raise ValueError(
                f"Unsupported expected outcome: {expected_outcome}"
            )

        if initial_decision == "ACADEMIC_MISCONDUCT":
            rationale = (
                "The reviewer examined the similarity report, matched "
                "sources, and linked evidence. The documented synthetic "
                "review scenario supports an initial misconduct finding. "
                "The similarity score was treated as an investigation "
                "signal, not as proof by itself."
            )

            if initial_decision_error:
                rationale = (
                    "SIMULATED INITIAL REVIEW ERROR: ambiguous overlap "
                    "was incorrectly interpreted as unauthorized reuse. "
                    "This deliberate synthetic error is eligible for "
                    "independent appeal review."
                )

        elif initial_decision == "NO_VIOLATION":
            rationale = (
                "The reviewer examined the matched material and evidence. "
                "The overlap is consistent with legitimate quotation, "
                "shared templates, or common code patterns. The evidence "
                "does not establish academic misconduct."
            )

        else:
            rationale = (
                "The available evidence is insufficient to establish "
                "whether a violation occurred. No finding of guilt is made. "
                "Additional evidence would be required for a conclusive "
                "determination."
            )

        initial_decision_id = next_decision_id
        next_decision_id += 1

        decisions.append({
            "decision_id": initial_decision_id,
            "case_id": case_id,
            "reviewer_id": original_reviewer_id,
            "decision_type": initial_decision,
            "decision_stage": "INITIAL",
            "rationale": rationale,
            "decided_at": format_date(decision_time),
            "supersedes_decision_id": "",
        })

        decision_counts[initial_decision] += 1

        add_event(
            case_id,
            "DECISION_RECORDED",
            "Initial reviewer decision recorded with rationale.",
            f"REVIEWER_{original_reviewer_id}",
            decision_time,
            {
                "decision_id": initial_decision_id,
                "decision_type": initial_decision,
                "decision_stage": "INITIAL",
            },
        )

        add_audit(
            case_id,
            "REVIEWER",
            f"REVIEWER_{original_reviewer_id}",
            "DECISION",
            str(initial_decision_id),
            "RECORD_INITIAL_DECISION",
            decision_time,
            {"decision_type": initial_decision},
        )

        change_case_status(
            case_lookup[case_id],
            "DECIDED",
            decision_time + timedelta(minutes=1),
            "REVIEW_WORKFLOW",
        )

        # Complete the original reviewer assignment.
        assignment["assignment_status"] = "COMPLETED"
        assignment["ended_at"] = format_date(
            decision_time + timedelta(minutes=1)
        )
        assignment["end_reason"] = "INITIAL_DECISION_RECORDED"

        add_event(
            case_id,
            "REVIEWER_ASSIGNMENT_COMPLETED",
            "Initial reviewer assignment completed after decision.",
            "REVIEW_WORKFLOW",
            decision_time + timedelta(minutes=1),
            {"reviewer_id": original_reviewer_id},
        )

        add_audit(
            case_id,
            "SYSTEM",
            "REVIEW_WORKFLOW",
            "REVIEWER_ASSIGNMENT",
            case_id,
            "COMPLETE_REVIEWER_ASSIGNMENT",
            decision_time + timedelta(minutes=1),
            {"reviewer_id": original_reviewer_id},
        )

        # ----------------------------------------------------
        # Determine appeal eligibility and create appeals
        # ----------------------------------------------------

        create_appeal = False

        if initial_decision == "ACADEMIC_MISCONDUCT":
            if initial_decision_error:
                create_appeal = True
            elif expected_outcome == "ACADEMIC_MISCONDUCT":
                create_appeal = (true_violation_counter % 4 == 0)

        appeal_expected_outcome = ""

        if create_appeal:
            appeal_id = f"APL-{case_id}-01"
            appeal_time = decision_time + timedelta(days=3)
            appeal_due = appeal_time + timedelta(days=14)
            review_time = appeal_time + timedelta(days=2)

            appeal_reviewer_id = select_appeal_reviewer(
                original_reviewer_id,
                learner_id,
                assessment_id,
            )

            if initial_decision_error:
                appeal_outcome = "OVERTURNED"
                appeal_expected_outcome = "OVERTURNED"
                appeal_reason = (
                    "The learner disputes the interpretation of the "
                    "overlapping material and requests an independent "
                    "review of the source context and supporting evidence."
                )
                appeal_rationale = (
                    "Independent review found that the overlap was "
                    "consistent with legitimate material reuse rather "
                    "than unauthorized copying. The original misconduct "
                    "decision is overturned."
                )
            else:
                appeal_outcome = "UPHELD"
                appeal_expected_outcome = "UPHELD"
                appeal_reason = (
                    "The learner requests reconsideration of the original "
                    "decision and review of the evidence and rationale."
                )
                appeal_rationale = (
                    "The independent reviewer examined the original "
                    "decision and supporting evidence. The evidence "
                    "continues to support the original misconduct finding. "
                    "The appeal is upheld."
                )

            # Appeal lifecycle.
            change_case_status(
                case_lookup[case_id],
                "APPEALED",
                appeal_time,
                "LEARNER_PORTAL",
            )

            appeals.append({
                "appeal_id": appeal_id,
                "case_id": case_id,
                "original_decision_id": initial_decision_id,
                "submitted_by_learner_id": learner_id,
                "appeal_reason": appeal_reason,
                "appeal_status": "UNDER_REVIEW",
                "submitted_at": format_date(appeal_time),
                "due_at": format_date(appeal_due),
                "outcome": "",
                "resolved_at": "",
            })

            appeal_counts["SUBMITTED"] += 1

            add_event(
                case_id,
                "APPEAL_SUBMITTED",
                "Learner submitted an appeal against the initial decision.",
                f"LEARNER_{learner_id}",
                appeal_time,
                {
                    "appeal_id": appeal_id,
                    "original_decision_id": initial_decision_id,
                },
            )

            add_audit(
                case_id,
                "LEARNER",
                f"LEARNER_{learner_id}",
                "APPEAL",
                appeal_id,
                "SUBMIT_APPEAL",
                appeal_time,
                {"original_decision_id": initial_decision_id},
            )

            change_case_status(
                case_lookup[case_id],
                "APPEAL_REVIEW",
                appeal_time + timedelta(minutes=1),
                "APPEAL_WORKFLOW",
            )

            add_event(
                case_id,
                "INDEPENDENT_APPEAL_REVIEW_STARTED",
                "Independent conflict-free reviewer began appeal review.",
                f"REVIEWER_{appeal_reviewer_id}",
                review_time,
                {
                    "appeal_id": appeal_id,
                    "reviewer_id": appeal_reviewer_id,
                    "original_reviewer_id": original_reviewer_id,
                },
            )

            add_audit(
                case_id,
                "REVIEWER",
                f"REVIEWER_{appeal_reviewer_id}",
                "APPEAL_REVIEW",
                appeal_id,
                "START_INDEPENDENT_APPEAL_REVIEW",
                review_time,
                {
                    "original_reviewer_id": original_reviewer_id,
                    "independent_reviewer_id": appeal_reviewer_id,
                },
            )

            # Independent appeal review record.
            appeal_reviews.append({
                "appeal_review_id": next_appeal_review_id,
                "appeal_id": appeal_id,
                "reviewer_id": appeal_reviewer_id,
                "outcome": appeal_outcome,
                "rationale": appeal_rationale,
                "reviewed_at": format_date(review_time),
            })

            next_appeal_review_id += 1

            # Preserve the initial decision and add a reassessment record.
            reassessment_decision_id = next_decision_id
            next_decision_id += 1

            decisions.append({
                "decision_id": reassessment_decision_id,
                "case_id": case_id,
                "reviewer_id": appeal_reviewer_id,
                "decision_type": appeal_outcome,
                "decision_stage": "REASSESSMENT",
                "rationale": appeal_rationale,
                "decided_at": format_date(review_time),
                "supersedes_decision_id": initial_decision_id,
            })

            add_event(
                case_id,
                "APPEAL_REVIEW_COMPLETED",
                "Independent appeal review completed.",
                f"REVIEWER_{appeal_reviewer_id}",
                review_time,
                {
                    "appeal_id": appeal_id,
                    "outcome": appeal_outcome,
                    "appeal_review_id": next_appeal_review_id - 1,
                },
            )

            add_audit(
                case_id,
                "REVIEWER",
                f"REVIEWER_{appeal_reviewer_id}",
                "APPEAL_REVIEW",
                appeal_id,
                "COMPLETE_INDEPENDENT_APPEAL_REVIEW",
                review_time,
                {"outcome": appeal_outcome},
            )

            # Resolve appeal only after independent review exists.
            appeal_row = appeals[-1]
            appeal_row["appeal_status"] = "RESOLVED"
            appeal_row["outcome"] = appeal_outcome
            appeal_row["resolved_at"] = format_date(review_time)

            appeal_counts["RESOLVED"] += 1
            appeal_counts[appeal_outcome] += 1

            add_event(
                case_id,
                "APPEAL_RESOLVED",
                "Appeal resolved after independent review.",
                "APPEAL_WORKFLOW",
                review_time,
                {
                    "appeal_id": appeal_id,
                    "outcome": appeal_outcome,
                    "reassessment_decision_id": reassessment_decision_id,
                },
            )

            add_audit(
                case_id,
                "SYSTEM",
                "APPEAL_WORKFLOW",
                "APPEAL",
                appeal_id,
                "RESOLVE_APPEAL",
                review_time,
                {"outcome": appeal_outcome},
            )

            final_time = review_time + timedelta(minutes=2)
            closure_reason = "CLOSED_AFTER_INDEPENDENT_APPEAL_REVIEW"

        else:
            final_time = decision_time + timedelta(minutes=2)
            closure_reason = "CLOSED_AFTER_INITIAL_DECISION"

        # ----------------------------------------------------
        # Close case after all required review steps
        # ----------------------------------------------------

        current_case = case_lookup[case_id]
        current_case["closed_at"] = format_date(final_time)
        current_case["closure_reason"] = closure_reason

        change_case_status(
            current_case,
            "CLOSED",
            final_time,
            "CASE_CLOSURE_WORKFLOW",
        )

        add_event(
            case_id,
            "CASE_CLOSED",
            "Case closed after completion of required decision and review steps.",
            "CASE_CLOSURE_WORKFLOW",
            final_time,
            {"closure_reason": closure_reason},
        )

        add_audit(
            case_id,
            "SYSTEM",
            "CASE_CLOSURE_WORKFLOW",
            "CASE",
            case_id,
            "CLOSE_CASE",
            final_time,
            {"closure_reason": closure_reason},
        )

        decision_ground_truth.append({
            "case_id": case_id,
            "report_id": report_id,
            "scenario_type": scenario_type,
            "expected_outcome": expected_outcome,
            "initial_decision_error": str(initial_decision_error).lower(),
            "appeal_expected_outcome": appeal_expected_outcome,
        })

    # --------------------------------------------------------
    # Persist generated records
    # --------------------------------------------------------

    write_csv("decisions.csv", decisions, DECISION_FIELDS)
    write_csv("appeals.csv", appeals, APPEAL_FIELDS)
    write_csv(
        "appeal_reviews.csv",
        appeal_reviews,
        APPEAL_REVIEW_FIELDS,
    )
    write_csv(
        "decision_ground_truth.csv",
        decision_ground_truth,
        DECISION_GROUND_TRUTH_FIELDS,
    )

    write_csv("cases.csv", updated_cases)
    write_csv("reviewer_assignments.csv", updated_assignments)
    write_csv("case_events.csv", events)
    write_csv("audit_logs.csv", audits)

    summary = {
        "generator_version": "1.0.0",
        "seed": SEED,
        "cases_processed": len(cases),
        "initial_decisions": len(cases),
        "reassessment_decisions": len(appeals),
        "total_decision_records": len(decisions),
        "appeals_created": len(appeals),
        "independent_appeal_reviews": len(appeal_reviews),
        "initial_decision_errors_injected": initial_error_count,
        "decision_counts": dict(decision_counts),
        "appeal_counts": dict(appeal_counts),
        "closed_cases": sum(
            1 for row in updated_cases
            if row["case_status"] == "CLOSED"
        ),
        "completed_reviewer_assignments": sum(
            1 for row in updated_assignments
            if row["assignment_status"] == "COMPLETED"
        ),
        "timeline_event_count": len(events),
        "audit_record_count": len(audits),
        "appeal_reviewer_load": dict(appeal_reviewer_load),
        "ground_truth_separate_from_operational_records": True,
    }

    with (OUTPUT_DIR / "decision_appeal_summary.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(summary, file, indent=4)

    print("\nPHASE 3 GENERATION COMPLETED")
    print("-" * 68)
    print(json.dumps(summary, indent=4))
    print("\nGenerated files:")
    for filename in [
        "decisions.csv",
        "appeals.csv",
        "appeal_reviews.csv",
        "decision_ground_truth.csv",
        "decision_appeal_summary.json",
    ]:
        print(f"  - {filename}")

    print("\nUpdated files:")
    for filename in [
        "cases.csv",
        "reviewer_assignments.csv",
        "case_events.csv",
        "audit_logs.csv",
    ]:
        print(f"  - {filename}")

    print(f"\nPhase 2 snapshot saved at: {SNAPSHOT_DIR}")


if __name__ == "__main__":
    main()
