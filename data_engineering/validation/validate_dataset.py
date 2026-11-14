
import csv
import json
import re
import sys

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from data_engineering.config import (
    TOTAL_LEARNERS,
    TOTAL_ASSESSMENTS,
    TOTAL_REVIEWERS,
    TOTAL_SUBMISSIONS,
    TOTAL_FLAGS,
    TOTAL_CASES
)


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data_engineering" / "output"

errors = []
checks_passed = 0


def check(condition, message):
    global checks_passed

    if condition:
        checks_passed += 1
        print(f"[PASS] {message}")
    else:
        errors.append(message)
        print(f"[FAIL] {message}")


def read_csv(filename):
    path = OUTPUT / filename

    with open(path, "r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def read_json(filename):
    with open(OUTPUT / filename, "r", encoding="utf-8") as file:
        return json.load(file)


def unique(records, field):
    values = [record[field] for record in records]
    return len(values) == len(set(values))


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def main():
    print("=" * 65)
    print("ACADEMIC INTEGRITY DATASET VALIDATION")
    print("=" * 65)

    learners = read_csv("learners.csv")
    assessments = read_csv("assessments.csv")
    reviewers = read_csv("reviewers.csv")
    rules = read_csv("integrity_rules.csv")
    submissions = read_csv("submissions.csv")
    reports = read_csv("similarity_reports.csv")
    matches = read_csv("report_matches.csv")
    cases = read_csv("cases.csv")
    ground_truth = read_json("ground_truth.json")

    # -------------------------------------------------
    # 1. RECORD COUNTS
    # -------------------------------------------------

    print("\n1. RECORD COUNT VALIDATION")

    expected_counts = [
        (learners, TOTAL_LEARNERS, "Learners"),
        (assessments, TOTAL_ASSESSMENTS, "Assessments"),
        (reviewers, TOTAL_REVIEWERS, "Reviewers"),
        (submissions, TOTAL_SUBMISSIONS, "Submissions"),
        (reports, TOTAL_FLAGS, "Similarity reports"),
        (cases, TOTAL_CASES, "Cases"),
        (ground_truth, TOTAL_FLAGS, "Ground truth")
    ]

    for records, expected, name in expected_counts:
        check(
            len(records) == expected,
            f"{name}: expected {expected}, found {len(records)}"
        )

    check(
        len(matches) > 0,
        f"Report matches generated: {len(matches)}"
    )

    # -------------------------------------------------
    # 2. PRIMARY KEY VALIDATION
    # -------------------------------------------------

    print("\n2. PRIMARY KEY VALIDATION")

    primary_keys = [
        (learners, "learner_id", "Learner"),
        (assessments, "assessment_id", "Assessment"),
        (reviewers, "reviewer_id", "Reviewer"),
        (rules, "rule_id", "Integrity rule"),
        (submissions, "submission_id", "Submission"),
        (reports, "report_id", "Similarity report"),
        (matches, "match_id", "Report match"),
        (cases, "case_id", "Case")
    ]

    for records, field, name in primary_keys:
        check(
            unique(records, field),
            f"{name} primary keys are unique"
        )

    # -------------------------------------------------
    # 3. LOOKUP SETS
    # -------------------------------------------------

    learner_ids = {
        record["learner_id"] for record in learners
    }

    assessment_ids = {
        record["assessment_id"] for record in assessments
    }

    submission_ids = {
        record["submission_id"] for record in submissions
    }

    report_ids = {
        record["report_id"] for record in reports
    }

    rule_ids = {
        record["rule_id"] for record in rules
    }

    case_ids = {
        record["case_id"] for record in cases
    }

    # -------------------------------------------------
    # 4. FOREIGN KEY VALIDATION
    # -------------------------------------------------

    print("\n3. FOREIGN KEY VALIDATION")

    check(
        all(s["learner_id"] in learner_ids for s in submissions),
        "Every submission references an existing learner"
    )

    check(
        all(s["assessment_id"] in assessment_ids for s in submissions),
        "Every submission references an existing assessment"
    )

    check(
        all(r["submission_id"] in submission_ids for r in reports),
        "Every report references an existing submission"
    )

    check(
        all(r["evaluated_rule_id"] in rule_ids for r in reports),
        "Every report references an existing integrity rule"
    )

    check(
        all(m["report_id"] in report_ids for m in matches),
        "Every report match references an existing report"
    )

    check(
        all(c["submission_id"] in submission_ids for c in cases),
        "Every case references an existing submission"
    )

    check(
        all(c["report_id"] in report_ids for c in cases),
        "Every case references an existing report"
    )

    check(
        all(c["rule_id"] in rule_ids for c in cases),
        "Every case references an existing integrity rule"
    )

    # -------------------------------------------------
    # 5. UNIQUE SUBMISSION COMBINATIONS
    # -------------------------------------------------

    print("\n4. DUPLICATE SUBMISSION VALIDATION")

    combinations = [
        (s["learner_id"], s["assessment_id"], s["attempt_number"])
        for s in submissions
    ]

    check(
        len(combinations) == len(set(combinations)),
        "No duplicate learner-assessment-attempt combinations"
    )

    # -------------------------------------------------
    # 6. ID FORMAT VALIDATION
    # -------------------------------------------------

    print("\n5. ID FORMAT VALIDATION")

    check(
        all(re.fullmatch(r"LRN-2026-\d{6}", x["learner_code"])
            for x in learners),
        "Learner codes follow LRN-2026-XXXXXX"
    )

    check(
        all(re.fullmatch(r"SUB-2026-\d{6}", x["submission_id"])
            for x in submissions),
        "Submission IDs follow SUB-2026-XXXXXX"
    )

    check(
        all(
            r["report_id"] == f"SIM-{r['submission_id']}-01"
            for r in reports
        ),
        "Similarity report IDs follow SIM-submission-id-01"
    )

    check(
        all(re.fullmatch(r"INT-2026-\d{6}", x["case_id"])
            for x in cases),
        "Case IDs follow INT-2026-XXXXXX"
    )

    # -------------------------------------------------
    # 7. REPORT AND CASE RELATIONSHIP VALIDATION
    # -------------------------------------------------

    print("\n6. REPORT AND CASE RELATIONSHIPS")

    reports_by_id = {
        r["report_id"]: r for r in reports
    }

    check(
        all(
            c["submission_id"] ==
            reports_by_id[c["report_id"]]["submission_id"]
            for c in cases
        ),
        "Case submission IDs match their report submission IDs"
    )

    check(
        len({c["report_id"] for c in cases}) == len(cases),
        "Each case references a different report"
    )

    # -------------------------------------------------
    # 8. SIMILARITY SCORE VALIDATION
    # -------------------------------------------------

    print("\n7. SIMILARITY SCORE VALIDATION")

    check(
        all(0 <= float(r["similarity_score"]) <= 100
            for r in reports),
        "All similarity scores are between 0 and 100"
    )

    check(
        all(
            float(r["similarity_score"]) >= 50
            and r["evaluated_rule_id"] == "RULE_HIGH"
            and r["review_action"] == "REVIEW"
            for r in reports
        ),
        "All generated flags meet the manual-review rule"
    )

    check(
        all(
            r["report_category"] ==
            ("CRITICAL" if float(r["similarity_score"]) >= 75 else "HIGH")
            for r in reports
        ),
        "Report categories agree with the configured category boundary"
    )

    # -------------------------------------------------
    # 9. REPORT MATCH RECONCILIATION
    # -------------------------------------------------

    print("\n8. REPORT MATCH RECONCILIATION")

    matches_by_report = defaultdict(list)

    for match in matches:
        matches_by_report[match["report_id"]].append(match)

    match_counts_valid = True
    match_sums_valid = True
    sequences_valid = True

    for report in reports:
        report_matches = matches_by_report[report["report_id"]]

        if len(report_matches) != int(report["matched_source_count"]):
            match_counts_valid = False

        total = sum(
            (Decimal(m["match_percentage"]) for m in report_matches),
            Decimal("0")
        )

        if total != Decimal(report["similarity_score"]):
            match_sums_valid = False

        sequences = sorted(
            int(m["match_sequence"]) for m in report_matches
        )

        if sequences != list(range(1, len(report_matches) + 1)):
            sequences_valid = False

    check(
        match_counts_valid,
        "Match counts agree with each report's matched_source_count"
    )

    check(
        match_sums_valid,
        "Match percentages reconcile to the report similarity score"
    )

    check(
        sequences_valid,
        "Match sequence numbers are consecutive within each report"
    )

    check(
        all(0 <= float(m["match_percentage"]) <= 100 for m in matches),
        "All individual match percentages are within 0-100"
    )

    # -------------------------------------------------
    # 10. DATE VALIDATION
    # -------------------------------------------------

    print("\n9. DATE VALIDATION")

    submissions_by_id = {
        s["submission_id"]: s for s in submissions
    }

    valid_report_dates = True

    for report in reports:
        submitted = parse_date(
            submissions_by_id[report["submission_id"]]["submitted_at"]
        )

        generated = parse_date(report["generated_at"])

        if generated < submitted:
            valid_report_dates = False

    check(
        valid_report_dates,
        "Reports are generated after their submissions"
    )

    valid_case_dates = True

    for case in cases:
        report_date = parse_date(
            reports_by_id[case["report_id"]]["generated_at"]
        )

        created = parse_date(case["created_at"])
        due = parse_date(case["due_at"])

        if created < report_date or due <= created:
            valid_case_dates = False

    check(
        valid_case_dates,
        "Case creation follows report generation and due date follows creation"
    )

    check(
        all(
            c["case_status"] == "OPEN"
            and not c["closed_at"]
            and not c["closure_reason"]
            for c in cases
        ),
        "Open baseline cases have no closure information"
    )

    # -------------------------------------------------
    # 11. PRIORITY VALIDATION
    # -------------------------------------------------

    print("\n10. CASE PRIORITY VALIDATION")

    def expected_priority(score):
        if score >= 90:
            return "CRITICAL"
        if score >= 75:
            return "HIGH"
        if score >= 60:
            return "MEDIUM"
        return "LOW"

    check(
        all(
            c["priority"] == expected_priority(
                float(reports_by_id[c["report_id"]]["similarity_score"])
            )
            for c in cases
        ),
        "Case priorities are derived from similarity scores"
    )

    # -------------------------------------------------
    # 12. GROUND TRUTH VALIDATION
    # -------------------------------------------------

    print("\n11. GROUND TRUTH VALIDATION")

    truth_by_report = {
        item["report_id"]: item for item in ground_truth
    }

    check(
        unique(ground_truth, "report_id"),
        "Ground-truth report IDs are unique"
    )

    check(
        set(truth_by_report) == report_ids,
        "Ground truth covers exactly the generated reports"
    )

    scenario_expectations = {
        "UNAUTHORIZED_OVERLAP": (True, "TRUE_VIOLATION"),
        "LEGITIMATE_QUOTATION": (False, "FALSE_POSITIVE"),
        "SHARED_TEMPLATE": (False, "FALSE_POSITIVE"),
        "COMMON_CODE_PATTERN": (False, "FALSE_POSITIVE"),
        "INSUFFICIENT_EVIDENCE": (None, "INCONCLUSIVE")
    }

    truth_valid = True

    for item in ground_truth:
        expected = scenario_expectations.get(item["scenario_type"])

        if expected is None:
            truth_valid = False
            continue

        if (
            item["true_violation"] != expected[0]
            or item["synthetic_label"] != expected[1]
        ):
            truth_valid = False

    check(
        truth_valid,
        "Ground-truth labels agree with documented scenario rules"
    )

    check(
        all(
            truth_by_report[r["report_id"]]["submission_id"]
            == r["submission_id"]
            for r in reports
        ),
        "Ground-truth submission references match report records"
    )

    # -------------------------------------------------
    # 13. FINAL RESULT
    # -------------------------------------------------

    print("\n" + "=" * 65)
    print("VALIDATION SUMMARY")
    print("=" * 65)

    print("Checks passed:", checks_passed)
    print("Checks failed:", len(errors))

    if errors:
        print("\nValidation errors:")

        for error in errors:
            print("-", error)

        print("\nDATASET VALIDATION FAILED")
        sys.exit(1)

    print("\nALL DATASET VALIDATION CHECKS PASSED")


if __name__ == "__main__":
    main()
