import { StatusBadge } from "./StatusBadge";
import { ArrowUpRight, Server } from "lucide-react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const monthlySpend = [
  { month: "Sep", spend: 8200 },
  { month: "Oct", spend: 9100 },
  { month: "Nov", spend: 8800 },
  { month: "Dec", spend: 10200 },
  { month: "Jan", spend: 12400 },
  { month: "Feb", spend: 14100 },
];

const serviceBreakdown = [
  { service: "EC2", cost: 5200 },
  { service: "S3", cost: 2100 },
  { service: "RDS", cost: 3800 },
  { service: "Lambda", cost: 1800 },
  { service: "Other", cost: 1200 },
];

import { AWSData } from "@/lib/api";

interface AWSCardProps {
  data?: AWSData;
  onRiskClick?: () => void;
}

export function AWSCard({ data, onRiskClick }: AWSCardProps) {
  const currentSpend = data?.current_spend ?? 0;
  const budget = data?.budget ?? 174.56;
  const percentOfBudget = data?.budget_pct ?? 0;
  const weeklyChange = data?.weekly_change ?? 0;
  const status = data?.status ?? "safe";
  const monthlyTrend = data?.monthly_trend ?? monthlySpend;
  const serviceBreakdown = data?.cost_by_service ?? [];

  return (
    <div
      className="relative flex flex-col rounded-lg border border-border bg-card p-4 card-shadow h-full overflow-hidden hover:card-shadow-md cursor-pointer transition-shadow"
      onClick={onRiskClick}
    >
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
        <div className="flex flex-col items-end gap-1">
          {status === "critical" ? (
            <StatusBadge status="critical" label="Over Budget" />
          ) : status === "warning" ? (
            <StatusBadge status="warning" label="Spend Warning" />
          ) : (
            <StatusBadge status="safe" label="On Track" />
          )}
        </div>
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
          <div className={`flex items-center gap-1 ${weeklyChange > 0 ? "text-destructive" : "text-emerald-500"}`}>
            <ArrowUpRight className={`h-3 w-3 ${weeklyChange <= 0 && "rotate-90"}`} />
            <span className="text-xs font-medium">{weeklyChange > 0 ? "+" : ""}{weeklyChange}%</span>
          </div>
        </div>
        <div>
          <div className="h-1.5 rounded-full bg-secondary">
            <div
              className={`h-1.5 rounded-full transition-all ${status === "critical" ? "bg-destructive" : status === "warning" ? "bg-warning" : "bg-aws"
                }`}
              style={{ width: `${Math.min(percentOfBudget, 100)}%` }}
            />
          </div>
          <p className="mt-1 text-[10px] text-muted-foreground">
            {percentOfBudget.toFixed(0)}% of monthly budget
          </p>
        </div>
      </div>

      {/* Monthly Trend Chart */}
      <div className="mb-3 flex-1 min-h-0">
        <p className="mb-1 text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Monthly Spend
        </p>
        <ResponsiveContainer width="100%" height="75%">
          <AreaChart
            data={monthlyTrend}
            margin={{ top: 5, right: 10, left: 10, bottom: 0 }}
          >
            <defs>
              <linearGradient id="awsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(var(--aws))" stopOpacity={0.3} />
                <stop offset="100%" stopColor="hsl(var(--aws))" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 9, fill: "hsl(var(--muted-foreground))" }}
              interval="preserveStartEnd"
              minTickGap={20}
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
            <Area
              type="monotone"
              dataKey="spend"
              stroke="hsl(var(--aws))"
              strokeWidth={2}
              fill="url(#awsGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Service Breakdown */}
      <div className="pt-2 border-t border-border">
        <p className="mb-1 text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Cost by Service
        </p>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={serviceBreakdown.map(s => ({ service: s.service, cost: s.amount }))} layout="vertical" barSize={14} margin={{ left: 0, right: 10 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="service"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 9, fill: "hsl(var(--foreground))" }}
              width={80}
              tickFormatter={(value) => value.length > 15 ? `${value.substring(0, 15)}...` : value}
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
