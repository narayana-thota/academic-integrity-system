
import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  Eye,
  FileText,
  LoaderCircle,
  RefreshCw,
  Search,
  X,
} from "lucide-react";

import { fetchDecisions, fetchDecision } from "../services/api";
import "../styles/decisions.css";

const PAGE_SIZE = 10;

// Extract decision records from API response
function getDecisionList(response) {
  if (Array.isArray(response)) return response;

  return (
    response?.decisions ??
    response?.items ??
    response?.results ??
    response?.data ??
    []
  );
}

// Extract total record count
function getTotal(response, records) {
  return (
    response?.total ??
    response?.total_count ??
    response?.count ??
    records.length
  );
}

// Format date and time using Indian Standard Time
function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

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

// Decision field helpers
function getDecisionId(decision) {
  return (
    decision?.decision_id ??
    decision?.id ??
    decision?.decisionId ??
    "—"
  );
}

function getDecisionType(decision) {
  return (
    decision?.decision_type ??
    decision?.type ??
    "Not specified"
  );
}

function getDecisionStage(decision) {
  return (
    decision?.decision_stage ??
    decision?.stage ??
    "Not specified"
  );
}

function getCaseId(decision) {
  return decision?.case_id ?? decision?.caseId ?? "—";
}

function getReviewerId(decision) {
  return decision?.reviewer_id ?? decision?.reviewerId ?? "—";
}

function getReviewerName(decision) {
  return (
    decision?.reviewer_name ??
    decision?.reviewer?.name ??
    (getReviewerId(decision) !== "—"
      ? `Reviewer ${String(getReviewerId(decision)).padStart(3, "0")}`
      : "Not assigned")
  );
}

function getDecisionDate(decision) {
  return (
    decision?.decided_at ??
    decision?.created_at ??
    decision?.decision_date ??
    decision?.createdAt ??
    null
  );
}

function getRationale(decision) {
  return (
    decision?.rationale ??
    decision?.reason ??
    "No rationale provided."
  );
}

// Reusable decision badge
function DecisionBadge({ value }) {
  const normalized = String(value || "unknown")
    .toLowerCase()
    .replaceAll("_", " ");

  return (
    <span
      className={`decision-badge decision-badge--${normalized.replaceAll(
        " ",
        "-"
      )}`}
    >
      {normalized}
    </span>
  );
}

// Reusable statistics card
function StatCard({ label, value, description, icon: Icon }) {
  return (
    <article className="decision-stat-card">
      <div className="decision-stat-top">
        <span>{label}</span>

        <div className="decision-stat-icon">
          <Icon size={18} />
        </div>
      </div>

      <strong>{value}</strong>
      <small>{description}</small>
    </article>
  );
}

