
import { CasePriority, CaseStatus } from "../cases/CasePriority";

function formatDate(value) {
  if (!value) return "Not available";

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

function Detail({ label, value }) {
  return (
    <div className="detail-item">
      <span>{label}</span>
      <strong>{value ?? "Not available"}</strong>
    </div>
  );
}

export default function CaseOverview({ caseData }) {
  const data = caseData || {};

  const caseId =
    data.case_id ?? data.id ?? data.case_number ?? "—";

  const learner =
    data.learner_name ??
    data.student_name ??
    data.learner_code ??
    data.learner_id ??
    "Not available";

  const assessment =
    data.assessment_title ??
    data.assessment_name ??
    data.assessment_id ??
    "Not available";

  const similarity =
    data.similarity_score ??
    data.similarity_percentage ??
    data.similarity ??
    null;

  const caseStatus =
    data.case_status ?? data.status ?? "UNKNOWN";

  const assignments = Array.isArray(data.assignments)
    ? data.assignments
    : [];

  const assignedReviewer =
    assignments.find(
      (item) => item.assignment_status === "ACTIVE"
    ) ?? assignments[0];

  const reviewerName =
    assignedReviewer?.reviewer_name ??
    data.reviewer_name ??
    data.assigned_reviewer ??
    (assignedReviewer?.reviewer_id
      ? `Reviewer ${String(assignedReviewer.reviewer_id).padStart(3, "0")}`
      : data.reviewer_id
        ? `Reviewer ${String(data.reviewer_id).padStart(3, "0")}`
        : "Not available");

  return (
    <section className="detail-card">
      <div className="detail-card-heading">
        <div>
          <p className="eyebrow">CASE SUMMARY</p>
          <h2>Case overview</h2>
        </div>

        <div className="case-badges">
          <CasePriority priority={data.priority} />
          <CaseStatus status={caseStatus} />
        </div>
      </div>

      <div className="case-detail-grid">
        <Detail
          label="Case ID"
          value={caseId}
        />

        <Detail
          label="Learner"
          value={learner}
        />

        <Detail
          label="Assessment"
          value={assessment}
        />

        <Detail
          label="Similarity score"
          value={
            similarity == null
              ? "Not available"
              : `${Number(similarity).toFixed(2)}%`
          }
        />

        <Detail
          label="Created"
          value={formatDate(data.created_at ?? data.created_on)}
        />

        <Detail
          label="Due date"
          value={formatDate(data.due_at ?? data.due_date ?? data.deadline)}
        />

        <Detail
          label="Closed"
          value={formatDate(data.closed_at ?? data.resolved_at)}
        />

        <Detail
          label="Assigned reviewer"
          value={reviewerName}
        />
      </div>

      {data.closure_reason && (
        <div className="case-description">
          <span>Closure reason</span>
          <p>{data.closure_reason.replaceAll("_", " ")}</p>
        </div>
      )}

      {data.description && (
        <div className="case-description">
          <span>Description</span>
          <p>{data.description}</p>
        </div>
      )}
    </section>
  );
}
