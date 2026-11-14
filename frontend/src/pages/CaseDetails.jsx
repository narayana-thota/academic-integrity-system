
import { useEffect, useState } from "react";
import {
  fetchCase,
  fetchCaseTimeline,
} from "../services/api";

import CaseOverview from "../components/case-details/CaseOverview";
import CaseTimeline from "../components/case-details/CaseTimeline";
import EvidencePanel from "../components/case-details/EvidencePanel";
import ReviewerPanel from "../components/case-details/ReviewerPanel";
import DecisionPanel from "../components/case-details/DecisionPanel";

import "../styles/case-details.css";

function getArray(value, keys = []) {
  if (Array.isArray(value)) return value;

  for (const key of keys) {
    if (Array.isArray(value?.[key])) {
      return value[key];
    }
  }

  return [];
}

function formatDate(value) {
  if (!value) return "Date unavailable";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatLabel(value) {
  return String(value || "UNKNOWN")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function AppealPanel({ appeals = [] }) {
  return (
    <section className="detail-card">
      <div className="detail-card-heading">
        <div>
          <p className="eyebrow">LEARNER REVIEW</p>
          <h2>Appeal history</h2>
        </div>

        <span className="count-label">
          {appeals.length} records
        </span>
      </div>

      {appeals.length === 0 ? (
        <div className="empty-detail">
          No appeal records are available for this case.
        </div>
      ) : (
        <div className="decision-list">
          {appeals.map((appeal, index) => (
            <article
              className="decision-item"
              key={appeal.appeal_id ?? index}
            >
              <div>
                <strong>
                  {appeal.appeal_id || `Appeal ${index + 1}`}
                </strong>

                <span className="decision-stage">
                  Status: {formatLabel(appeal.appeal_status)}
                </span>

                <p>
                  <strong>Outcome:</strong>{" "}
                  {formatLabel(appeal.outcome)}
                </p>

                <p>
                  <strong>Appeal reason:</strong>{" "}
                  {appeal.appeal_reason ||
                    "No appeal reason provided."}
                </p>

                <p>
                  <strong>Submitted:</strong>{" "}
                  {formatDate(appeal.submitted_at)}
                </p>

                <p>
                  <strong>Resolved:</strong>{" "}
                  {formatDate(appeal.resolved_at)}
                </p>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default function CaseDetails({ caseId, onBack }) {
  const [caseData, setCaseData] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadCaseDetails() {
      try {
        setLoading(true);
        setError("");
        setCaseData(null);
        setTimeline([]);

        const [caseResponse, timelineResponse] = await Promise.all([
          fetchCase(caseId),
          fetchCaseTimeline(caseId),
        ]);

        if (!active) return;

        const details =
          caseResponse?.case ??
          caseResponse?.data?.case ??
          caseResponse?.data ??
          caseResponse;

        const events = getArray(timelineResponse, [
          "items",
          "events",
          "timeline",
          "data",
        ]);

        setCaseData(details);
        setTimeline(events);
      } catch (err) {
        if (active) {
          setError(
            err?.response?.data?.detail ??
              err?.message ??
              "Unable to load this case."
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    if (caseId) {
      loadCaseDetails();
    } else {
      setError("No case ID was provided.");
      setLoading(false);
    }

    return () => {
      active = false;
    };
  }, [caseId]);

  if (loading) {
    return (
      <main className="case-details-page">
        <button className="back-button" onClick={onBack}>
          ← Back to cases
        </button>

        <div className="details-message">
          <div className="details-loader" />
          <p>Loading case investigation workspace...</p>
        </div>
      </main>
    );
  }

  if (error || !caseData) {
    return (
      <main className="case-details-page">
        <button className="back-button" onClick={onBack}>
          ← Back to cases
        </button>

        <div className="details-error">
          <h2>Unable to open case</h2>
          <p>{error || "The requested case was not found."}</p>

          <button
            className="details-retry"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      </main>
    );
  }

  // Extract records using the actual backend response fields.
  const evidence = getArray(caseData, ["evidence"]);

  const reviewers = getArray(caseData, ["assignments"]);

  const decisions = getArray(caseData, ["decisions"]);

  const appeals = getArray(caseData, ["appeals"]);

  return (
    <main className="case-details-page">
      <div className="details-topbar">
        <button className="back-button" onClick={onBack}>
          <span>←</span> Back to cases
        </button>

        <span className="details-reference">
          CASE / {caseId}
        </span>
      </div>

      <header className="details-header">
        <div>
          <p className="eyebrow">
            ACADEMIC INTEGRITY / INVESTIGATION
          </p>

          <h1>Case investigation</h1>

          <p>
            Review case information, supporting evidence,
            reviewer activity, decisions and appeals.
          </p>
        </div>

        <div className="read-only-label">
          <span />
          Read-only workspace
        </div>
      </header>

      <div className="details-layout">
        <div className="details-main-column">
          <CaseOverview caseData={caseData} />

          <CaseTimeline events={timeline} />

          <EvidencePanel evidence={evidence} />
        </div>

        <aside className="details-side-column">
          <ReviewerPanel reviewers={reviewers} />

          <DecisionPanel decisions={decisions} />

          <AppealPanel appeals={appeals} />

          <div className="integrity-note">
            <span>i</span>

            <div>
              <strong>Audit integrity</strong>

              <p>
                This workspace displays recorded case information.
                No case records are modified by viewing this page.
              </p>
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}
