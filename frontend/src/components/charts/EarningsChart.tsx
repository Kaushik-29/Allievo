import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface EarningsData {
  platform: string;
  amount: number;
}

interface EarningsChartProps {
  data: EarningsData[];
  height?: number;
}

export const EarningsChart: React.FC<EarningsChartProps> = ({ data, height = 250 }) => {
  const COLORS = ["#f43f5e", "#ff6b00", "#10b981", "#3b82f6"];

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
          <XAxis
            dataKey="platform"
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 10, fill: "#9ca3af" }}
            dy={10}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 10, fill: "#9ca3af" }}
          />
          <Tooltip
            cursor={{ fill: "#f9fafb" }}
            contentStyle={{
              borderRadius: "16px",
              border: "none",
              boxShadow: "0 10px 40px -10px rgba(0,0,0,0.1)",
              padding: "12px",
            }}
            labelStyle={{ fontWeight: "bold", marginBottom: "4px", fontSize: "12px" }}
            itemStyle={{ fontSize: "12px", color: "#111827", fontWeight: "bold" }}
            formatter={(value: any) => [`₹${value}`, "Earnings"]}
          />
          <Bar dataKey="amount" radius={[8, 8, 0, 0]} barSize={40}>
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
