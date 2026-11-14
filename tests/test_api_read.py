
import os
import requests
import pytest

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")


def get_json(path):
    response = requests.get(f"{BASE_URL}{path}", timeout=15)
    assert response.status_code == 200, (
        f"{path}: HTTP {response.status_code} - {response.text}"
    )
    return response.json()


@pytest.mark.parametrize("endpoint", [
    "/",
    "/health",
    "/health/db",
    "/api/v1/system/tables",
    "/api/v1/system/schema",
    "/api/v1/system/summary",
    "/api/v1/submissions",
    "/api/v1/similarity-reports",
    "/api/v1/cases",
    "/api/v1/evidence",
    "/api/v1/reviewers",
    "/api/v1/reviewer-assignments",
    "/api/v1/decisions",
    "/api/v1/appeals",
    "/api/v1/audit-logs",
    "/api/v1/dashboard/summary",
])
def test_get_endpoint_returns_success(endpoint):
    assert get_json(endpoint) is not None


def test_dashboard_baseline_counts():
    totals = get_json("/api/v1/dashboard/summary")["totals"]

    expected = {
        "learners": 2000,
        "assessments": 100,
        "submissions": 10000,
        "similarity_reports": 1000,
        "cases": 300,
        "evidence_items": 920,
        "reviewers": 30,
        "decisions": 341,
        "appeals": 41,
        "appeal_reviews": 41,
    }

    for key, value in expected.items():
        assert totals[key] == value, f"{key}: expected {value}, got {totals[key]}"


def test_all_baseline_cases_are_closed():
    metrics = get_json("/api/v1/dashboard/summary")["case_metrics"]
    assert metrics["closed"] == 300
    assert metrics["not_closed"] == 0


def test_all_baseline_appeals_are_resolved():
    metrics = get_json("/api/v1/dashboard/summary")["appeal_metrics"]
    assert metrics["by_status"]["RESOLVED"] == 41


def test_all_appeals_have_independent_reviews():
    totals = get_json("/api/v1/dashboard/summary")["totals"]
    assert totals["appeals"] == totals["appeal_reviews"] == 41


@pytest.mark.parametrize("endpoint,collection,id_field", [
    ("/api/v1/submissions", "submissions", "submission_id"),
    ("/api/v1/similarity-reports", "reports", "report_id"),
    ("/api/v1/cases", "cases", "case_id"),
    ("/api/v1/evidence", "evidence", "evidence_id"),
    ("/api/v1/decisions", "decisions", "decision_id"),
    ("/api/v1/appeals", "items", "appeal_id"),
])
def test_detail_endpoint_matches_list_record(endpoint, collection, id_field):
    listing = get_json(endpoint)
    records = listing[collection]

    assert len(records) > 0

    record_id = records[0][id_field]
    detail = get_json(f"{endpoint}/{record_id}")

    # Appeals return a wrapper containing appeal and reviews.
    if endpoint == "/api/v1/appeals":
        assert detail["appeal"][id_field] == record_id
    else:
        assert detail[id_field] == record_id


def test_case_timeline_endpoint():
    cases = get_json("/api/v1/cases")["cases"]
    assert cases

    case_id = cases[0]["case_id"]
    timeline = get_json(f"/api/v1/cases/{case_id}/timeline")

    assert timeline is not None


def test_similarity_reports_are_not_automatic_guilt():
    reports = get_json("/api/v1/similarity-reports")["reports"]

    assert reports
    for report in reports:
        assert report["review_action"] in {
            "REVIEW",
            "NO_ACTION",
            "MONITOR",
        }
