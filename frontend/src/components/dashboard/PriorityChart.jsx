
import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";

const priorityColors = {
  CRITICAL: "#b85d52",
  HIGH: "#c47d5b",
  MEDIUM: "#a2ad91",
  LOW: "#8c9b7c",
};

export default function PriorityChart({ priorities = {} }) {
  const data = Object.entries(priorities).map(([name, value]) => ({
    name: name.charAt(0) + name.slice(1).toLowerCase(),
    value,
    color: priorityColors[name],
  }));

  return (
    <section className="surface dashboard-panel">
      <div className="panel-heading">
        <div>
          <h2>Case priority</h2>
          <p>Distribution of recorded cases</p>
        </div>
        <span className="panel-kicker">BY PRIORITY</span>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barSize={38}>
            <CartesianGrid stroke="#eeede7" vertical={false} />
            <XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fill: "#85887e", fontSize: 11 }} />
            <YAxis tickLine={false} axisLine={false} tick={{ fill: "#85887e", fontSize: 11 }} />
            <Tooltip
              contentStyle={{ borderRadius: 10, border: "1px solid #e9e8e0" }}
              cursor={{ fill: "#f5f4ef" }}
            />
            <Bar dataKey="value" radius={[7, 7, 0, 0]}>
              {data.map((item) => (
                <cell key={item.name} fill={item.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
