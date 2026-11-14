import SimilarityScore from "./SimilarityScore";

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString();
}

function formatLabel(value) {
  if (!value) return "Not available";

  return String(value).replaceAll("_", " ");
}

export default function SimilarityTable({
  reports,
  onSelect,
  selectedReportId,
}) {
  if (!reports.length) {
    return (
      <div className="similarity-empty">
        <div className="similarity-empty-icon">⌕</div>
        <h3>No similarity reports found</h3>
        <p>Try changing your search or filter criteria.</p>
      </div>
    );
  }

  return (
    <div className="similarity-table-wrap">
      <table className="similarity-table">
        <thead>
          <tr>
            <th>Report ID</th>
            <th>Submission</th>
            <th>Similarity</th>
            <th>Category</th>
            <th>Matched sources</th>
            <th>Review action</th>
            <th>Generated</th>
            <th />
          </tr>
        </thead>

        <tbody>
          {reports.map((report) => {
            const id = report.report_id;

            return (
              <tr
                key={id}
                className={selectedReportId === id ? "selected" : ""}
                onClick={() => onSelect(id)}
              >
                <td>
                  <strong className="report-id">{id}</strong>
                </td>

                <td>{report.submission_id ?? "—"}</td>

                <td>
                  <SimilarityScore score={report.similarity_score} />
                </td>

                <td>
                  <span className="report-category">
                    {formatLabel(report.report_category)}
                  </span>
                </td>

                <td className="source-count">
                  {report.matched_source_count ?? 0}
                </td>

                <td>
                  <span className="review-action">
                    {formatLabel(report.review_action)}
                  </span>
                </td>

                <td>{formatDate(report.generated_at)}</td>

                <td>
                  <button
                  type="button"
                    className="view-report-button"
                    onClick={(event) => {
                      event.stopPropagation();
                      onSelect(id);
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

      <div className="similarity-mobile-list">
        {reports.map((report) => (
          <button
            className="similarity-mobile-card"
            key={report.report_id}
            onClick={() => onSelect(report.report_id)}
          >
            <div className="mobile-card-heading">
              <strong>{report.report_id}</strong>
              <SimilarityScore score={report.similarity_score} />
            </div>

            <span>Submission: {report.submission_id ?? "—"}</span>
            <span>Category: {formatLabel(report.report_category)}</span>
            <span>Review: {formatLabel(report.review_action)}</span>
            <span>
              Matched sources: {report.matched_source_count ?? 0}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}