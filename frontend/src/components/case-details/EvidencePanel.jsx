
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

export default function EvidencePanel({ evidence = [] }) {
  return (
    <section className="detail-card">
      <div className="detail-card-heading">
        <div>
          <p className="eyebrow">SUPPORTING MATERIAL</p>
          <h2>Evidence records</h2>
        </div>
        <span className="count-label">{evidence.length} items</span>
      </div>

      {evidence.length === 0 ? (
        <div className="empty-detail">
          No evidence records are available for this case.
        </div>
      ) : (
        <div className="evidence-list">
          {evidence.map((item, index) => (
            <article
              className="evidence-item"
              key={item.evidence_id ?? index}
            >
              <div className="evidence-icon">
                <span>EV</span>
              </div>

              <div className="evidence-info">
                <strong>{item.evidence_id || `Evidence ${index + 1}`}</strong>
                <span>{item.evidence_type || "Evidence record"}</span>
                <p>{item.description || "No description available."}</p>

                <div className="evidence-metadata">
                  <span>Version {item.version ?? "—"}</span>
                  <span>Source: {item.added_by || "—"}</span>
                  <span>{formatDate(item.created_at)}</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
