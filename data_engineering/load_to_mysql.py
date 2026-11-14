
import csv
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import MetaData, inspect
from sqlalchemy.sql.sqltypes import (
    Boolean,
    Date,
    DateTime,
    Integer,
    Numeric,
)

# The API container has the backend mounted at /app.
sys.path.insert(0, "/app")

from app.database import engine


OUTPUT_DIR = Path(__file__).resolve().parent / "output"
BATCH_SIZE = 500

# Parent tables must be loaded before dependent tables.
LOAD_ORDER = [
    "learners",
    "assessments",
    "reviewers",
    "integrity_rules",
    "submissions",
    "similarity_reports",
    "cases",
    "evidence_items",
    "report_matches",
    "reviewer_conflicts",
    "reviewer_assignments",
    "case_evidence",
    "decisions",
    "appeals",
    "appeal_reviews",
    "case_events",
    "audit_logs",
]

BOOLEAN_COLUMNS = {"is_active"}
JSON_COLUMNS = {"event_data"}


def convert_value(value, column):
    """Convert CSV strings into values suitable for MySQL."""

    if value is None or value.strip() == "":
        return None

    value = value.strip()
    column_name = column.name
    column_type = column.type

    if column_name in BOOLEAN_COLUMNS or isinstance(column_type, Boolean):
        lowered = value.lower()

        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False

        raise ValueError(
            f"Invalid Boolean value for {column_name}: {value}"
        )

    if column_name in JSON_COLUMNS:
        parsed = json.loads(value)
        return json.dumps(parsed, ensure_ascii=False)

    if isinstance(column_type, DateTime):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.replace(tzinfo=None)
        return parsed

    if isinstance(column_type, Date):
        return date.fromisoformat(value[:10])

    if isinstance(column_type, Integer):
        return int(value)

    if isinstance(column_type, Numeric):
        return Decimal(value)

    return value


def read_csv(table_name):
    file_path = OUTPUT_DIR / f"{table_name}.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required CSV file not found: {file_path}"
        )

    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {file_path}")

        rows = list(reader)

    if not rows:
        raise ValueError(f"CSV contains no records: {file_path}")

    return reader.fieldnames, rows


def main():
    print("=" * 65)
    print("PHASE 5: MYSQL DATA LOADING")
    print("=" * 65)

    metadata = MetaData()
    metadata.reflect(bind=engine)

    available_tables = set(metadata.tables.keys())

    missing_tables = set(LOAD_ORDER) - available_tables
    if missing_tables:
        raise RuntimeError(
            f"Tables missing from database: {sorted(missing_tables)}"
        )

    # Verify that every target table is empty before loading.
    with engine.connect() as connection:
        existing_counts = {}

        for table_name in LOAD_ORDER:
            count = connection.exec_driver_sql(
                f"SELECT COUNT(*) FROM `{table_name}`"
            ).scalar_one()

            existing_counts[table_name] = count

    non_empty = {
        name: count
        for name, count in existing_counts.items()
        if count != 0
    }

    if non_empty:
        raise RuntimeError(
            "Loading stopped because some target tables are not empty. "
            f"Existing counts: {non_empty}. "
            "No records were deleted."
        )

    print("\nPre-check passed: all 17 target tables are empty.")

    expected_counts = {}

    # One transaction for the entire import.
    with engine.begin() as connection:

        for table_name in LOAD_ORDER:
            print(f"\nLoading: {table_name}")

            table = metadata.tables[table_name]
            headers, rows = read_csv(table_name)

            unknown_columns = set(headers) - set(table.columns.keys())

            if unknown_columns:
                raise ValueError(
                    f"{table_name}.csv contains columns absent "
                    f"from MySQL: {sorted(unknown_columns)}"
                )

            prepared_rows = []

            for row_number, row in enumerate(rows, start=2):
                prepared = {}

                for header in headers:
                    column = table.columns[header]
                    raw_value = row.get(header)

                    try:
                        prepared[header] = convert_value(
                            raw_value, column
                        )
                    except Exception as exc:
                        raise ValueError(
                            f"Error in {table_name}.csv, "
                            f"row {row_number}, column {header}: {exc}"
                        ) from exc

                prepared_rows.append(prepared)

            for start in range(0, len(prepared_rows), BATCH_SIZE):
                batch = prepared_rows[start:start + BATCH_SIZE]
                connection.execute(table.insert(), batch)

            expected_counts[table_name] = len(prepared_rows)

            print(f"  Inserted: {len(prepared_rows)} records")

        # Verify all counts before committing.
        print("\nVerifying imported record counts...")

        for table_name, expected in expected_counts.items():
            actual = connection.exec_driver_sql(
                f"SELECT COUNT(*) FROM `{table_name}`"
            ).scalar_one()

            if actual != expected:
                raise RuntimeError(
                    f"Count mismatch in {table_name}: "
                    f"expected {expected}, found {actual}"
                )

            print(f"  PASS {table_name}: {actual}")

    print("\n" + "=" * 65)
    print("DATABASE LOADING COMPLETED SUCCESSFULLY")
    print("=" * 65)

    print(f"Tables loaded: {len(LOAD_ORDER)}")
    print(f"Total records: {sum(expected_counts.values())}")
    print("Transaction committed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\nDATABASE LOADING FAILED")
        print(f"Reason: {error}")
        print("If the transaction had started, its changes were rolled back.")
        raise
