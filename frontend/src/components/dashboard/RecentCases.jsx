
import { ArrowRight, Search } from "lucide-react";
import { useMemo, useState } from "react";
import StatusBadge from "../common/StatusBadge";

export default function RecentCases({ cases = [], onViewAll, onOpenCase }) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => cases.filter((item) => {
    const text = `${item.case_id} ${item.learner_name} ${item.learner_code}`;
    return text.toLowerCase().includes(query.toLowerCase());
  }), [cases, query]);

  return (
    <section className="surface dashboard-panel cases-panel">
      <div className="panel-heading cases-heading">
        <div>
          <h2>Recent integrity cases</h2>
          <p>Latest records from the case management system</p>
        </div>
        <button className="subtle-button" onClick={onViewAll}>
          View all <ArrowRight size={15} />
        </button>
      </div>

      <label className="table-search">
        <Search size={17} />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search case or learner"
        />
      </label>

      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>CASE</th>
              <th>LEARNER</th>
              <th>SIMILARITY</th>
              <th>PRIORITY</th>
              <th>STATUS</th>
              <th>CREATED</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => (
              <tr key={item.case_id} onClick={() => onOpenCase?.(item.case_id)}>
                <td className="table-case-id">{item.case_id}</td>
                <td>
                  <strong className="table-primary">{item.learner_name}</strong>
                  <small className="table-secondary">{item.learner_code}</small>
                </td>
                <td>{Number(item.similarity_score).toFixed(2)}%</td>
                <td>
                  <span className={`priority-label priority-${item.priority?.toLowerCase()}`}>
                    {item.priority}
                  </span>
                </td>
                <td><StatusBadge value={item.case_status} /></td>
                <td>{item.created_at?.slice(0, 10) || "—"}</td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan="6" className="empty-message">No matching cases found.</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="table-mobile-note">Swipe horizontally to view all case details.</div>
    </section>
  );
}
