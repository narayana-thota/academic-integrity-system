
import { X, FileText, ExternalLink, Clock3 } from "lucide-react";

function formatPercentage(value) {
  if (value == null) return "N/A";

  const number = Number(value);
  if (!Number.isFinite(number)) return "N/A";

  return `${number <= 1 ? (number * 100).toFixed(1) : number.toFixed(2)}%`;
}

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

function formatLabel(value) {
  if (!value) return "Not available";

  return String(value)
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function MatchComparison({ report, onClose }) {
  if (!report) return null;

  const matches = Array.isArray(report.matches)
    ? report.matches
    : [];

  return (
    <div
      className="match-modal-backdrop"
      onClick={onClose}
    >
      <section
        className="match-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="match-panel-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="match-panel-heading">
          <div>
            <p className="eyebrow">REPORT INVESTIGATION</p>
            <h2 id="match-panel-title">Similarity report details</h2>
            <span>{report.report_id}</span>
          </div>

          <button
            type="button"
            className="match-close"
            onClick={onClose}
            aria-label="Close report details"
          >
            <X size={18} />
            Close
          </button>
        </div>

        <div className="match-summary">
          <div>
            <span>Similarity score</span>
            <strong className="match-score">
              {formatPercentage(report.similarity_score)}
            </strong>
          </div>

          <div>
            <span>Report category</span>
            <strong>{formatLabel(report.report_category)}</strong>
          </div>

          <div>
            <span>Review action</span>
            <strong>{formatLabel(report.review_action)}</strong>
          </div>

          <div>
            <span>Matched sources</span>
            <strong>{report.matched_source_count ?? matches.length}</strong>
          </div>

          <div>
            <span>Submission ID</span>
            <strong>{report.submission_id || "—"}</strong>
          </div>

          <div>
            <span>Evaluated rule</span>
            <strong>{report.evaluated_rule_id || "—"}</strong>
          </div>

          <div>
            <span>Associated case</span>
            <strong>{report.case_id || "No linked case"}</strong>
          </div>

          <div>
            <span>Case status</span>
            <strong>{formatLabel(report.case_status)}</strong>
          </div>

          <div>
            <span>Generated</span>
            <strong>{formatDate(report.generated_at)}</strong>
          </div>

          <div>
            <span>Generator version</span>
            <strong>{report.generator_version || "—"}</strong>
          </div>
        </div>

        <div className="match-list-heading">
          <div>
            <p className="eyebrow">SOURCE ANALYSIS</p>
            <h3>Matched sources</h3>
          </div>
          <span>{matches.length} matches</span>
        </div>

        {matches.length === 0 ? (
          <div className="similarity-empty compact">
            No match details are available for this report.
          </div>
        ) : (
          <div className="match-list">
            {matches.map((match, index) => (
              <article
                className="match-item"
                key={match.match_id ?? index}
              >
                <div className="match-number">
                  {match.match_sequence ?? index + 1}
                </div>

                <div className="match-information">
                  <div className="match-title-row">
                    <strong>
                      {match.source_reference || "Source unavailable"}
                    </strong>

                    <span className="match-percentage">
                      {formatPercentage(match.match_percentage)}
                    </span>
                  </div>

                  <span className="match-type">
                    {formatLabel(match.match_type)}
                  </span>

                  {match.description && (
                    <p>{match.description}</p>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}

        <div className="match-panel-footer">
          <span>
            <Clock3 size={14} />
            Report generated {formatDate(report.generated_at)}
          </span>

          <button
            type="button"
            className="match-done-button"
            onClick={onClose}
          >
            Done
          </button>
        </div>
      </section>
    </div>
  );
}
