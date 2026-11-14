
import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Eye,
  FileText,
  LoaderCircle,
  RefreshCw,
  Search,
  X,
} from "lucide-react";

import { fetchAppeals } from "../services/api";
import "../styles/appeals.css";

const PAGE_SIZE = 10;

function getAppealList(response) {
  if (Array.isArray(response)) return response;

  return (
    response?.items ??
    response?.appeals ??
    response?.results ??
    response?.data ??
    []
  );
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return String(value);

  return date.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}

function AppealStatus({ status }) {
  const value = String(status || "UNKNOWN")
    .toLowerCase()
    .replaceAll("_", "-");

  return (
    <span className={`appeal-badge appeal-badge--${value}`}>
      {String(status || "Unknown").replaceAll("_", " ")}
    </span>
  );
}

function AppealOutcome({ outcome }) {
  if (!outcome) {
    return <span className="appeal-outcome-empty">Pending</span>;
  }

  const value = String(outcome).toLowerCase();

  return (
    <span className={`appeal-outcome appeal-outcome--${value}`}>
      {String(outcome).replaceAll("_", " ")}
    </span>
  );
}

function StatCard({ label, value, description, icon: Icon }) {
  return (
    <article className="appeal-stat-card">
      <div className="appeal-stat-top">
        <span>{label}</span>
        <div className="appeal-stat-icon">
          <Icon size={18} />
        </div>
      </div>

      <strong>{value}</strong>
      <small>{description}</small>
    </article>
  );
}

function AppealDetails({ appeal, onClose }) {
  return (
    <div className="appeal-modal-backdrop" onClick={onClose}>
      <section
        className="appeal-detail-panel"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="appeal-detail-title"
      >
        <header className="appeal-detail-header">
          <div>
            <span className="eyebrow">APPEAL RECORD</span>
            <h2 id="appeal-detail-title">
              {appeal.appeal_id}
            </h2>
          </div>

          <button
            className="appeal-icon-button"
            onClick={onClose}
            aria-label="Close appeal details"
          >
            <X size={20} />
          </button>
        </header>

        <div className="appeal-detail-status">
          <AppealStatus status={appeal.appeal_status} />
          <AppealOutcome outcome={appeal.outcome} />
        </div>

        <div className="appeal-detail-grid">
          <div>
            <span>Appeal ID</span>
            <strong>{appeal.appeal_id || "—"}</strong>
          </div>

          <div>
            <span>Case ID</span>
            <strong>{appeal.case_id || "—"}</strong>
          </div>

          <div>
            <span>Learner ID</span>
            <strong>{appeal.submitted_by_learner_id ?? "—"}</strong>
          </div>

          <div>
            <span>Original decision ID</span>
            <strong>
              {appeal.original_decision_id ?? "—"}
            </strong>
          </div>

          <div>
            <span>Submitted at</span>
            <strong>{formatDate(appeal.submitted_at)}</strong>
          </div>

          <div>
            <span>Due date</span>
            <strong>{formatDate(appeal.due_at)}</strong>
          </div>

          <div>
            <span>Resolved at</span>
            <strong>{formatDate(appeal.resolved_at)}</strong>
          </div>

          <div>
            <span>Outcome</span>
            <strong>
              {appeal.outcome
                ? appeal.outcome.replaceAll("_", " ")
                : "Pending"}
            </strong>
          </div>
        </div>

        <div className="appeal-reason-card">
          <div className="appeal-reason-title">
            <FileText size={18} />
            <h3>Appeal reason</h3>
          </div>

          <p>
            {appeal.appeal_reason || "No appeal reason provided."}
          </p>
        </div>

        <p className="appeal-readonly-note">
          <CheckCircle2 size={15} />
          This is a read-only view of the recorded appeal.
        </p>
      </section>
    </div>
  );
}

