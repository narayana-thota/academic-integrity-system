
import csv
import json
import hashlib
import random

from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

from data_engineering.config import SEED


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

rng = random.Random(SEED + 1)

OUTPUT = Path(__file__).resolve().parent / "output"

SYSTEM_ACTOR = "DATA_GENERATOR_V1"
ASSIGNMENT_ACTOR = "ASSIGNMENT_SERVICE"


# --------------------------------------------------
# FILE HELPERS
# --------------------------------------------------

def read_csv(filename):
    with open(
        OUTPUT / filename,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def write_csv(filename, records):
    if not records:
        raise ValueError(
            f"Cannot write empty dataset: {filename}"
        )

    with open(
        OUTPUT / filename,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(records[0].keys())
        )
        writer.writeheader()
        writer.writerows(records)


def write_json(filename, data):
    with open(
        OUTPUT / filename,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(data, file, indent=2)


def parse_date(value):
    return datetime.strptime(
        value,
        "%Y-%m-%d %H:%M:%S"
    )


def format_date(value):
    return value.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def stable_hash(value):
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


# --------------------------------------------------
# EVENT AND AUDIT HELPERS
# --------------------------------------------------

def add_event(
    events,
    case_id,
    event_type,
    description,
    actor,
    occurred_at,
    event_data
):
    events.append({
        "case_id": case_id,
        "event_type": event_type,
        "event_description": description,
        "actor_reference": actor,
        "event_data": json.dumps(
            event_data,
            sort_keys=True
        ),
        "occurred_at": format_date(occurred_at)
    })


def add_audit(
    logs,
    case_id,
    actor_type,
    actor_reference,
    entity_type,
    entity_reference,
    action,
    created_at,
    event_data
):
    logs.append({
        "case_id": case_id,
        "actor_type": actor_type,
        "actor_reference": actor_reference,
        "entity_type": entity_type,
        "entity_reference": entity_reference,
        "action": action,
        "event_data": json.dumps(
            event_data,
            sort_keys=True
        ),
        "created_at": format_date(created_at)
    })


# --------------------------------------------------
# EVIDENCE GENERATION
# --------------------------------------------------

def generate_evidence(cases, reports, matches):
    print("\nGenerating evidence records...")

    reports_by_id = {
        report["report_id"]: report
        for report in reports
    }

    matches_by_report = defaultdict(list)

    for match in matches:
        matches_by_report[
            match["report_id"]
        ].append(match)

    evidence_items = []
    case_evidence = []

    evidence_count_by_case = {}

    for case in cases:

        case_id = case["case_id"]
        report_id = case["report_id"]

        report = reports_by_id[report_id]

        report_matches = sorted(
            matches_by_report[report_id],
            key=lambda item: int(item["match_sequence"])
        )

        created_at = parse_date(
            case["created_at"]
        )

        for sequence, match in enumerate(
            report_matches,
            start=1
        ):

            evidence_id = (
                f"EVD-{case_id}-{sequence:03d}"
            )

            evidence_type = match["match_type"]

            description = (
                f"Matched-source evidence for "
                f"{report_id}. "
                f"{match['description']}. "
                f"Matched percentage: "
                f"{match['match_percentage']}%."
            )

            evidence_hash = stable_hash(
                match["source_reference"]
                + "|"
                + description
            )

            evidence_items.append({
                "evidence_id": evidence_id,
                "evidence_type": evidence_type,
                "evidence_reference": match[
                    "source_reference"
                ],
                "description": description,
                "content_hash": evidence_hash,
                "version": 1,
                "added_by": "SIMILARITY_ENGINE",
                "created_at": format_date(
                    parse_date(report["generated_at"])
                )
            })

            linked_at = created_at + timedelta(
                minutes=5 + sequence
            )

            case_evidence.append({
                "case_id": case_id,
                "evidence_id": evidence_id,
                "linked_at": format_date(linked_at)
            })

        evidence_count_by_case[case_id] = len(
            report_matches
        )

    write_csv(
        "evidence_items.csv",
        evidence_items
    )

    write_csv(
        "case_evidence.csv",
        case_evidence
    )

    print("Evidence items:", len(evidence_items))
    print("Case-evidence links:", len(case_evidence))

    return (
        evidence_items,
        case_evidence,
        evidence_count_by_case
    )


# --------------------------------------------------
# REVIEWER CONFLICT GENERATION
# --------------------------------------------------

def generate_conflicts(
    cases,
    reviewers,
    submissions_by_id
):
    print("\nGenerating reviewer conflicts...")

    conflicts = []
    blocked_preferred_reviewers = {}

    conflict_counter = 0

    for index, case in enumerate(
        cases,
        start=1
    ):

        # Create a deliberate conflict for every
        # tenth case in the valid baseline dataset.
        if index % 10 != 0:
            continue

        conflict_counter += 1

        # Spread conflicts across all reviewers.
        reviewer_index = (
            conflict_counter - 1
        ) % len(reviewers)

        reviewer = reviewers[reviewer_index]

        submission = submissions_by_id[
            case["submission_id"]
        ]

        learner_id = ""
        assessment_id = ""

        # Alternate between learner-level and
        # assessment-level conflicts.
        if conflict_counter % 2 == 1:
            learner_id = submission["learner_id"]
            conflict_type = "LEARNER_RELATIONSHIP"
        else:
            assessment_id = submission["assessment_id"]
            conflict_type = "ASSESSMENT_RELATIONSHIP"

        conflict = {
            "reviewer_id": reviewer["reviewer_id"],
            "learner_id": learner_id,
            "assessment_id": assessment_id,
            "conflict_type": conflict_type,
            "description": (
                "Synthetic conflict of interest. "
                "Reviewer must not be assigned to "
                "the affected learner or assessment."
            ),
            "is_active": 1,
            "created_at": case["created_at"]
        }

        conflicts.append(conflict)

        blocked_preferred_reviewers[
            case["case_id"]
        ] = reviewer["reviewer_id"]

    write_csv(
        "reviewer_conflicts.csv",
        conflicts
    )

    print("Reviewer conflicts:", len(conflicts))

    return conflicts, blocked_preferred_reviewers


# --------------------------------------------------
# CONFLICT CHECKING
# --------------------------------------------------

def find_conflict(
    reviewer_id,
    learner_id,
    assessment_id,
    conflicts_by_reviewer
):
    reviewer_conflicts = conflicts_by_reviewer.get(
        reviewer_id,
        []
    )

    for conflict in reviewer_conflicts:

        if str(conflict["is_active"]) not in (
            "1", "True", "true"
        ):
            continue

        learner_conflict = (
            conflict["learner_id"] != ""
            and conflict["learner_id"] == str(learner_id)
        )

        assessment_conflict = (
            conflict["assessment_id"] != ""
            and conflict["assessment_id"] == str(assessment_id)
        )

        if learner_conflict or assessment_conflict:
            return conflict

    return None


# --------------------------------------------------
# REVIEWER ASSIGNMENT
# --------------------------------------------------

def generate_assignments(
    cases,
    reviewers,
    submissions_by_id,
    conflicts,
    blocked_preferred_reviewers
):
    print("\nGenerating reviewer assignments...")

    conflicts_by_reviewer = defaultdict(list)

    for conflict in conflicts:
        conflicts_by_reviewer[
            conflict["reviewer_id"]
        ].append(conflict)

    active_load = {
        reviewer["reviewer_id"]: 0
        for reviewer in reviewers
    }

    reviewer_capacity = {
        reviewer["reviewer_id"]: int(
            reviewer["max_active_cases"]
        )
        for reviewer in reviewers
    }

    assignments = []
    blocked_attempts = []

    for index, case in enumerate(
        cases,
        start=1
    ):

        submission = submissions_by_id[
            case["submission_id"]
        ]

        learner_id = submission["learner_id"]
        assessment_id = submission["assessment_id"]

        case_id = case["case_id"]

        # Preferred reviewer for normal assignment.
        preferred_reviewer_id = (
            blocked_preferred_reviewers.get(case_id)
        )

        if preferred_reviewer_id is None:
            preferred_reviewer_id = reviewers[
                (index - 1) % len(reviewers)
            ]["reviewer_id"]

        preferred_conflict = find_conflict(
            preferred_reviewer_id,
            learner_id,
            assessment_id,
            conflicts_by_reviewer
        )

        selected_reviewer = None

        # First attempt the preferred reviewer.
        if preferred_conflict is not None:

           blocked_attempts.append({
               "case_id": case_id,
               "reviewer_id": preferred_reviewer_id,
               "conflict_type": preferred_conflict["conflict_type"],"reason": "CONFLICT_OF_INTEREST"
            })

        elif active_load[preferred_reviewer_id] < (
            reviewer_capacity[preferred_reviewer_id]
        ):

            selected_reviewer = preferred_reviewer_id

        # If the preferred reviewer is unavailable,
        # search other eligible reviewers.
        if selected_reviewer is None:

            reviewer_order = sorted(
                reviewers,
                key=lambda reviewer: (
                    active_load[reviewer["reviewer_id"]],
                    (
                        int(reviewer["reviewer_id"])
                        - int(preferred_reviewer_id)
                    ) % len(reviewers)
                )
            )

            for reviewer in reviewer_order:

                reviewer_id = reviewer["reviewer_id"]

                if active_load[reviewer_id] >= (
                    reviewer_capacity[reviewer_id]
                ):
                    continue

                conflict = find_conflict(
                    reviewer_id,
                    learner_id,
                    assessment_id,
                    conflicts_by_reviewer
                )

                if conflict is not None:
                    continue

                selected_reviewer = reviewer_id
                break

        if selected_reviewer is None:
            raise RuntimeError(
                f"No eligible reviewer found for {case_id}"
            )

        # Increase the active workload.
        active_load[selected_reviewer] += 1

        created_at = parse_date(
            case["created_at"]
        )

        assigned_at = created_at + timedelta(
            hours=1
        )

        assignments.append({
            "case_id": case_id,
            "reviewer_id": selected_reviewer,
            "assignment_status": "ACTIVE",
            "assigned_at": format_date(assigned_at),
            "ended_at": "",
            "assigned_by": ASSIGNMENT_ACTOR,
            "end_reason": ""
        })

        # Update case lifecycle state.
        case["case_status"] = "ASSIGNED"

    write_csv(
        "reviewer_assignments.csv",
        assignments
    )

    print("Successful assignments:", len(assignments))
    print("Blocked conflict attempts:", len(blocked_attempts))

    return (
        assignments,
        blocked_attempts,
        active_load
    )


# --------------------------------------------------
# CASE EVENTS AND AUDIT LOGS
# --------------------------------------------------

def generate_history(
    cases,
    evidence_items,
    case_evidence,
    assignments,
    blocked_attempts
):
    print("\nGenerating case timeline and audit history...")

    events = []
    audit_logs = []

    evidence_by_id = {
        item["evidence_id"]: item
        for item in evidence_items
    }

    evidence_by_case = defaultdict(list)

    for link in case_evidence:
        evidence_by_case[
            link["case_id"]
        ].append(link)

    assignment_by_case = {
        item["case_id"]: item
        for item in assignments
    }

    blocked_by_case = defaultdict(list)

    for item in blocked_attempts:
        blocked_by_case[
            item["case_id"]
        ].append(item)

    for case in cases:

        case_id = case["case_id"]

        created_at = parse_date(
            case["created_at"]
        )

        add_event(
            events,
            case_id,
            "CASE_CREATED",
            "Investigation case created from a similarity report.",
            SYSTEM_ACTOR,
            created_at,
            {
                "report_id": case["report_id"],
                "submission_id": case["submission_id"],
                "priority": case["priority"]
            }
        )

        add_audit(
            audit_logs,
            case_id,
            "SYSTEM",
            SYSTEM_ACTOR,
            "CASE",
            case_id,
            "CREATE",
            created_at,
            {
                "case_status": "OPEN"
            }
        )

        # Evidence-linking history.
        for link in evidence_by_case[case_id]:

            evidence_id = link["evidence_id"]

            evidence = evidence_by_id[evidence_id]

            linked_at = parse_date(
                link["linked_at"]
            )

            add_event(
                events,
                case_id,
                "EVIDENCE_LINKED",
                "Evidence item linked to investigation case.",
                SYSTEM_ACTOR,
                linked_at,
                {
                    "evidence_id": evidence_id,
                    "evidence_type": evidence["evidence_type"],
                    "version": evidence["version"]
                }
            )

            add_audit(
                audit_logs,
                case_id,
                "SYSTEM",
                SYSTEM_ACTOR,
                "EVIDENCE_ITEM",
                evidence_id,
                "LINK_TO_CASE",
                linked_at,
                {
                    "case_id": case_id
                }
            )

        # Record rejected assignment attempts.
        for attempt in blocked_by_case[case_id]:

            blocked_at = created_at + timedelta(
                minutes=30
            )

            add_event(
                events,
                case_id,
                "REVIEWER_ASSIGNMENT_BLOCKED_CONFLICT",
                "Reviewer assignment blocked due to conflict of interest.",
                ASSIGNMENT_ACTOR,
                blocked_at,
                {
                    "reviewer_id": attempt["reviewer_id"],
                    "conflict_type": attempt["conflict_type"],
                    "reason": attempt["reason"]
                }
            )

            add_audit(
                audit_logs,
                case_id,
                "SYSTEM",
                ASSIGNMENT_ACTOR,
                "REVIEWER_ASSIGNMENT",
                case_id,
                "BLOCKED_CONFLICT_ASSIGNMENT",
                blocked_at,
                attempt
            )

        # Record successful assignment.
        assignment = assignment_by_case[case_id]

        assigned_at = parse_date(
            assignment["assigned_at"]
        )

        add_event(
            events,
            case_id,
            "REVIEWER_ASSIGNED",
            "Eligible reviewer assigned to case.",
            ASSIGNMENT_ACTOR,
            assigned_at,
            {
                "reviewer_id": assignment["reviewer_id"],
                "assignment_status": "ACTIVE"
            }
        )
        add_event(
            events,
            case_id,
            "CASE_STATUS_CHANGED",
            "Case status changed from OPEN to ASSIGNED.",
            ASSIGNMENT_ACTOR,
            assigned_at,
            {
                "previous_status": "OPEN",
                "new_status": "ASSIGNED"
            }
        )

        add_audit(
            audit_logs,
            case_id,
            "SYSTEM",
            ASSIGNMENT_ACTOR,
            "CASE",
            case_id,
            "STATUS_CHANGE",
            assigned_at,
            {
                "previous_status": "OPEN",
                "new_status": "ASSIGNED"
            }
        )

        add_audit(
            audit_logs,
            case_id,
            "SYSTEM",
            ASSIGNMENT_ACTOR,
            "REVIEWER_ASSIGNMENT",
            case_id,
            "ASSIGN_REVIEWER",
            assigned_at,
            {
                "reviewer_id": assignment["reviewer_id"]
            }
        )

    write_csv(
        "case_events.csv",
        events
    )

    write_csv(
        "audit_logs.csv",
        audit_logs
    )

    print("Case events:", len(events))
    print("Audit records:", len(audit_logs))

    return events, audit_logs


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
    print("=" * 60)
    print("WORKFLOW DATA GENERATION")
    print("Seed:", SEED + 1)
    print("=" * 60)

    learners = read_csv("learners.csv")
    submissions = read_csv("submissions.csv")
    reports = read_csv("similarity_reports.csv")
    matches = read_csv("report_matches.csv")
    cases = read_csv("cases.csv")
    reviewers = read_csv("reviewers.csv")

    submissions_by_id = {
        item["submission_id"]: item
        for item in submissions
    }

    # 1. Generate evidence.
    evidence_items, case_evidence, _ = (
        generate_evidence(
            cases,
            reports,
            matches
        )
    )

    # 2. Generate reviewer conflicts.
    conflicts, blocked_preferred_reviewers = (
        generate_conflicts(
            cases,
            reviewers,
            submissions_by_id
        )
    )

    # 3. Generate valid assignments.
    assignments, blocked_attempts, active_load = (
        generate_assignments(
            cases,
            reviewers,
            submissions_by_id,
            conflicts,
            blocked_preferred_reviewers
        )
    )

    # 4. Generate timeline and audit history.
    events, audit_logs = generate_history(
        cases,
        evidence_items,
        case_evidence,
        assignments,
        blocked_attempts
    )

    # Save updated case lifecycle states.
    write_csv("cases.csv", cases)

    summary = {
        "seed": SEED + 1,
        "evidence_items": len(evidence_items),
        "case_evidence_links": len(case_evidence),
        "reviewer_conflicts": len(conflicts),
        "reviewer_assignments": len(assignments),
        "blocked_assignment_attempts": len(blocked_attempts),
        "case_events": len(events),
        "audit_logs": len(audit_logs),
        "assigned_cases": sum(
            1 for case in cases
            if case["case_status"] == "ASSIGNED"
        ),
        "maximum_reviewer_load": max(
            active_load.values()
        )
    }

    write_json(
        "workflow_summary.json",
        summary
    )

    print("\n" + "=" * 60)
    print("WORKFLOW GENERATION COMPLETE")
    print("=" * 60)

    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
