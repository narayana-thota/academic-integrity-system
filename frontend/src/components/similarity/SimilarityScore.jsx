export default function SimilarityScore({ score }) {
  if (score == null) {
    return <span className="similarity-score unavailable">N/A</span>;
  }

  const numericScore = Number(score);
  const percentage =
    numericScore <= 1 ? numericScore * 100 : numericScore;

  const level =
    percentage >= 70
      ? "high"
      : percentage >= 40
        ? "medium"
        : "low";

  return (
    <div className="similarity-score-wrap">
      <strong className={`similarity-score ${level}`}>
        {percentage.toFixed(1)}%
      </strong>

      <div className="similarity-meter">
        <span
          className={level}
          style={{
            width: `${Math.min(100, Math.max(0, percentage))}%`,
          }}
        />
      </div>
    </div>
  );
}