import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ClipboardList,
  RefreshCw,
  X,
} from "lucide-react";

import { fetchCases, fetchCase } from "../services/api";
import CaseFilters from "../components/cases/CaseFilters";
import CasesTable from "../components/cases/CasesTable";
import Pagination from "../components/cases/Pagination";
import { CasePriority, CaseStatus } from "../components/cases/CasePriority";

import "../styles/cases.css";

const PAGE_SIZE = 20;

function CasePreview({ caseData, onClose }) {
  if (!caseData) return null;

  const fields = [
    ["Case ID", caseData.case_id],
    ["Submission ID", caseData.submission_id],
    ["Report ID", caseData.report_id],
    ["Learner", caseData.learner_name],
    ["Learner code", caseData.learner_code],
    ["Similarity score", caseData.similarity_score != null
      ? `${Number(caseData.similarity_score).toFixed(1)}%`
      : "—"],
    ["Created", caseData.created_at
      ? new Date(caseData.created_at).toLocaleString("en-IN")
      : "—"],
    ["Due date", caseData.due_at
      ? new Date(caseData.due_at).toLocaleString("en-IN")
      : "—"],
  ];

  return (
    <div className="case-preview-backdrop" onClick={onClose}>
      <section
        className="case-preview"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="preview-heading">
          <div>
            <p className="eyebrow">CASE INFORMATION</p>
            <h2>Case #{caseData.case_id}</h2>
          </div>
          <button onClick={onClose} className="preview-close" aria-label="Close">
            <X size={20} />
          </button>
        </div>

        <div className="preview-tags">
          <CasePriority priority={caseData.priority} />
          <CaseStatus status={caseData.case_status} />
        </div>

        <div className="preview-grid">
          {fields.map(([label, value]) => (
            <div className="preview-field" key={label}>
              <small>{label}</small>
              <strong>{value ?? "—"}</strong>
            </div>
          ))}
        </div>

        <p className="preview-note">
          Similarity scores are indicators for human review and do not establish
          academic misconduct.
        </p>
      </section>
    </div>
  );
}

export default function Cases({ onOpenCase }) {
  const [cases, setCases] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  const [search, setSearch] = useState("");
  const [priority, setPriority] = useState("ALL");
  const [status, setStatus] = useState("ALL");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedCase, setSelectedCase] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const loadCases = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetchCases(page, PAGE_SIZE);

      const records = Array.isArray(response)
        ? response
        : response?.cases || response?.items || [];

      setCases(records);
      setTotal(
        Number(response?.total ?? response?.total_count ?? records.length)
      );
    } catch (err) {
      setError(err.message || "Unable to load cases.");
      setCases([]);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    loadCases();
  }, [loadCases]);

  const filteredCases = useMemo(() => {
    const term = search.trim().toLowerCase();

    return cases.filter((item) => {
      const matchesSearch =
        !term ||
        String(item.case_id ?? "").toLowerCase().includes(term) ||
        String(item.learner_name ?? "").toLowerCase().includes(term) ||
        String(item.learner_code ?? "").toLowerCase().includes(term) ||
        String(item.submission_id ?? "").toLowerCase().includes(term);

      const matchesPriority =
        priority === "ALL" ||
        String(item.priority || "").toUpperCase() === priority;

      const matchesStatus =
        status === "ALL" ||
        String(item.case_status || "").toUpperCase() === status;

      return matchesSearch && matchesPriority && matchesStatus;
    });
  }, [cases, search, priority, status]);

  const handleOpenCase = (caseId) => {
    if (onOpenCase) {
      onOpenCase(caseId);
    } else {
      openCase(caseId);
    }
  };

  const openCase = async (caseId) => {
    setPreviewLoading(true);
    setSelectedCase(null);

    try {
      const data = await fetchCase(caseId);
      setSelectedCase(data);
    } catch (err) {
      setError(err.message || "Unable to load case details.");
    } finally {
      setPreviewLoading(false);
    }
  };

  const clearFilters = () => {
    setSearch("");
    setPriority("ALL");
    setStatus("ALL");
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <main className="cases-page">
      <div className="cases-heading">
        <div>
          <p className="eyebrow">ACADEMIC INTEGRITY / CASE MANAGEMENT</p>
          <h1>Case management</h1>
          <p className="cases-subtitle">
            Review, track and manage academic integrity cases.
          </p>
        </div>

        <button
          className="cases-refresh"
          onClick={loadCases}
          disabled={loading}
        >
          <RefreshCw size={15} className={loading ? "spin-icon" : ""} />
          Refresh
        </button>
      </div>

      <section className="cases-summary">
        <div className="cases-summary-icon">
          <ClipboardList size={22} />
        </div>
        <div>
          <span>Total registered cases</span>
          <strong>{total.toLocaleString("en-IN")}</strong>
        </div>
        <div className="cases-summary-divider" />
        <div className="cases-summary-info">
          <span>Current page</span>
          <strong>{page} of {totalPages}</strong>
        </div>
        <div className="cases-summary-info">
          <span>Displayed records</span>
          <strong>{filteredCases.length}</strong>
        </div>
      </section>

      <section className="cases-content panel">
        <div className="cases-section-heading">
          <div>
            <p className="eyebrow">INVESTIGATION RECORDS</p>
            <h2>All cases</h2>
          </div>
          <span className="cases-count">
            {filteredCases.length} on this page
          </span>
        </div>

        <CaseFilters
          search={search}
          setSearch={setSearch}
          priority={priority}
          setPriority={setPriority}
          status={status}
          setStatus={setStatus}
          onClear={clearFilters}
        />

        {loading ? (
          <div className="cases-state">
            <span className="loading-spinner" />
            <p>Loading case records...</p>
          </div>
        ) : error ? (
          <div className="cases-state cases-error">
            <AlertCircle size={25} />
            <h3>Unable to load cases</h3>
            <p>{error}</p>
            <button className="cases-refresh" onClick={loadCases}>
              <RefreshCw size={15} /> Try again
            </button>
          </div>
        ) : (
          <>
            <CasesTable
              cases={filteredCases}
              onOpenCase={handleOpenCase}
            />

            <Pagination
              page={page}
              totalPages={totalPages}
              total={total}
              pageSize={PAGE_SIZE}
              onPageChange={setPage}
            />
          </>
        )}
      </section>

      {previewLoading && (
        <div className="preview-loading">
          <span className="loading-spinner" />
          <p>Loading case details...</p>
        </div>
      )}

      {selectedCase && (
        <CasePreview
          caseData={selectedCase}
          onClose={() => setSelectedCase(null)}
        />
      )}
    </main>
  );
}