// Decision detail modal
function DecisionDetails({ decision, onClose }) {
  const [details, setDetails] = useState(decision);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    const loadDetails = async () => {
      const id = getDecisionId(decision);

      if (id === "—") {
        setLoading(false);
        return;
      }

      try {
        const result = await fetchDecision(id);

        if (active) {
          setDetails(result?.decision ?? result?.data ?? result);
        }
      } catch (err) {
        if (active) {
          setError(
            err.message || "Unable to load decision details."
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    loadDetails();

    return () => {
      active = false;
    };
  }, [decision]);

  return (
    <div
      className="decision-modal-backdrop"
      onClick={onClose}
    >
      <section
        className="decision-detail-panel"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="decision-detail-title"
      >
        <header className="decision-detail-header">
          <div>
            <span className="eyebrow">DECISION RECORD</span>

            <h2 id="decision-detail-title">
              Decision #{getDecisionId(details)}
            </h2>
          </div>

          <button
            className="decision-icon-button"
            onClick={onClose}
            aria-label="Close decision details"
          >
            <X size={20} />
          </button>
        </header>

        {loading ? (
          <div className="decision-detail-loading">
            <LoaderCircle className="spin" size={24} />
            <span>Loading decision details...</span>
          </div>
        ) : (
          <>
            {error && (
              <div className="decision-inline-notice">
                <AlertCircle size={17} />
                {error} Showing available list information instead.
              </div>
            )}

            <div className="decision-detail-grid">
              <div>
                <span>Case ID</span>
                <strong>{getCaseId(details)}</strong>
              </div>

              <div>
                <span>Reviewer</span>
                <strong>{getReviewerName(details)}</strong>
              </div>

              <div>
                <span>Reviewer ID</span>
                <strong>#{getReviewerId(details)}</strong>
              </div>

              <div>
                <span>Decision type</span>
                <strong>
                  <DecisionBadge value={getDecisionType(details)} />
                </strong>
              </div>

              <div>
                <span>Decision stage</span>
                <strong>
                  <DecisionBadge value={getDecisionStage(details)} />
                </strong>
              </div>

              <div>
                <span>Decision date</span>
                <strong>{formatDate(getDecisionDate(details))}</strong>
              </div>

              <div>
                <span>Decision ID</span>
                <strong>#{getDecisionId(details)}</strong>
              </div>

              {details?.supersedes_decision_id != null && (
                <div>
                  <span>Supersedes decision</span>
                  <strong>
                    #{details.supersedes_decision_id}
                  </strong>
                </div>
              )}
            </div>

            <div className="decision-rationale">
              <div className="decision-rationale-title">
                <FileText size={18} />
                <h3>Decision rationale</h3>
              </div>

              <p>{getRationale(details)}</p>
            </div>

            <p className="decision-readonly-note">
              <CheckCircle2 size={15} />
              This is a read-only view of the recorded decision.
            </p>
          </>
        )}
      </section>
    </div>
  );
}

// Main Decisions page
export default function Decisions() {
  const [records, setRecords] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedDecision, setSelectedDecision] = useState(null);

  const [search, setSearch] = useState("");
  const [caseFilter, setCaseFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [stageFilter, setStageFilter] = useState("");

  // Fetch decisions from backend
  const loadDecisions = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetchDecisions(page, PAGE_SIZE, {
        case_id: caseFilter.trim(),
        decision_type: typeFilter,
        decision_stage: stageFilter,
      });

      const list = getDecisionList(response);

      setRecords(list);
      setTotal(getTotal(response, list));
    } catch (err) {
      setError(
        err.message || "Unable to load decisions."
      );

      setRecords([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDecisions();
  }, [page, caseFilter, typeFilter, stageFilter]);

  // Search currently loaded page
  const filteredRecords = useMemo(() => {
    const term = search.trim().toLowerCase();

    if (!term) return records;

    return records.filter((decision) => {
      const searchable = [
        getDecisionId(decision),
        getCaseId(decision),
        getReviewerId(decision),
        getReviewerName(decision),
        getDecisionType(decision),
        getDecisionStage(decision),
        getRationale(decision),
      ]
        .join(" ")
        .toLowerCase();

      return searchable.includes(term);
    });
  }, [records, search]);

  // Available decision types
  const decisionTypes = useMemo(
    () =>
      [
        ...new Set(
          records
            .map(getDecisionType)
            .filter((value) => value !== "Not specified")
        ),
      ],
    [records]
  );

  // Available decision stages
  const decisionStages = useMemo(
    () =>
      [
        ...new Set(
          records
            .map(getDecisionStage)
            .filter((value) => value !== "Not specified")
        ),
      ],
    [records]
  );

  const currentPageCount = records.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  // Reset filters
  const resetFilters = () => {
    setSearch("");
    setCaseFilter("");
    setTypeFilter("");
    setStageFilter("");
    setPage(1);
  };

  return (
    <main className="decisions-page">
      {/* Page heading */}
      <div className="decisions-heading">
        <div>
          <p className="eyebrow">
            ACADEMIC INTEGRITY / OVERSIGHT
          </p>

          <h1>Decisions</h1>

          <p className="dashboard-subtitle">
            Review recorded outcomes and decision rationales across
            integrity cases.
          </p>
        </div>

        <button
          className="decision-refresh-button"
          onClick={loadDecisions}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={loading ? "spin" : ""}
          />
          Refresh
        </button>
      </div>

      {/* Statistics */}
      <section className="decision-stats-grid">
        <StatCard
          label="Total decisions"
          value={total}
          description="Records returned by the API"
          icon={ClipboardCheck}
        />

        <StatCard
          label="Visible on this page"
          value={currentPageCount}
          description={`Page ${page} of ${totalPages}`}
          icon={FileText}
        />

        <StatCard
          label="Decision types"
          value={decisionTypes.length}
          description="Types on the current page"
          icon={ArrowUpRight}
        />

        <StatCard
          label="Decision stages"
          value={decisionStages.length}
          description="Stages on the current page"
          icon={ArrowDownRight}
        />
      </section>

      {/* Decision records */}
      <section className="decision-content-card">
        <div className="decision-content-heading">
          <div>
            <h2>Decision records</h2>
            <p>Browse and inspect recorded decisions.</p>
          </div>

          <span className="decision-record-count">
            {total} records
          </span>
        </div>

        {/* Filters */}
        <div className="decision-filters">
          <label className="decision-search">
            <Search size={17} />

            <input
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search decisions or reviewers..."
            />
          </label>

          <input
            className="decision-filter-input"
            value={caseFilter}
            onChange={(event) => {
              setPage(1);
              setCaseFilter(event.target.value);
            }}
            placeholder="Filter by case ID"
          />

          <select
            className="decision-filter-select"
            value={typeFilter}
            onChange={(event) => {
              setPage(1);
              setTypeFilter(event.target.value);
            }}
          >
            <option value="">All decision types</option>

            {decisionTypes.map((type) => (
              <option key={type} value={type}>
                {type.replaceAll("_", " ")}
              </option>
            ))}
          </select>

          <select
            className="decision-filter-select"
            value={stageFilter}
            onChange={(event) => {
              setPage(1);
              setStageFilter(event.target.value);
            }}
          >
            <option value="">All stages</option>

            {decisionStages.map((stage) => (
              <option key={stage} value={stage}>
                {stage.replaceAll("_", " ")}
              </option>
            ))}
          </select>

          <button
            className="decision-reset-button"
            onClick={resetFilters}
          >
            Reset
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="decision-error">
            <AlertCircle size={18} />

            <span>{error}</span>

            <button onClick={loadDecisions}>
              Retry
            </button>
          </div>
        )}

        {/* Loading */}
        {loading ? (
          <div className="decision-empty-state">
            <LoaderCircle
              className="spin"
              size={26}
            />

            <p>Loading decision records...</p>
          </div>
        ) : !error && filteredRecords.length === 0 ? (
          <div className="decision-empty-state">
            <ClipboardCheck size={30} />

            <h3>No decisions found</h3>

            <p>Try changing your search or filters.</p>
          </div>
        ) : (
          /* Decisions table */
          <div className="decision-table-wrap">
            <table className="decision-table">
              <thead>
                <tr>
                  <th>Decision</th>
                  <th>Case</th>
                  <th>Reviewer</th>
                  <th>Decision type</th>
                  <th>Stage</th>
                  <th>Date & time</th>
                  <th></th>
                </tr>
              </thead>

              <tbody>
                {filteredRecords.map((decision, index) => (
                  <tr
                    key={
                      getDecisionId(decision) === "—"
                        ? index
                        : getDecisionId(decision)
                    }
                  >
                    <td>
                      <strong className="decision-id">
                        #{getDecisionId(decision)}
                      </strong>
                    </td>

                    <td>
                      <span className="decision-case-id">
                        {getCaseId(decision)}
                      </span>
                    </td>

                    <td>
                      <div className="decision-reviewer-cell">
                        <strong>
                          {getReviewerName(decision)}
                        </strong>

                        <small>
                          ID: {getReviewerId(decision)}
                        </small>
                      </div>
                    </td>

                    <td>
                      <DecisionBadge
                        value={getDecisionType(decision)}
                      />
                    </td>

                    <td>
                      <DecisionBadge
                        value={getDecisionStage(decision)}
                      />
                    </td>

                    <td>
                      {formatDate(getDecisionDate(decision))}
                    </td>

                    <td>
                      <button
                        className="decision-view-button"
                        onClick={() =>
                          setSelectedDecision(decision)
                        }
                        aria-label={`View decision ${getDecisionId(
                          decision
                        )}`}
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

        {/* Pagination */}
        {!loading && total > 0 && (
          <div className="decision-pagination">
            <span>
              Page {page} of {totalPages} · {total} total records
            </span>

            <div>
              <button
                onClick={() =>
                  setPage((current) => Math.max(1, current - 1))
                }
                disabled={page <= 1 || loading}
                aria-label="Previous page"
              >
                <ChevronLeft size={17} />
              </button>

              <button
                onClick={() =>
                  setPage((current) =>
                    Math.min(totalPages, current + 1)
                  )
                }
                disabled={page >= totalPages || loading}
                aria-label="Next page"
              >
                <ChevronRight size={17} />
              </button>
            </div>
          </div>
        )}
      </section>

      {/* Decision detail modal */}
      {selectedDecision && (
        <DecisionDetails
          decision={selectedDecision}
          onClose={() => setSelectedDecision(null)}
        />
      )}
    </main>
  );
}
