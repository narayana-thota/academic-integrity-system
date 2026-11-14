
import json
import sys
from pathlib import Path

sys.path.insert(0, "/app")

from sqlalchemy import inspect, text
from app.database import engine

EXPECTED_TABLES = {
    "learners", "assessments", "reviewers", "integrity_rules",
    "submissions", "similarity_reports", "cases", "evidence_items",
    "case_evidence", "reviewer_conflicts", "reviewer_assignments",
    "report_matches", "decisions", "appeals", "appeal_reviews",
    "case_events", "audit_logs",
}

EXPECTED_COUNTS = {
    "learners": 2000,
    "assessments": 100,
    "reviewers": 30,
    "integrity_rules": 3,
    "submissions": 10000,
    "similarity_reports": 1000,
    "cases": 300,
    "evidence_items": 920,
    "case_evidence": 920,
    "reviewer_conflicts": 30,
    "reviewer_assignments": 300,
    "report_matches": 3059,
    "decisions": 341,
    "appeals": 41,
    "appeal_reviews": 41,
    "case_events": 3897,
    "audit_logs": 3897,
}

EXPECTED_FKS = {
    "fk_submission_learner",
    "fk_submission_assessment",
    "fk_report_submission",
    "fk_report_rule",
    "fk_case_submission",
    "fk_case_report",
    "fk_case_rule",
    "fk_case_evidence_case",
    "fk_case_evidence_item",
    "fk_conflict_reviewer",
    "fk_conflict_learner",
    "fk_conflict_assessment",
    "fk_assignment_case",
    "fk_assignment_reviewer",
    "fk_match_report",
    "fk_decision_case",
    "fk_decision_reviewer",
    "fk_decision_supersedes",
    "fk_appeal_case",
    "fk_appeal_decision",
    "fk_appeal_learner",
    "fk_appeal_review_appeal",
    "fk_appeal_review_reviewer",
    "fk_event_case",
    "fk_audit_case",
}

results = []

def scalar(connection, query, params=None):
    return connection.execute(text(query), params or {}).scalar() or 0

def check(name, passed, detail):
    results.append({
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "detail": str(detail),
    })
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")

