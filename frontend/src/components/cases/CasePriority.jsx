
export function CasePriority({ priority }) {
  const value = (priority || "UNKNOWN").toLowerCase();

  return (
    <span className={`case-priority priority-${value}`}>
      <span className="priority-dot" />
      {priority || "Unknown"}
    </span>
  );
}

export function CaseStatus({ status }) {
  const value = (status || "UNKNOWN").toLowerCase().replaceAll("_", "-");

  return (
    <span className={`case-status status-${value}`}>
      {status ? status.replaceAll("_", " ") : "Unknown"}
    </span>
  );
}
