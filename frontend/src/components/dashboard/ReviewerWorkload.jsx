
import { Users } from "lucide-react";

export default function ReviewerWorkload({ reviewers = [] }) {
  return (
    <section className="surface dashboard-panel">
      <div className="panel-heading">
        <div>
          <h2>Reviewer capacity</h2>
          <p>Active workload of available reviewers</p>
        </div>
        <Users size={19} color="#85887e" />
      </div>

      <div className="reviewer-list">
        {reviewers.slice(0, 6).map((reviewer) => {
          const active = reviewer.active_cases || 0;
          const capacity = reviewer.max_active_cases || 1;
          const percentage = Math.min((active / capacity) * 100, 100);

          return (
            <div className="reviewer-item" key={reviewer.reviewer_id}>
              <div className="reviewer-initials">
                {reviewer.name?.split(" ").map((part) => part[0]).join("")}
              </div>
              <div className="reviewer-details">
                <strong>{reviewer.name}</strong>
                <small>{reviewer.reviewer_code}</small>
                <div className="reviewer-progress">
                  <span style={{ width: `${percentage}%` }} />
                </div>
              </div>
              <div className="reviewer-count">
                <strong>{active}/{capacity}</strong>
                <small>Active</small>
              </div>
            </div>
          );
        })}
        {reviewers.length === 0 && (
          <p className="empty-message">No reviewer workload data available.</p>
        )}
      </div>
    </section>
  );
}
