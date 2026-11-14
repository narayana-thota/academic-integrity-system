function Stat({ label, value, description }) {
  return (
    <div className="similarity-stat">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{description}</small>
    </div>
  );
}

export default function SimilarityStats({ reports, total }) {
  const scores = reports
    .map((report) => Number(report.similarity_score))
    .filter(Number.isFinite)
    .map((score) => (score <= 1 ? score * 100 : score));

  const average = scores.length
    ? `${(
        scores.reduce((sum, score) => sum + score, 0) / scores.length
      ).toFixed(1)}%`
    : "—";

  const matchedSources = reports.reduce(
    (sum, report) =>
      sum + (Number(report.matched_source_count) || 0),
    0
  );

  const flagged = reports.filter((report) => {
    const score = Number(report.similarity_score);
    const percentage = score <= 1 ? score * 100 : score;
    return Number.isFinite(score) && percentage >= 70;
  }).length;

  return (
    <div className="similarity-stats">
      <Stat
        label="Total reports"
        value={total}
        description="Reports in the system"
      />

      <Stat
        label="Average similarity"
        value={average}
        description="Current page average"
      />

      <Stat
        label="Matched sources"
        value={matchedSources}
        description="Sources across current page"
      />

      <Stat
        label="High similarity"
        value={flagged}
        description="70% or higher on current page"
      />
    </div>
  );
}