export default function Appeals() {
  const [appeals, setAppeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [outcomeFilter, setOutcomeFilter] = useState("");

  const [selectedAppeal, setSelectedAppeal] = useState(null);

  const loadAppeals = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetchAppeals();
      setAppeals(getAppealList(response));
    } catch (err) {
      setError(err.message || "Unable to load appeals.");
      setAppeals([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppeals();
  }, []);

  const total = appeals.length;

  const pendingCount = appeals.filter(
    (appeal) =>
      String(appeal.appeal_status || "").toUpperCase() === "PENDING"
  ).length;

  const resolvedCount = appeals.filter(
    (appeal) =>
      String(appeal.appeal_status || "").toUpperCase() === "RESOLVED"
  ).length;

  const overturnedCount = appeals.filter(
    (appeal) =>
      String(appeal.outcome || "").toUpperCase() === "OVERTURNED"
  ).length;

  const filteredAppeals = useMemo(() => {
    const term = search.trim().toLowerCase();

    return appeals.filter((appeal) => {
      const matchesSearch =
        !term ||
        [
          appeal.appeal_id,
          appeal.case_id,
          appeal.submitted_by_learner_id,
          appeal.original_decision_id,
          appeal.appeal_reason,
          appeal.outcome,
          appeal.appeal_status,
        ]
          .join(" ")
          .toLowerCase()
          .includes(term);

      const matchesStatus =
        !statusFilter ||
        String(appeal.appeal_status || "").toUpperCase() === statusFilter;

      const matchesOutcome =
        !outcomeFilter ||
        String(appeal.outcome || "").toUpperCase() === outcomeFilter;

      return matchesSearch && matchesStatus && matchesOutcome;
    });
  }, [appeals, search, statusFilter, outcomeFilter]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredAppeals.length / PAGE_SIZE)
  );

  const currentPage = Math.min(page, totalPages);

  const visibleAppeals = filteredAppeals.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const resetFilters = () => {
    setSearch("");
    setStatusFilter("");
    setOutcomeFilter("");
    setPage(1);
  };

  return (
    <main className="appeals-page">
      <div className="appeals-heading">
        <div>
          <p className="eyebrow">ACADEMIC INTEGRITY / DUE PROCESS</p>
          <h1>Appeals</h1>
          <p className="dashboard-subtitle">
            Review learner appeals, monitor their status and inspect recorded outcomes.
          </p>
        </div>

        <button
          className="appeal-refresh-button"
          onClick={loadAppeals}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={loading ? "appeal-spin" : ""}
          />
          Refresh
        </button>
      </div>

      <section className="appeal-stats-grid">
        <StatCard
          label="Total appeals"
          value={total}
          description="All loaded appeal records"
          icon={FileText}
        />

        <StatCard
          label="Pending appeals"
          value={pendingCount}
          description="Awaiting resolution"
          icon={Clock3}
        />

        <StatCard
          label="Resolved appeals"
          value={resolvedCount}
          description="Resolution recorded"
          icon={CheckCircle2}
        />

        <StatCard
          label="Overturned"
          value={overturnedCount}
          description="Original decisions overturned"
          icon={CalendarDays}
        />
      </section>

      <section className="appeal-content-card">
        <div className="appeal-content-heading">
          <div>
            <h2>Appeal records</h2>
            <p>Search and inspect submitted appeals.</p>
          </div>

          <span className="appeal-record-count">
            {filteredAppeals.length} records
          </span>
        </div>

        <div className="appeal-filters">
          <label className="appeal-search">
            <Search size={17} />
            <input
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
              placeholder="Search appeal, case or learner..."
            />
          </label>

          <select
            className="appeal-filter-select"
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All statuses</option>
            <option value="PENDING">Pending</option>
            <option value="RESOLVED">Resolved</option>
          </select>

          <select
            className="appeal-filter-select"
            value={outcomeFilter}
            onChange={(event) => {
              setOutcomeFilter(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All outcomes</option>
            <option value="UPHELD">Upheld</option>
            <option value="OVERTURNED">Overturned</option>
            <option value="MODIFIED">Modified</option>
          </select>

          <button
            className="appeal-reset-button"
            onClick={resetFilters}
          >
            Reset
          </button>
        </div>

        {error && (
          <div className="appeal-error">
            <AlertCircle size={18} />
            <span>{error}</span>
            <button onClick={loadAppeals}>Retry</button>
          </div>
        )}

        {loading ? (
          <div className="appeal-empty-state">
            <LoaderCircle className="appeal-spin" size={26} />
            <p>Loading appeal records...</p>
          </div>
        ) : !error && visibleAppeals.length === 0 ? (
          <div className="appeal-empty-state">
            <FileText size={30} />
            <h3>No appeals found</h3>
            <p>Try changing your search or filters.</p>
          </div>
        ) : (
          <div className="appeal-table-wrap">
            <table className="appeal-table">
              <thead>
                <tr>
                  <th>Appeal ID</th>
                  <th>Case ID</th>
                  <th>Learner</th>
                  <th>Status</th>
                  <th>Outcome</th>
                  <th>Submitted</th>
                  <th>Due date</th>
                  <th></th>
                </tr>
              </thead>

              <tbody>
                {visibleAppeals.map((appeal) => (
                  <tr key={appeal.appeal_id}>
                    <td>
                      <strong className="appeal-id">
                        {appeal.appeal_id}
                      </strong>
                    </td>

                    <td>
                      <span className="appeal-case-id">
                        {appeal.case_id}
                      </span>
                    </td>

                    <td>
                      <span className="appeal-learner-id">
                        #{appeal.submitted_by_learner_id}
                      </span>
                    </td>

                    <td>
                      <AppealStatus status={appeal.appeal_status} />
                    </td>

                    <td>
                      <AppealOutcome outcome={appeal.outcome} />
                    </td>

                    <td>{formatDate(appeal.submitted_at)}</td>

                    <td>{formatDate(appeal.due_at)}</td>

                    <td>
                      <button
                        className="appeal-view-button"
                        onClick={() => setSelectedAppeal(appeal)}
                      >
                        <Eye size={16} />
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!loading && filteredAppeals.length > 0 && (
          <div className="appeal-pagination">
            <span>
              Page {currentPage} of {totalPages} ·{" "}
              {filteredAppeals.length} matching records
            </span>

            <div>
              <button
                onClick={() =>
                  setPage((value) => Math.max(1, value - 1))
                }
                disabled={currentPage <= 1}
                aria-label="Previous page"
              >
                <ChevronLeft size={17} />
              </button>

              <button
                onClick={() =>
                  setPage((value) =>
                    Math.min(totalPages, value + 1)
                  )
                }
                disabled={currentPage >= totalPages}
                aria-label="Next page"
              >
                <ChevronRight size={17} />
              </button>
            </div>
          </div>
        )}
      </section>

      {selectedAppeal && (
        <AppealDetails
          appeal={selectedAppeal}
          onClose={() => setSelectedAppeal(null)}
        />
      )}
    </main>
  );
}
