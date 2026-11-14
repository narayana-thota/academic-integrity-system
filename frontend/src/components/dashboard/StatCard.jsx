
export default function StatCard({ label, value, detail, icon: Icon, tone }) {
  return (
    <article className="stat-card surface">
      <div className="stat-card-top">
        <span>{label}</span>
        <div className={`stat-card-icon ${tone}`}>
          <Icon size={20} strokeWidth={1.8} />
        </div>
      </div>
      <div className="stat-card-value">
        {Number(value || 0).toLocaleString("en-IN")}
      </div>
      <div className="stat-card-detail">{detail}</div>
    </article>
  );
}
