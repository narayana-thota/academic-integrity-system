
import sys
from pathlib import Path

sys.path.insert(0, "/app")

from sqlalchemy import inspect
from app.database import engine

TABLE_DESCRIPTIONS = {
    "learners": "Master records for learners who submit academic work.",
    "assessments": "Academic assessments to which submissions belong.",
    "reviewers": "Instructors and administrators who review integrity cases.",
    "integrity_rules": "Versioned similarity thresholds and their corresponding review actions.",
    "submissions": "Learner submissions associated with assessments.",
    "similarity_reports": "Similarity analysis results generated for submissions.",
    "cases": "Formal academic integrity investigations.",
    "evidence_items": "Evidence records collected during investigations.",
    "case_evidence": "Bridge table linking cases to evidence items.",
    "reviewer_conflicts": "Declared reviewer conflicts involving learners or assessments.",
    "reviewer_assignments": "Reviewer assignment history for investigation cases.",
    "report_matches": "Individual matched sources within similarity reports.",
    "decisions": "Initial and reassessment decisions with reviewer rationale.",
    "appeals": "Learner appeals against original case decisions.",
    "appeal_reviews": "Independent reviewer assessments of appeals.",
    "case_events": "Chronological case timeline events.",
    "audit_logs": "Audit records tracking actions and affected entities.",
}

def clean(value):
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ").strip()

def generate_dictionary():
    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())

    lines = [
        "# Academic Integrity Case Management System",
        "",
        "## Database Data Dictionary",
        "",
        "- Database: `academic_integrity`",
        "- Engine: MySQL 8.4 / InnoDB",
        f"- Tables documented: {len(tables)}",
        "- Source: Live MySQL schema inspection",
        "",
        "## Table overview",
        "",
        "| Table | Purpose |",
        "|---|---|",
    ]

    for table in tables:
        description = TABLE_DESCRIPTIONS.get(
            table, "Operational table in the academic integrity system."
        )
        lines.append(f"| `{table}` | {description} |")

    for table in tables:
        lines.extend([
            "",
            f"## {table}",
            "",
            TABLE_DESCRIPTIONS.get(
                table, "Operational table in the academic integrity system."
            ),
            "",
            "### Columns",
            "",
            "| Column | Data type | Nullable | Default | Key |",
            "|---|---|---|---|---|",
        ])

        columns = inspector.get_columns(table)
        pk_columns = inspector.get_pk_constraint(table).get("constrained_columns") or []
        fk_constraints = inspector.get_foreign_keys(table)
        unique_constraints = inspector.get_unique_constraints(table)

        fk_map = {}
        for fk in fk_constraints:
            for column in fk.get("constrained_columns") or []:
                referred_table = fk.get("referred_table")
                referred_columns = fk.get("referred_columns") or []
                target = ", ".join(referred_columns)
                fk_map[column] = f"FK → {referred_table}.{target}"

        unique_columns = set()
        for constraint in unique_constraints:
            unique_columns.update(constraint.get("column_names") or [])

        for column in columns:
            name = column["name"]
            keys = []

            if name in pk_columns:
                keys.append("PK")
            if name in fk_map:
                keys.append(fk_map[name])
            if name in unique_columns:
                keys.append("UNIQUE")

            lines.append(
                f"| `{name}` | `{clean(column['type'])}` "
                f"| {'Yes' if column.get('nullable') else 'No'} "
                f"| `{clean(column.get('default'))}` "
                f"| {', '.join(keys)} |"
            )

        lines.extend([
            "",
            "### Foreign-key relationships",
            "",
        ])

        if fk_constraints:
            for fk in fk_constraints:
                source = ", ".join(fk.get("constrained_columns") or [])
                target = ", ".join(fk.get("referred_columns") or [])
                lines.append(
                    f"- `{source}` → `{fk.get('referred_table')}.{target}`"
                )
        else:
            lines.append("- No foreign keys.")

        lines.extend([
            "",
            "### Unique constraints",
            "",
        ])

        if unique_constraints:
            for constraint in unique_constraints:
                columns_text = ", ".join(
                    constraint.get("column_names") or []
                )
                lines.append(
                    f"- `{constraint.get('name')}`: `{columns_text}`"
                )
        else:
            lines.append("- No additional unique constraints.")

        lines.extend([
            "",
            "### Check constraints",
            "",
        ])

        try:
            checks = inspector.get_check_constraints(table)
        except NotImplementedError:
            checks = []

        if checks:
            for check in checks:
                lines.append(
                    f"- `{check.get('name')}`: "
                    f"`{clean(check.get('sqltext'))}`"
                )
        else:
            lines.append("- No check constraints reported by the database.")

        lines.extend([
            "",
            "### Indexes",
            "",
        ])

        indexes = inspector.get_indexes(table)
        if indexes:
            for index in indexes:
                columns_text = ", ".join(index.get("column_names") or [])
                unique_text = "UNIQUE" if index.get("unique") else "NON-UNIQUE"
                lines.append(
                    f"- `{index.get('name')}` ({unique_text}): `{columns_text}`"
                )
        else:
            lines.append("- No additional indexes.")

    lines.extend([
        "",
        "## Important business rules",
        "",
        "1. Similarity scores are indicators for review, not automatic proof of misconduct.",
        "2. Investigation decisions must include reviewer rationale.",
        "3. Reviewer conflicts must be checked before assignment.",
        "4. Appeals require independent review.",
        "5. Historical decisions and case events must remain traceable.",
        "6. Case closure requires a closure timestamp and closure reason.",
        "7. Ground-truth labels are maintained separately from operational database records.",
        "",
    ])

    output = Path("/data_engineering/output/data_dictionary.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")

    print(f"Data dictionary generated: {output}")
    print(f"Tables documented: {len(tables)}")

    if len(tables) != 17:
        raise SystemExit("FAIL: Expected 17 tables.")

    print("PASS: All 17 database tables documented.")

if __name__ == "__main__":
    with engine.connect() as connection:
        connection.execute(__import__("sqlalchemy").text("SELECT 1"))

    generate_dictionary()
