import { StatusBadge } from "./StatusBadge";
import { TrendingUp, DollarSign, ArrowUpRight, Server } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";

const monthlySpend = [
  { month: "Sep", spend: 8200 },
  { month: "Oct", spend: 9100 },
  { month: "Nov", spend: 8800 },
  { month: "Dec", spend: 10200 },
  { month: "Jan", spend: 12400 },
  { month: "Feb", spend: 14100 },
];

const serviceBreakdown = [
  { service: "EC2", cost: 5200, color: "hsl(var(--aws))" },
  { service: "S3", cost: 2100, color: "hsl(30 100% 60%)" },
  { service: "RDS", cost: 3800, color: "hsl(30 100% 70%)" },
  { service: "Lambda", cost: 1800, color: "hsl(30 100% 80%)" },
  { service: "Other", cost: 1200, color: "hsl(30 100% 90%)" },
];

export function AWSCard() {
  const currentSpend = 14100;
  const budget = 12000;
  const percentOfBudget = (currentSpend / budget) * 100;
  const weeklyChange = 18.2;
  const isOverBudget = currentSpend > budget;

  return (
    <div className="relative flex flex-col rounded-lg border border-border bg-card p-4 card-shadow h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-aws-muted">
            <Server className="h-5 w-5 text-aws" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-foreground">AWS</h2>
            <p className="text-xs text-muted-foreground">Cloud Infrastructure</p>
          </div>
        </div>
        {isOverBudget && <StatusBadge status="critical" label="Over Budget" />}
        {weeklyChange > 15 && !isOverBudget && (
          <StatusBadge status="warning" label="Spend Spike" />
        )}
      </div>

      {/* Budget vs Actual */}
      <div className="mb-3">
        <div className="flex items-baseline justify-between mb-1.5">
          <div>
            <span className="text-2xl font-bold text-foreground">
              ${currentSpend.toLocaleString()}
            </span>
            <span className="text-muted-foreground text-sm ml-1.5">
              / ${budget.toLocaleString()}
            </span>
          </div>
          <div className="flex items-center gap-1 text-destructive">
            <ArrowUpRight className="h-3 w-3" />
            <span className="text-xs font-medium">+{weeklyChange}%</span>
          </div>
        </div>
        <div className="h-1.5 rounded-full bg-secondary">
          <div
            className={`h-1.5 rounded-full transition-all ${
              isOverBudget ? "bg-destructive" : "bg-aws"
            }`}
            style={{ width: `${Math.min(percentOfBudget, 100)}%` }}
          />
        </div>
        <p className="mt-1 text-[10px] text-muted-foreground">
          {percentOfBudget.toFixed(0)}% of monthly budget
        </p>
      </div>

      {/* Monthly Trend Chart */}
      <div className="mb-3 flex-1 min-h-0">
        <p className="mb-1 text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Monthly Spend
        </p>
        <ResponsiveContainer width="100%" height="70%">
          <LineChart data={monthlySpend}>
            <XAxis
              dataKey="month"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 9, fill: "hsl(var(--muted-foreground))" }}
            />
            <YAxis hide />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
                fontSize: "11px",
              }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, "Spend"]}
            />
            <Line
              type="monotone"
              dataKey="spend"
              stroke="hsl(var(--aws))"
              strokeWidth={2}
              dot={{ fill: "hsl(var(--aws))", strokeWidth: 0, r: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Service Breakdown */}
      <div className="pt-2 border-t border-border">
        <p className="mb-1 text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Cost by Service
        </p>
        <ResponsiveContainer width="100%" height={60}>
          <BarChart data={serviceBreakdown} layout="vertical" barSize={10}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="service"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 9, fill: "hsl(var(--foreground))" }}
              width={40}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
                fontSize: "11px",
              }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, "Cost"]}
            />
            <Bar dataKey="cost" fill="hsl(var(--aws))" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