def validate():
    with engine.connect() as connection:
        inspector = inspect(connection)
        actual_tables = set(inspector.get_table_names())

        # 1. Table structure
        check(
            "Expected database tables",
            actual_tables == EXPECTED_TABLES,
            f"Expected {len(EXPECTED_TABLES)}, found {len(actual_tables)}"
        )

        missing_tables = EXPECTED_TABLES - actual_tables
        check(
            "No missing tables",
            not missing_tables,
            f"Missing: {sorted(missing_tables) if missing_tables else 'None'}"
        )

        # 2. Primary keys
        missing_pk = []
        for table in sorted(EXPECTED_TABLES & actual_tables):
            pk = inspector.get_pk_constraint(table).get("constrained_columns")
            if not pk:
                missing_pk.append(table)

        check(
            "Primary keys",
            not missing_pk,
            f"Tables without primary keys: {missing_pk}"
        )

        # 3. Foreign-key constraints
        fk_rows = connection.execute(text("""
            SELECT CONSTRAINT_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND REFERENCED_TABLE_NAME IS NOT NULL
        """)).scalars().all()

        actual_fks = set(fk_rows)

        check(
            "Foreign-key constraint count",
            len(actual_fks) == 25,
            f"Expected 25, found {len(actual_fks)}"
        )

        missing_fks = EXPECTED_FKS - actual_fks
        check(
            "Expected foreign-key names",
            not missing_fks,
            f"Missing: {sorted(missing_fks) if missing_fks else 'None'}"
        )

        # 4. Foreign-key orphan checks
        fk_relationships = [
            ("submissions", "learner_id", "learners", "learner_id", False),
            ("submissions", "assessment_id", "assessments", "assessment_id", False),
            ("similarity_reports", "submission_id", "submissions", "submission_id", False),
            ("similarity_reports", "evaluated_rule_id", "integrity_rules", "rule_id", True),
            ("cases", "submission_id", "submissions", "submission_id", False),
            ("cases", "report_id", "similarity_reports", "report_id", False),
            ("cases", "rule_id", "integrity_rules", "rule_id", False),
            ("case_evidence", "case_id", "cases", "case_id", False),
            ("case_evidence", "evidence_id", "evidence_items", "evidence_id", False),
            ("reviewer_conflicts", "reviewer_id", "reviewers", "reviewer_id", False),
            ("reviewer_conflicts", "learner_id", "learners", "learner_id", True),
            ("reviewer_conflicts", "assessment_id", "assessments", "assessment_id", True),
            ("reviewer_assignments", "case_id", "cases", "case_id", False),
            ("reviewer_assignments", "reviewer_id", "reviewers", "reviewer_id", False),
            ("report_matches", "report_id", "similarity_reports", "report_id", False),
            ("decisions", "case_id", "cases", "case_id", False),
            ("decisions", "reviewer_id", "reviewers", "reviewer_id", False),
            ("decisions", "supersedes_decision_id", "decisions", "decision_id", True),
            ("appeals", "case_id", "cases", "case_id", False),
            ("appeals", "original_decision_id", "decisions", "decision_id", False),
            ("appeals", "submitted_by_learner_id", "learners", "learner_id", False),
            ("appeal_reviews", "appeal_id", "appeals", "appeal_id", False),
            ("appeal_reviews", "reviewer_id", "reviewers", "reviewer_id", False),
            ("case_events", "case_id", "cases", "case_id", False),
            ("audit_logs", "case_id", "cases", "case_id", True),
        ]

        orphan_total = 0

        for child, child_col, parent, parent_col, nullable in fk_relationships:
            null_filter = f" AND child.{child_col} IS NOT NULL" if nullable else ""

            query = f"""
                SELECT COUNT(*)
                FROM {child} child
                LEFT JOIN {parent} parent
                  ON child.{child_col} = parent.{parent_col}
                WHERE parent.{parent_col} IS NULL
                {null_filter}
            """

            orphan_count = scalar(connection, query)
            orphan_total += orphan_count

        check(
            "Foreign-key orphan validation",
            orphan_total == 0,
            f"25 relationships checked; total orphan records: {orphan_total}"
        )

        # 5. Exact baseline row counts
        count_failures = []

        for table, expected in EXPECTED_COUNTS.items():
            actual = scalar(connection, f"SELECT COUNT(*) FROM {table}")
            if actual != expected:
                count_failures.append(
                    f"{table}: expected {expected}, found {actual}"
                )

        check(
            "Baseline row counts",
            not count_failures,
            "; ".join(count_failures) if count_failures else
            "All 17 table counts match the generated dataset"
        )

        # 6. Case lifecycle and closure
        closed_cases = scalar(connection, """
            SELECT COUNT(*) FROM cases
            WHERE case_status = 'CLOSED'
              AND closed_at IS NOT NULL
              AND closure_reason IS NOT NULL
        """)

        invalid_closures = scalar(connection, """
            SELECT COUNT(*) FROM cases
            WHERE (case_status = 'CLOSED'
                   AND (closed_at IS NULL OR closure_reason IS NULL))
               OR (closed_at IS NOT NULL AND case_status <> 'CLOSED')
        """)

        check(
            "Case closure consistency",
            closed_cases == 300 and invalid_closures == 0,
            f"Valid closed cases: {closed_cases}; invalid closures: {invalid_closures}"
        )

        # 7. Reviewer assignments
        active_assignments = scalar(connection, """
            SELECT COUNT(*) FROM reviewer_assignments
            WHERE assignment_status = 'ACTIVE'
        """)

        incomplete_assignments = scalar(connection, """
            SELECT COUNT(*) FROM reviewer_assignments
            WHERE assignment_status = 'COMPLETED'
              AND (ended_at IS NULL OR end_reason IS NULL)
        """)

        check(
            "Reviewer assignment lifecycle",
            active_assignments == 0 and incomplete_assignments == 0,
            f"Active assignments: {active_assignments}; "
            f"incomplete completed assignments: {incomplete_assignments}"
        )

        assignment_conflicts = scalar(connection, """
            SELECT COUNT(*)
            FROM reviewer_assignments ra
            JOIN cases c ON c.case_id = ra.case_id
            JOIN submissions s ON s.submission_id = c.submission_id
            JOIN reviewer_conflicts rc
              ON rc.reviewer_id = ra.reviewer_id
             AND rc.is_active = TRUE
             AND (
                 rc.learner_id = s.learner_id
                 OR rc.assessment_id = s.assessment_id
             )
        """)

        check(
            "No conflicted case assignments",
            assignment_conflicts == 0,
            f"Conflicted assignments: {assignment_conflicts}"
        )

        # 8. Initial decisions
        initial_count = scalar(connection, """
            SELECT COUNT(*) FROM decisions
            WHERE decision_stage = 'INITIAL'
        """)

        cases_without_initial = scalar(connection, """
            SELECT COUNT(*)
            FROM cases c
            LEFT JOIN decisions d
              ON d.case_id = c.case_id
             AND d.decision_stage = 'INITIAL'
            WHERE d.decision_id IS NULL
        """)

        multiple_initial = scalar(connection, """
            SELECT COUNT(*) FROM (
                SELECT case_id
                FROM decisions
                WHERE decision_stage = 'INITIAL'
                GROUP BY case_id
                HAVING COUNT(*) <> 1
            ) x
        """)

        check(
            "Initial decision coverage",
            initial_count == 300
            and cases_without_initial == 0
            and multiple_initial == 0,
            f"Initial decisions: {initial_count}; cases without one: "
            f"{cases_without_initial}; duplicate cases: {multiple_initial}"
        )

        # Initial decision reviewer must have been assigned to that case
        unassigned_decisions = scalar(connection, """
            SELECT COUNT(*)
            FROM decisions d
            LEFT JOIN reviewer_assignments ra
              ON ra.case_id = d.case_id
             AND ra.reviewer_id = d.reviewer_id
            WHERE d.decision_stage = 'INITIAL'
              AND ra.assignment_id IS NULL
        """)

        check(
            "Initial decision reviewer assignment",
            unassigned_decisions == 0,
            f"Initial decisions without matching assignment: {unassigned_decisions}"
        )

        # 9. Appeal and independent review
        resolved_appeals = scalar(connection, """
            SELECT COUNT(*) FROM appeals
            WHERE appeal_status = 'RESOLVED'
              AND outcome IS NOT NULL
              AND resolved_at IS NOT NULL
        """)

        appeals_without_review = scalar(connection, """
            SELECT COUNT(*)
            FROM appeals a
            WHERE a.appeal_status = 'RESOLVED'
              AND NOT EXISTS (
                  SELECT 1
                  FROM appeal_reviews ar
                  WHERE ar.appeal_id = a.appeal_id
              )
        """)

        appeal_review_count = scalar(connection, """
            SELECT COUNT(*) FROM appeal_reviews
        """)

        check(
            "Appeal review coverage",
            resolved_appeals == 41
            and appeal_review_count == 41
            and appeals_without_review == 0,
            f"Resolved appeals: {resolved_appeals}; "
            f"independent reviews: {appeal_review_count}"
        )

        same_reviewer = scalar(connection, """
            SELECT COUNT(*)
            FROM appeals a
            JOIN decisions original
              ON original.decision_id = a.original_decision_id
            JOIN appeal_reviews ar
              ON ar.appeal_id = a.appeal_id
            WHERE original.reviewer_id = ar.reviewer_id
        """)

        check(
            "Independent appeal reviewers",
            same_reviewer == 0,
            f"Appeals reviewed by original decision-maker: {same_reviewer}"
        )

        appeal_conflicts = scalar(connection, """
            SELECT COUNT(*)
            FROM appeal_reviews ar
            JOIN appeals a ON a.appeal_id = ar.appeal_id
            JOIN cases c ON c.case_id = a.case_id
            JOIN submissions s ON s.submission_id = c.submission_id
            JOIN reviewer_conflicts rc
              ON rc.reviewer_id = ar.reviewer_id
             AND rc.is_active = TRUE
             AND (
                 rc.learner_id = s.learner_id
                 OR rc.assessment_id = s.assessment_id
             )
        """)

        check(
            "Conflict-free appeal reviewers",
            appeal_conflicts == 0,
            f"Conflicted appeal reviews: {appeal_conflicts}"
        )

        # Appeal original decision must belong to the same case
        wrong_original_case = scalar(connection, """
            SELECT COUNT(*)
            FROM appeals a
            JOIN decisions d ON d.decision_id = a.original_decision_id
            WHERE a.case_id <> d.case_id
               OR d.decision_stage <> 'INITIAL'
        """)

        wrong_appeal_learner = scalar(connection, """
            SELECT COUNT(*)
            FROM appeals a
            JOIN cases c ON c.case_id = a.case_id
            JOIN submissions s ON s.submission_id = c.submission_id
            WHERE a.submitted_by_learner_id <> s.learner_id
        """)

        check(
            "Appeal ownership and original decision",
            wrong_original_case == 0 and wrong_appeal_learner == 0,
            f"Invalid original decisions: {wrong_original_case}; "
            f"wrong learner submissions: {wrong_appeal_learner}"
        )

        # Reassessment must correspond to appeal outcome
        wrong_reassessment = scalar(connection, """
            SELECT COUNT(*)
            FROM appeals a
            JOIN appeal_reviews ar ON ar.appeal_id = a.appeal_id
            LEFT JOIN decisions d
              ON d.case_id = a.case_id
             AND d.decision_stage = 'REASSESSMENT'
             AND d.reviewer_id = ar.reviewer_id
            WHERE d.decision_id IS NULL
               OR d.decision_type <> a.outcome
               OR ar.outcome <> a.outcome
        """)

        check(
            "Appeal and reassessment reconciliation",
            wrong_reassessment == 0,
            f"Inconsistent appeal/reassessment records: {wrong_reassessment}"
        )

        # 10. Event and audit history
        cases_without_events = scalar(connection, """
            SELECT COUNT(*)
            FROM cases c
            LEFT JOIN case_events e ON e.case_id = c.case_id
            WHERE e.event_id IS NULL
        """)

        cases_without_audits = scalar(connection, """
            SELECT COUNT(*)
            FROM cases c
            LEFT JOIN audit_logs a ON a.case_id = c.case_id
            WHERE a.audit_id IS NULL
        """)

        event_count = scalar(connection, "SELECT COUNT(*) FROM case_events")
        audit_count = scalar(connection, "SELECT COUNT(*) FROM audit_logs")

        check(
            "Case event and audit history",
            cases_without_events == 0
            and cases_without_audits == 0
            and event_count == audit_count == 3897,
            f"Events: {event_count}; audits: {audit_count}; "
            f"cases without events: {cases_without_events}; "
            f"cases without audits: {cases_without_audits}"
        )

        # 11. Ground truth separation
        check(
            "Ground truth separation",
            "ground_truth" not in actual_tables,
            "Ground-truth labels are not stored in operational database tables"
        )

    passed = sum(r["status"] == "PASS" for r in results)
    failed = sum(r["status"] == "FAIL" for r in results)

    report = {
        "phase": "5.4",
        "database": "academic_integrity",
        "expected_tables": len(EXPECTED_TABLES),
        "expected_foreign_keys": len(EXPECTED_FKS),
        "checks_passed": passed,
        "checks_failed": failed,
        "overall_status": "PASS" if failed == 0 else "FAIL",
        "results": results,
    }

    output = Path("/data_engineering/output/mysql_validation_report.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n" + "=" * 55)
    print("MYSQL VALIDATION SUMMARY")
    print("=" * 55)
    print(f"Checks passed : {passed}")
    print(f"Checks failed : {failed}")
    print(f"Overall       : {report['overall_status']}")
    print(f"Report        : {output}")

    if failed:
        raise SystemExit(1)

if __name__ == "__main__":
    validate()
