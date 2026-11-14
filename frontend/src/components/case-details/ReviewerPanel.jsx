
function formatDate(value) {
  if (!value) return "—";

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

export default function ReviewerPanel({ reviewers = [] }) {
  return (
    <section className="detail-card">
      <div className="detail-card-heading">
        <div>
          <p className="eyebrow">REVIEW OWNERSHIP</p>
          <h2>Reviewer assignments</h2>
        </div>
        <span className="count-label">{reviewers.length} records</span>
      </div>

      {reviewers.length === 0 ? (
        <div className="empty-detail">
          No reviewer assignment information is available.
        </div>
      ) : (
        <div className="reviewer-list">
          {reviewers.map((reviewer, index) => {
            const name = reviewer.reviewer_name || 
              `Reviewer ${reviewer.reviewer_id}`;

            const status = reviewer.assignment_status || "UNKNOWN";

            return (
              <article
                className="reviewer-item"
                key={reviewer.assignment_id ?? index}
              >
                <div className="reviewer-avatar">
                  {String(name).replace("Reviewer ", "").slice(0, 2)}
                </div>

                <div className="reviewer-info">
                  <strong>{name}</strong>
                  <span>Reviewer ID: {reviewer.reviewer_id ?? "—"}</span>
                  <span>
                    Assigned: {formatDate(reviewer.assigned_at)}
                  </span>
                  <span>
                    Completed: {formatDate(reviewer.ended_at)}
                  </span>
                </div>

                <span className="evidence-status">
                  {status.replaceAll("_", " ")}
                </span>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
