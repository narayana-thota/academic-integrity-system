
import { CalendarDays, ChevronRight, UserRound } from "lucide-react";
import { CasePriority, CaseStatus } from "./CasePriority";

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function Similarity({ value }) {
  if (value === null || value === undefined) {
    return <span className="similarity-score">—</span>;
  }

  const score = Number(value);

  return (
    <span className="similarity-score">
      {Number.isFinite(score) ? `${score.toFixed(1)}%` : "—"}
    </span>
  );
}

export default function CasesTable({ cases, onOpenCase }) {
  if (!cases.length) {
    return (
      <div className="cases-empty">
        <UserRound size={28} />
        <h3>No matching cases</h3>
        <p>Try changing your search or filters.</p>
      </div>
    );
  }

  return (
    <>
      <div className="cases-table-wrap">
        <table className="cases-table">
          <thead>
            <tr>
              <th>CASE ID</th>
              <th>LEARNER</th>
              <th>SIMILARITY</th>
              <th>PRIORITY</th>
              <th>CREATED</th>
              <th>DUE DATE</th>
              <th>STATUS</th>
              <th />
            </tr>
          </thead>

          <tbody>
            {cases.map((item) => (
              <tr
                key={item.case_id}
                className="case-row"
                onClick={() => onOpenCase(item.case_id)}
              >
                <td>
                  <span className="case-reference">
                    #{item.case_id}
                  </span>
                  <span className="case-sub-reference">
                    Submission {item.submission_id ?? "—"}
                  </span>
                </td>

                <td>
                  <div className="case-learner">
                    <div className="learner-avatar">
                      {(item.learner_name || "L").charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <strong>{item.learner_name || "Unknown learner"}</strong>
                      <small>{item.learner_code || "—"}</small>
                    </div>
                  </div>
                </td>

                <td><Similarity value={item.similarity_score} /></td>
                <td><CasePriority priority={item.priority} /></td>
                <td>{formatDate(item.created_at)}</td>
                <td>
                  <span className="due-date">
                    <CalendarDays size={13} />
                    {formatDate(item.due_at)}
                  </span>
                </td>
                <td><CaseStatus status={item.case_status} /></td>
                <td>
                  <ChevronRight size={17} className="case-arrow" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="cases-mobile-list">
        {cases.map((item) => (
          <button
            className="case-mobile-card"
            key={item.case_id}
            onClick={() => onOpenCase(item.case_id)}
          >
            <div className="mobile-card-top">
              <span className="case-reference">#{item.case_id}</span>
              <CaseStatus status={item.case_status} />
            </div>

            <div className="mobile-learner">
              <div className="learner-avatar">
                {(item.learner_name || "L").charAt(0).toUpperCase()}
              </div>
              <div>
                <strong>{item.learner_name || "Unknown learner"}</strong>
                <small>{item.learner_code || "—"}</small>
              </div>
            </div>

            <div className="mobile-card-details">
              <div>
                <small>Similarity</small>
                <Similarity value={item.similarity_score} />
              </div>
              <div>
                <small>Priority</small>
                <CasePriority priority={item.priority} />
              </div>
              <div>
                <small>Created</small>
                <strong>{formatDate(item.created_at)}</strong>
              </div>
            </div>
          </button>
        ))}
      </div>
    </>
  );
}
