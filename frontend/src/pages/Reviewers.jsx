
import { useEffect, useMemo, useState } from "react";
import {
  fetchReviewers,
  fetchReviewerAssignments,
} from "../services/api";

import "../styles/reviewers.css";

function getRows(response, keys) {
  if (Array.isArray(response)) return response;

  for (const key of keys) {
    if (Array.isArray(response?.[key])) return response[key];
    if (Array.isArray(response?.data?.[key])) return response.data[key];
  }

  if (Array.isArray(response?.data)) return response.data;
  return [];
}

function getReviewerId(item) {
  return item.reviewer_id ?? item.id ?? item.user_id ?? "—";
}

function getReviewerName(item) {
  return (
    item.reviewer_name ??
    item.full_name ??
    item.name ??
    item.username ??
    `Reviewer ${getReviewerId(item)}`
  );
}

// Map the backend is_active field to a readable status.
function getStatus(item) {
  if (item.is_active !== undefined && item.is_active !== null) {
    return Number(item.is_active) === 1 ? "Active" : "Inactive";
  }

  return String(
    item.status ?? item.availability_status ?? "Unknown"
  );
}

function getAssignmentReviewerId(item) {
  return String(
    item.reviewer_id ??
      item.assigned_reviewer_id ??
      item.reviewer?.reviewer_id ??
      ""
  );
}

function getAssignmentCaseId(item) {
  return (
    item.case_id ??
    item.assigned_case_id ??
    item.case?.case_id ??
    "—"
  );
}

function StatCard({ label, value, hint }) {
  return (
    <article className="reviewer-stat">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{hint}</small>
    </article>
  );
}

function StatusBadge({ status }) {
  const normalized = String(status).toLowerCase();

  let className = "unknown";

  if (
    normalized === "active" ||
    normalized === "available" ||
    normalized === "eligible"
  ) {
    className = "available";
  } else if (
    normalized === "inactive" ||
    normalized === "unavailable"
  ) {
    className = "unavailable";
  }

  return (
    <span className={`reviewer-status ${className}`}>
      {String(status).replaceAll("_", " ")}
    </span>
  );
}

