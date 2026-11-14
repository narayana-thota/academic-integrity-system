
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

export default function DecisionPanel({ decisions = [] }) {
  return (
    <section className="detail-card">
      <div className="detail-card-heading">
        <div>
          <p className="eyebrow">CASE OUTCOME</p>
          <h2>Decision history</h2>
        </div>
        <span className="count-label">{decisions.length} records</span>
      </div>

      {decisions.length === 0 ? (
        <div className="empty-detail">
          No decision records are available.
        </div>
      ) : (
        <div className="decision-list">
          {decisions.map((decision, index) => (
            <article
              className="decision-item"
              key={decision.decision_id ?? index}
            >
              <div>
                <strong>
                  {decision.decision_type?.replaceAll("_", " ")}
                </strong>

                <span className="decision-stage">
                  {decision.decision_stage?.replaceAll("_", " ")}
                </span>

                <p>
                  Reviewer ID: {decision.reviewer_id ?? "—"}
                </p>

                <p>
                  {decision.rationale || "No rationale provided."}
                </p>

                <time>{formatDate(decision.decided_at)}</time>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
