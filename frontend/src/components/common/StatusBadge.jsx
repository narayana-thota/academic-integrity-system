
export default function StatusBadge({ value }) {
  const normalized = (value || "UNKNOWN").toLowerCase().replaceAll("_", "-");

  return (
    <span className={`status-badge status-${normalized}`}>
      {value?.replaceAll("_", " ") || "Unknown"}
    </span>
  );
}