export default function Reviewers() {
  const [reviewers, setReviewers] = useState([]);
  const [assignments, setAssignments] = useState([]);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedReviewer, setSelectedReviewer] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [assignmentError, setAssignmentError] = useState("");

  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let active = true;

    async function loadReviewerData() {
      setLoading(true);
      setError("");
      setAssignmentError("");

      const [reviewerResult, assignmentResult] =
        await Promise.allSettled([
          fetchReviewers(),
          fetchReviewerAssignments(),
        ]);

      if (!active) return;

      if (reviewerResult.status === "fulfilled") {
        setReviewers(
          getRows(reviewerResult.value, ["reviewers", "items"])
        );
      } else {
        setError(
          reviewerResult.reason?.response?.data?.detail ??
            reviewerResult.reason?.message ??
            "Unable to load reviewers."
        );
      }

      if (assignmentResult.status === "fulfilled") {
        setAssignments(
          getRows(assignmentResult.value, [
            "assignments",
            "reviewer_assignments",
            "items",
          ])
        );
      } else {
        setAssignments([]);
        setAssignmentError(
          "Reviewer assignment records are unavailable."
        );
      }

      setLoading(false);
    }

    loadReviewerData();

    return () => {
      active = false;
    };
  }, [refreshKey]);

  const assignmentCounts = useMemo(() => {
    const counts = {};

    assignments.forEach((assignment) => {
      const reviewerId = getAssignmentReviewerId(assignment);

      if (reviewerId) {
        counts[reviewerId] = (counts[reviewerId] || 0) + 1;
      }
    });

    return counts;
  }, [assignments]);

  const filteredReviewers = useMemo(() => {
    const query = search.trim().toLowerCase();

    return reviewers.filter((reviewer) => {
      const id = String(getReviewerId(reviewer));
      const name = String(getReviewerName(reviewer));
      const status = getStatus(reviewer).toLowerCase();

      const matchesSearch =
        !query ||
        id.toLowerCase().includes(query) ||
        name.toLowerCase().includes(query) ||
        String(reviewer.email ?? "").toLowerCase().includes(query);

      const matchesStatus =
        statusFilter === "all" ||
        status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [reviewers, search, statusFilter]);

  const selectedAssignments = selectedReviewer
    ? assignments.filter(
        (item) =>
          getAssignmentReviewerId(item) ===
          String(getReviewerId(selectedReviewer))
      )
    : [];

  const availableCount = reviewers.filter(
    (reviewer) => getStatus(reviewer) === "Active"
  ).length;

  const totalAssignments = assignments.length;

  if (loading) {
    return (
      <main className="reviewers-page">
        <div className="reviewers-state">
          <div className="reviewers-spinner" />
          <p>Loading reviewer information...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="reviewers-page">
        <div className="reviewers-state reviewer-error">
          <h2>Unable to load reviewers</h2>
          <p>{error}</p>
          <button onClick={() => setRefreshKey((value) => value + 1)}>
            Retry
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="reviewers-page">
      <header className="reviewers-header">
        <div>
          <p className="eyebrow">
            ACADEMIC INTEGRITY / REVIEW OPERATIONS
          </p>

          <h1>Reviewer Management</h1>

          <p>
            Monitor reviewer availability, case assignments,
            workload, and case-level eligibility.
          </p>
        </div>

        <div className="reviewer-count-pill">
          <span />
          {reviewers.length} reviewers registered
        </div>
      </header>

      <section className="reviewer-stats">
        <StatCard
          label="Total reviewers"
          value={reviewers.length}
          hint="Registered reviewer records"
        />

        <StatCard
          label="Available / active"
          value={availableCount}
          hint="Based on reviewer active status"
        />

        <StatCard
          label="Assignments"
          value={totalAssignments}
          hint="Records returned by the API"
        />

        <StatCard
          label="Conflict verification"
          value="Case-level"
          hint="Checked through reviewer eligibility API"
        />
      </section>

      <section className="reviewers-content">
        <div className="reviewers-section-heading">
          <div>
            <h2>Reviewer directory</h2>
            <p>
              Select a reviewer to inspect their assignment history.
            </p>
          </div>
        </div>

        <div className="reviewers-filters">
          <div className="reviewers-search">
            <span>⌕</span>

            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search reviewer name, ID, or email..."
            />
          </div>

          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>

          <button
            className="reviewers-refresh"
            onClick={() => setRefreshKey((value) => value + 1)}
          >
            ↻ Refresh
          </button>
        </div>

        {filteredReviewers.length === 0 ? (
          <div className="reviewers-empty">
            No reviewers match the selected filters.
          </div>
        ) : (
          <div className="reviewers-table-wrap">
            <table className="reviewers-table">
              <thead>
                <tr>
                  <th>Reviewer</th>
                  <th>Reviewer ID</th>
                  <th>Role</th>
                  <th>Assignments</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {filteredReviewers.map((reviewer, index) => {
                  const id = String(getReviewerId(reviewer));
                  const name = getReviewerName(reviewer);

                  return (
                    <tr
                      key={id === "—" ? index : id}
                      className={
                        selectedReviewer &&
                        String(getReviewerId(selectedReviewer)) === id
                          ? "selected"
                          : ""
                      }
                      onClick={() => setSelectedReviewer(reviewer)}
                    >
                      <td>
                        <div className="reviewer-person">
                          <div className="reviewer-avatar">
                            {String(name).charAt(0).toUpperCase()}
                          </div>

                          <div>
                            <strong>{name}</strong>
                            <span>
                              {reviewer.email ?? "Email unavailable"}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td>{id}</td>

                      <td>
                        {reviewer.role ??
                          reviewer.reviewer_role ??
                          "Reviewer"}
                      </td>

                      <td>{assignmentCounts[id] ?? 0}</td>

                      <td>
                        <StatusBadge status={getStatus(reviewer)} />
                      </td>

                      <td>
                        <button
                          className="reviewer-view-button"
                          onClick={(event) => {
                            event.stopPropagation();
                            setSelectedReviewer(reviewer);
                          }}
                        >
                          View →
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {assignmentError && (
        <p className="reviewer-data-note">{assignmentError}</p>
      )}

      {selectedReviewer && (
        <section className="reviewer-detail-panel">
          <div className="reviewer-detail-heading">
            <div>
              <p className="eyebrow">REVIEWER PROFILE</p>
              <h2>{getReviewerName(selectedReviewer)}</h2>
              <span>
                Reviewer ID: {getReviewerId(selectedReviewer)}
              </span>
            </div>

            <button
              className="reviewer-close"
              onClick={() => setSelectedReviewer(null)}
            >
              Close ×
            </button>
          </div>

          <div className="reviewer-profile-grid">
            <div>
              <span>Email</span>
              <strong>
                {selectedReviewer.email ?? "Not available"}
              </strong>
            </div>

            <div>
              <span>Role</span>
              <strong>
                {selectedReviewer.role ??
                  selectedReviewer.reviewer_role ??
                  "Reviewer"}
              </strong>
            </div>

            <div>
              <span>Status</span>
              <strong>{getStatus(selectedReviewer)}</strong>
            </div>

            <div>
              <span>Assignment count</span>
              <strong>{selectedAssignments.length}</strong>
            </div>

            <div>
              <span>Department</span>
              <strong>
                {selectedReviewer.department ?? "Not available"}
              </strong>
            </div>

            <div>
              <span>Maximum active cases</span>
              <strong>
                {selectedReviewer.max_active_cases ?? "Not available"}
              </strong>
            </div>
          </div>

          <div className="reviewer-detail-columns">
            <div>
              <h3>Assigned cases</h3>

              {selectedAssignments.length === 0 ? (
                <p className="reviewer-no-data">
                  No assignment records returned for this reviewer.
                </p>
              ) : (
                selectedAssignments.map((item, index) => (
                  <div
                    className="reviewer-record"
                    key={item.assignment_id ?? item.id ?? index}
                  >
                    <strong>{getAssignmentCaseId(item)}</strong>
                    <span>
                      {item.assignment_status ??
                        item.status ??
                        "Assignment recorded"}
                    </span>
                  </div>
                ))
              )}
            </div>

            <div>
              <h3>Eligibility verification</h3>
              <p className="reviewer-no-data">
                Reviewer eligibility and conflict checks are performed
                for a specific case through the backend eligibility API.
                Select a case and reviewer to perform that check.
              </p>
            </div>
          </div>

          <div className="reviewer-readonly-note">
            Reviewer assignment changes are disabled in this view.
            Assignments must pass backend workload and conflict validation.
          </div>
        </section>
      )}
    </main>
  );
}
