
import {
  Activity,
  ArrowUpRight,
  BookOpen,
  CheckCircle2,
  ClipboardList,
  FileSearch,
  Gavel,
  RefreshCw,
  ShieldCheck,
  Users,
  AlertTriangle,
} from "lucide-react";

import useDashboard from "../hooks/useDashboard";
import "../styles/dashboard.css";

const number = (value) =>
  Number(value || 0).toLocaleString("en-IN");

function MetricCard({ icon: Icon, label, value, note, accent }) {
  return (
    <article className={`metric-card ${accent}`}>
      <div className="metric-top">
        <span className="metric-icon">
          <Icon size={19} />
        </span>
        <span className="metric-note">{note}</span>
      </div>
      <div className="metric-value">{number(value)}</div>
      <div className="metric-label">{label}</div>
    </article>
  );
}

function Distribution({ title, data, colors }) {
  const entries = Object.entries(data || {});
  const total = entries.reduce(
    (sum, [, value]) => sum + Number(value || 0),
    0
  );

  return (
    <section className="panel distribution-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">CASE ANALYTICS</p>
          <h3>{title}</h3>
        </div>
        <span className="panel-total">{number(total)} total</span>
      </div>

      {entries.length === 0 ? (
        <p className="empty-inline">
          No distribution data available.
        </p>
      ) : (
        <div className="distribution-list">
          {entries.map(([name, value], index) => {
            const amount = Number(value || 0);
            const percent = total ? (amount / total) * 100 : 0;
            const color = colors[index % colors.length];

            return (
              <div className="distribution-item" key={name}>
                <div className="distribution-label">
                  <span
                    className="legend-dot"
                    style={{ background: color }}
                  />
                  <span>{name.replaceAll("_", " ")}</span>
                  <strong>{number(amount)}</strong>
                </div>

                <div className="progress-track">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${percent}%`,
                      background: color,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

function RecentCases({ cases }) {
  return (
    <section className="panel recent-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">LATEST RECORDS</p>
          <h3>Recent cases</h3>
        </div>
        <span className="panel-total">
          {cases.length} shown
        </span>
      </div>

      {cases.length === 0 ? (
        <p className="empty-inline">
          No case records returned by the API.
        </p>
      ) : (
        <div className="table-scroll">
          <table className="case-table">
            <thead>
              <tr>
                <th>CASE</th>
                <th>LEARNER</th>
                <th>SIMILARITY</th>
                <th>PRIORITY</th>
                <th>STATUS</th>
              </tr>
            </thead>

            <tbody>
              {cases.map((item, index) => (
                <tr key={item.case_id ?? index}>
                  <td className="case-id">
                    #{item.case_id}
                  </td>

                  <td>
                    <div className="learner-name">
                      {item.learner_name ||
                        item.learner_code ||
                        "Unknown learner"}
                    </div>
                    <div className="muted-small">
                      {item.learner_code || "—"}
                    </div>
                  </td>

                  <td>
                    <span className="similarity-value">
                      {item.similarity_score != null
                        ? `${Number(item.similarity_score).toFixed(1)}%`
                        : "—"}
                    </span>
                  </td>

                  <td>
                    <span
                      className={`priority-tag ${(item.priority || "low").toLowerCase()}`}
                    >
                      {item.priority || "—"}
                    </span>
                  </td>

                  <td>
                    <span
                      className={`status-tag ${(item.case_status || "unknown")
                        .toLowerCase()
                        .replaceAll("_", "-")}`}
                    >
                      {item.case_status || "Unknown"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default function Dashboard() {
  const { summary, cases, loading, error, refresh } =
    useDashboard();

  const totals = summary?.totals || {};
  const caseMetrics = summary?.case_metrics || {};
  const decisionMetrics = summary?.decision_metrics || {};

  // Correct backend mapping: appeal_metrics
  const appealMetrics = summary?.appeal_metrics || {};

  const resolvedAppeals =
    appealMetrics.by_status?.RESOLVED ?? 0;

  const upheldAppeals =
    appealMetrics.by_outcome?.UPHELD ?? 0;

  const overturnedAppeals =
    appealMetrics.by_outcome?.OVERTURNED ?? 0;

  const modifiedAppeals =
    appealMetrics.by_outcome?.MODIFIED ?? 0;

  const priorityColors = [
    "#d49b4b",
    "#c77b52",
    "#a9b68c",
    "#71836b",
  ];

  const decisionColors = [
    "#91a77b",
    "#d49b4b",
    "#bd765d",
    "#788a75",
    "#b0a58c",
  ];

  if (loading) {
    return (
      <main className="dashboard-page">
        <div className="dashboard-loading">
          <span className="loading-spinner" />
          <p>Loading academic integrity data...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="dashboard-page">
        <div className="dashboard-error">
          <AlertTriangle size={28} />
          <h2>Dashboard data unavailable</h2>
          <p>{error}</p>

          <button className="primary-button" onClick={refresh}>
            <RefreshCw size={16} />
            Retry connection
          </button>
        </div>
      </main>
    );
  }

  const closedPercentage = totals.cases
    ? (Number(caseMetrics.closed || 0) /
        Number(totals.cases)) *
      100
    : 0;

  return (
    <main className="dashboard-page">
      <div className="dashboard-header">
        <div>
          <p className="eyebrow">
            ACADEMIC INTEGRITY / OVERVIEW
          </p>
          <h1>Command center</h1>
          <p className="dashboard-subtitle">
            Monitor submissions, investigations, decisions and appeals.
          </p>
        </div>

        <button className="refresh-button" onClick={refresh}>
          <RefreshCw size={15} />
          Refresh data
        </button>
      </div>

      <section className="welcome-strip">
        <div className="welcome-icon">
          <ShieldCheck size={25} />
        </div>

        <div>
          <p className="welcome-kicker">SYSTEM OVERVIEW</p>
          <h2>Integrity operations at a glance</h2>
          <p>
            Similarity flags support human review. They do not
            determine misconduct.
          </p>
        </div>

        <div className="welcome-status">
          <span className="live-dot" />
          API connected
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard
          icon={Users}
          label="Learners"
          value={totals.learners}
          note="Registered"
          accent="green"
        />

        <MetricCard
          icon={BookOpen}
          label="Submissions"
          value={totals.submissions}
          note="Total records"
          accent="gold"
        />

        <MetricCard
          icon={FileSearch}
          label="Similarity reports"
          value={totals.similarity_reports}
          note="Generated"
          accent="orange"
        />

        <MetricCard
          icon={ClipboardList}
          label="Integrity cases"
          value={totals.cases}
          note="Total cases"
          accent="sage"
        />

        <MetricCard
          icon={CheckCircle2}
          label="Decisions"
          value={totals.decisions}
          note="Recorded"
          accent="green"
        />

        <MetricCard
          icon={Gavel}
          label="Appeals"
          value={totals.appeals}
          note="Submitted"
          accent="gold"
        />
      </section>

      <section className="analytics-grid">
        <Distribution
          title="Cases by priority"
          data={caseMetrics.by_priority}
          colors={priorityColors}
        />

        <Distribution
          title="Decisions by outcome"
          data={decisionMetrics.by_type}
          colors={decisionColors}
        />
      </section>

      <section className="bottom-grid">
        <RecentCases cases={cases} />

        <section className="panel resolution-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">CASE LIFECYCLE</p>
              <h3>Resolution snapshot</h3>
            </div>

            <Activity size={19} className="panel-icon" />
          </div>

          <div className="resolution-number">
            {number(caseMetrics.closed)}
            <span>
              {" "}/ {number(totals.cases)} cases closed
            </span>
          </div>

          <div className="progress-track resolution-track">
            <div
              className="progress-fill"
              style={{
                width: `${closedPercentage}%`,
                background: "#91a77b",
              }}
            />
          </div>

          <div className="resolution-details">
            <div>
              <span
                className="legend-dot"
                style={{ background: "#91a77b" }}
              />
              <span>Closed</span>
              <strong>{number(caseMetrics.closed)}</strong>
            </div>

            <div>
              <span
                className="legend-dot"
                style={{ background: "#d49b4b" }}
              />
              <span>Not closed</span>
              <strong>{number(caseMetrics.not_closed)}</strong>
            </div>
          </div>

          <div className="appeal-summary">
            <div className="appeal-icon">
              <Gavel size={18} />
            </div>

            <div className="appeal-summary-content">
              <strong>
                {number(resolvedAppeals)} appeals resolved
              </strong>

              <p>
                Review outcomes are recorded separately from initial
                decisions.
              </p>

              <div className="appeal-outcome-breakdown">
                <span>
                  Upheld <strong>{number(upheldAppeals)}</strong>
                </span>

                <span>
                  Overturned <strong>{number(overturnedAppeals)}</strong>
                </span>

                {modifiedAppeals > 0 && (
                  <span>
                    Modified <strong>{number(modifiedAppeals)}</strong>
                  </span>
                )}
              </div>
            </div>

            <ArrowUpRight size={17} />
          </div>
        </section>
      </section>

      <p className="dashboard-footnote">
        Data is loaded from the Academic Integrity API. Similarity
        scores are indicators for review, not findings of misconduct.
      </p>
    </main>
  );
}
