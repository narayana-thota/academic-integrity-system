
import {
  Cell, Pie, PieChart, ResponsiveContainer, Tooltip,
} from "recharts";

const palette = ["#87977a", "#c47d5b", "#c5a66d", "#788b6d", "#b85d52"];

export default function DecisionChart({ decisions = {} }) {
  const data = [
    { name: "No violation", value: decisions.NO_VIOLATION || 0 },
    { name: "Academic misconduct", value: decisions.ACADEMIC_MISCONDUCT || 0 },
    { name: "Insufficient evidence", value: decisions.INSUFFICIENT_EVIDENCE || 0 },
    { name: "Upheld", value: decisions.UPHELD || 0 },
    { name: "Overturned", value: decisions.OVERTURNED || 0 },
  ];

  return (
    <section className="surface dashboard-panel">
      <div className="panel-heading">
        <div>
          <h2>Decision outcomes</h2>
          <p>Recorded decision distribution</p>
        </div>
        <span className="panel-kicker">ALL STAGES</span>
      </div>

      <div className="decision-chart">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={62}
              outerRadius={91}
              paddingAngle={3}
              stroke="none"
            >
              {data.map((entry, index) => (
                <Cell key={entry.name} fill={palette[index]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="decision-legend">
        {data.map((item, index) => (
          <div className="decision-legend-row" key={item.name}>
            <span style={{ background: palette[index] }} />
            <span>{item.name}</span>
            <strong>{item.value.toLocaleString("en-IN")}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
