
import csv
import json
import random
import hashlib

from pathlib import Path
from datetime import datetime, timedelta

from data_engineering.config import (
    SEED,
    TOTAL_LEARNERS,
    TOTAL_ASSESSMENTS,
    TOTAL_REVIEWERS,
    TOTAL_SUBMISSIONS,
    TOTAL_FLAGS,
    TOTAL_CASES,
    GENERATOR_VERSION,
    OUTPUT_DIRECTORY
)


rng = random.Random(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_ROOT / OUTPUT_DIRECTORY
OUTPUT.mkdir(parents=True, exist_ok=True)

BASE_DATE = datetime(2026, 1, 1, 9, 0, 0)

DEPARTMENTS = [
    "Computer Science",
    "Information Technology",
    "Electronics",
    "Mechanical",
    "Civil",
    "Electrical"
]

FIRST_NAMES = [
    "Aarav", "Arjun", "Rahul", "Kiran", "Vijay",
    "Priya", "Ananya", "Sneha", "Divya", "Meera",
    "Rohan", "Sai", "Varun", "Neha", "Sanjay"
]

LAST_NAMES = [
    "Sharma", "Reddy", "Kumar", "Rao", "Patel",
    "Gupta", "Verma", "Singh", "Nair", "Das"
]

ASSESSMENT_TYPES = [
    "ASSIGNMENT", "EXAM", "PROJECT", "QUIZ"
]

SCENARIOS = [
    "UNAUTHORIZED_OVERLAP",
    "LEGITIMATE_QUOTATION",
    "SHARED_TEMPLATE",
    "COMMON_CODE_PATTERN",
    "INSUFFICIENT_EVIDENCE"
]

SCENARIO_WEIGHTS = [35, 20, 20, 15, 10]


def write_csv(filename, records):
    if not records:
        raise ValueError(f"No records generated for {filename}")

    with open(OUTPUT / filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(records[0].keys())
        )
        writer.writeheader()
        writer.writerows(records)


def write_json(filename, records):
    with open(OUTPUT / filename, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)


def stable_hash(value):
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def format_datetime(value):
    return value.strftime("%Y-%m-%d %H:%M:%S")


def generate_learners():
    records = []

    for i in range(1, TOTAL_LEARNERS + 1):
        name = (
            f"{rng.choice(FIRST_NAMES)} "
            f"{rng.choice(LAST_NAMES)}"
        )

        records.append({
            "learner_id": i,
            "learner_code": f"LRN-2026-{i:06d}",
            "full_name": name,
            "email": f"learner{i:05d}@example.edu",
            "department": rng.choice(DEPARTMENTS)
        })

    write_csv("learners.csv", records)
    return records


def generate_assessments():
    records = []

    for i in range(1, TOTAL_ASSESSMENTS + 1):
        due_date = BASE_DATE + timedelta(days=150 + i)

        records.append({
            "assessment_id": i,
            "assessment_code": f"ASM-2026-{i:04d}",
            "title": f"Academic Assessment {i:03d}",
            "assessment_type": rng.choice(ASSESSMENT_TYPES),
            "description": f"Synthetic assessment {i}",
            "due_date": format_datetime(due_date)
        })

    write_csv("assessments.csv", records)
    return records


def generate_reviewers():
    records = []

    for i in range(1, TOTAL_REVIEWERS + 1):
        records.append({
            "reviewer_id": i,
            "reviewer_code": f"REV-2026-{i:04d}",
            "full_name": f"Reviewer {i:03d}",
            "email": f"reviewer{i:03d}@example.edu",
            "role": "REVIEWER",
            "department": DEPARTMENTS[
                (i - 1) % len(DEPARTMENTS)
            ],
            "max_active_cases": 10,
            "is_active": 1
        })

    write_csv("reviewers.csv", records)
    return records


def generate_rules():
    records = [
        {
            "rule_id": "RULE_LOW",
            "rule_name": "Low Similarity",
            "description": "Low similarity monitoring",
            "minimum_score": 0,
            "maximum_score": 19.99,
            "action": "NO_FLAG",
            "rule_version": 1,
            "effective_from": "2026-01-01 00:00:00",
            "effective_to": "",
            "is_active": 1
        },
        {
            "rule_id": "RULE_MODERATE",
            "rule_name": "Moderate Similarity",
            "description": "Similarity monitoring",
            "minimum_score": 20,
            "maximum_score": 49.99,
            "action": "MONITOR",
            "rule_version": 1,
            "effective_from": "2026-01-01 00:00:00",
            "effective_to": "",
            "is_active": 1
        },
        {
            "rule_id": "RULE_HIGH",
            "rule_name": "High Similarity",
            "description": "Manual review required",
            "minimum_score": 50,
            "maximum_score": 100,
            "action": "REVIEW",
            "rule_version": 1,
            "effective_from": "2026-01-01 00:00:00",
            "effective_to": "",
            "is_active": 1
        }
    ]

    write_csv("integrity_rules.csv", records)
    return records


def generate_submissions(learners, assessments):
    records = []

    combinations = [
        (learner, assessment)
        for learner in learners
        for assessment in assessments
    ]

    selected = rng.sample(
        combinations,
        TOTAL_SUBMISSIONS
    )

    for i, (learner, assessment) in enumerate(
        selected, start=1
    ):
        submission_id = f"SUB-2026-{i:06d}"

        submitted_at = BASE_DATE + timedelta(
            days=rng.randint(0, 120),
            minutes=rng.randint(0, 1439)
        )

        content_reference = (
            f"synthetic://submissions/{submission_id}"
        )

        synthetic_content = (
            f"Synthetic assessment content for {submission_id}"
        )

        records.append({
            "submission_id": submission_id,
            "learner_id": learner["learner_id"],
            "assessment_id": assessment["assessment_id"],
            "submitted_at": format_datetime(submitted_at),
            "content_reference": content_reference,
            "content_hash": stable_hash(synthetic_content),
            "attempt_number": 1,
            "status": "ANALYZED"
        })

    write_csv("submissions.csv", records)
    return records


def allocate_match_percentages(total_score, count):
    total_cents = int(round(total_score * 100))

    weights = [rng.random() for _ in range(count)]
    weight_total = sum(weights)

    raw_values = [
        total_cents * weight / weight_total
        for weight in weights
    ]

    values = [int(value) for value in raw_values]
    remainder = total_cents - sum(values)

    fractions = sorted(
        range(count),
        key=lambda i: raw_values[i] - values[i],
        reverse=True
    )

    for index in fractions[:remainder]:
        values[index] += 1

    return [
        round(value / 100, 2)
        for value in values
    ]


def get_scenario_score(scenario):
    score_ranges = {
        "UNAUTHORIZED_OVERLAP": (60, 98),
        "LEGITIMATE_QUOTATION": (50, 85),
        "SHARED_TEMPLATE": (50, 80),
        "COMMON_CODE_PATTERN": (50, 70),
        "INSUFFICIENT_EVIDENCE": (50, 75)
    }

    minimum, maximum = score_ranges[scenario]

    return round(
        rng.uniform(minimum, maximum),
        2
    )


def get_scenario_match_type(scenario):
    match_types = {
        "UNAUTHORIZED_OVERLAP": [
            "CODE_MATCH", "TEXT_MATCH"
        ],
        "LEGITIMATE_QUOTATION": [
            "TEXT_MATCH"
        ],
        "SHARED_TEMPLATE": [
            "CODE_MATCH"
        ],
        "COMMON_CODE_PATTERN": [
            "CODE_MATCH"
        ],
        "INSUFFICIENT_EVIDENCE": [
            "CODE_MATCH", "TEXT_MATCH"
        ]
    }

    return rng.choice(match_types[scenario])


def get_report_category(score):
    if score >= 75:
        return "CRITICAL"

    return "HIGH"


def get_case_priority(score):
    if score >= 90:
        return "CRITICAL"
    if score >= 75:
        return "HIGH"
    if score >= 60:
        return "MEDIUM"

    return "LOW"


def get_ground_truth(scenario):
    outcomes = {
        "UNAUTHORIZED_OVERLAP": {
            "true_violation": True,
            "synthetic_label": "TRUE_VIOLATION",
            "expected_outcome": "ACADEMIC_MISCONDUCT"
        },
        "LEGITIMATE_QUOTATION": {
            "true_violation": False,
            "synthetic_label": "FALSE_POSITIVE",
            "expected_outcome": "NO_VIOLATION"
        },
        "SHARED_TEMPLATE": {
            "true_violation": False,
            "synthetic_label": "FALSE_POSITIVE",
            "expected_outcome": "NO_VIOLATION"
        },
        "COMMON_CODE_PATTERN": {
            "true_violation": False,
            "synthetic_label": "FALSE_POSITIVE",
            "expected_outcome": "NO_VIOLATION"
        },
        "INSUFFICIENT_EVIDENCE": {
            "true_violation": None,
            "synthetic_label": "INCONCLUSIVE",
            "expected_outcome": "INSUFFICIENT_EVIDENCE"
        }
    }

    return outcomes[scenario].copy()


def generate_similarity_reports(submissions):
    selected = rng.sample(
        submissions,
        TOTAL_FLAGS
    )

    reports = []
    report_matches = []
    ground_truth = []

    match_id = 1

    for submission in selected:
        scenario = rng.choices(
            SCENARIOS,
            weights=SCENARIO_WEIGHTS,
            k=1
        )[0]

        score = get_scenario_score(scenario)

        report_id = (
            f"SIM-{submission['submission_id']}-01"
        )

        submitted_at = datetime.strptime(
            submission["submitted_at"],
            "%Y-%m-%d %H:%M:%S"
        )

        generated_at = submitted_at + timedelta(
            hours=rng.randint(1, 72)
        )

        matched_source_count = rng.randint(1, 5)

        percentages = allocate_match_percentages(
            score,
            matched_source_count
        )

        for sequence, percentage in enumerate(
            percentages,
            start=1
        ):
            report_matches.append({
                "match_id": match_id,
                "report_id": report_id,
                "match_sequence": sequence,
                "source_reference": (
                    f"SYNTH-SRC-2026-{match_id:06d}"
                ),
                "match_percentage": percentage,
                "match_type": get_scenario_match_type(
                    scenario
                ),
                "description": (
                    f"Synthetic {scenario.lower()} match"
                )
            })

            match_id += 1

        reports.append({
            "report_id": report_id,
            "submission_id": submission["submission_id"],
            "evaluated_rule_id": "RULE_HIGH",
            "similarity_score": score,
            "matched_source_count": matched_source_count,
            "report_category": get_report_category(score),
            "review_action": "REVIEW",
            "generated_at": format_datetime(generated_at),
            "generator_version": GENERATOR_VERSION
        })

        truth = get_ground_truth(scenario)

        ground_truth.append({
            "report_id": report_id,
            "submission_id": submission["submission_id"],
            "scenario_type": scenario,
            **truth
        })

    write_csv("similarity_reports.csv", reports)
    write_csv("report_matches.csv", report_matches)
    write_json("ground_truth.json", ground_truth)

    return reports, report_matches, ground_truth


def generate_cases(reports):
    selected = rng.sample(
        reports,
        TOTAL_CASES
    )

    records = []

    for i, report in enumerate(selected, start=1):
        created_at = datetime.strptime(
            report["generated_at"],
            "%Y-%m-%d %H:%M:%S"
        )

        due_at = created_at + timedelta(days=14)

        records.append({
            "case_id": f"INT-2026-{i:06d}",
            "submission_id": report["submission_id"],
            "report_id": report["report_id"],
            "rule_id": report["evaluated_rule_id"],
            "case_status": "OPEN",
            "priority": get_case_priority(
                float(report["similarity_score"])
            ),
            "created_at": format_datetime(created_at),
            "due_at": format_datetime(due_at),
            "closed_at": "",
            "closure_reason": ""
        })

    write_csv("cases.csv", records)
    return records


def write_dataset_summary(data):
    summary = {
        "seed": SEED,
        "generator_version": GENERATOR_VERSION,
        "counts": {
            "learners": len(data["learners"]),
            "assessments": len(data["assessments"]),
            "reviewers": len(data["reviewers"]),
            "submissions": len(data["submissions"]),
            "similarity_reports": len(data["reports"]),
            "report_matches": len(data["matches"]),
            "cases": len(data["cases"]),
            "ground_truth": len(data["ground_truth"])
        }
    }

    write_json("dataset_summary.json", summary)


def main():
    print("Starting redesigned dataset generation...")
    print("Random seed:", SEED)

    learners = generate_learners()
    assessments = generate_assessments()
    reviewers = generate_reviewers()

    generate_rules()

    submissions = generate_submissions(
        learners,
        assessments
    )

    reports, matches, ground_truth = (
        generate_similarity_reports(submissions)
    )

    cases = generate_cases(reports)

    data = {
        "learners": learners,
        "assessments": assessments,
        "reviewers": reviewers,
        "submissions": submissions,
        "reports": reports,
        "matches": matches,
        "cases": cases,
        "ground_truth": ground_truth
    }

    write_dataset_summary(data)

    print("\nREDESIGNED DATASET GENERATED")
    for name, records in data.items():
        print(f"{name}: {len(records)}")

    print("\nOutput directory:", OUTPUT.resolve())


if __name__ == "__main__":
    main()
