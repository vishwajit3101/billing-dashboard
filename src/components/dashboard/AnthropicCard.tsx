import { StatusBadge } from "./StatusBadge";
import { TrendingDown, DollarSign, Calendar, Zap } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";

const usageData = [
  { day: "Jan 20", credits: 12500 },
  { day: "Jan 21", credits: 11800 },
  { day: "Jan 22", credits: 13200 },
  { day: "Jan 23", credits: 14100 },
  { day: "Jan 24", credits: 12900 },
  { day: "Jan 25", credits: 15600 },
  { day: "Jan 26", credits: 14800 },
  { day: "Jan 27", credits: 16200 },
  { day: "Jan 28", credits: 15100 },
  { day: "Jan 29", credits: 17800 },
  { day: "Jan 30", credits: 16500 },
  { day: "Jan 31", credits: 18200 },
  { day: "Feb 1", credits: 17100 },
  { day: "Feb 2", credits: 19500 },
];

export function AnthropicCard() {
  const creditsRemaining = 42350;
  const totalCredits = 500000;
  const percentRemaining = (creditsRemaining / totalCredits) * 100;
  const isLow = percentRemaining < 10;
  const isWarning = percentRemaining < 20 && !isLow;

  return (
    <div className="relative flex flex-col rounded-lg border border-border bg-card p-6 card-shadow h-full">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-anthropic-muted">
            <Zap className="h-6 w-6 text-anthropic" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Anthropic</h2>
            <p className="text-sm text-muted-foreground">Claude API Credits</p>
          </div>
        </div>
        {isLow && <StatusBadge status="critical" label="Credits Critical" />}
        {isWarning && <StatusBadge status="warning" label="Credits Low" />}
        {!isLow && !isWarning && <StatusBadge status="healthy" label="Healthy" />}
      </div>

      {/* Main Metric */}
      <div className="mb-6">
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-bold text-foreground">
            {creditsRemaining.toLocaleString()}
          </span>
          <span className="text-lg text-muted-foreground">credits left</span>
        </div>
        <div className="mt-2 flex items-center gap-4">
          <div className="h-2 flex-1 rounded-full bg-secondary">
            <div
              className="h-2 rounded-full bg-anthropic transition-all"
              style={{ width: `${percentRemaining}%` }}
            />
          </div>
          <span className="text-sm font-medium text-muted-foreground">
            {percentRemaining.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="mb-6 flex-1 min-h-[160px]">
        <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Daily Usage Trend
        </p>
        <ResponsiveContainer width="100%" height={140}>
          <AreaChart data={usageData}>
            <defs>
              <linearGradient id="anthropicGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(var(--anthropic))" stopOpacity={0.3} />
                <stop offset="100%" stopColor="hsl(var(--anthropic))" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="day"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              interval="preserveStartEnd"
            />
            <YAxis hide />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
                fontSize: "12px",
              }}
              formatter={(value: number) => [value.toLocaleString(), "Credits Used"]}
            />
            <Area
              type="monotone"
              dataKey="credits"
              stroke="hsl(var(--anthropic))"
              strokeWidth={2}
              fill="url(#anthropicGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border">
        <div>
          <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
            <TrendingDown className="h-3.5 w-3.5" />
            <span className="text-xs">Avg Daily</span>
          </div>
          <p className="text-lg font-semibold text-foreground">15,420</p>
        </div>
        <div>
          <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
            <Calendar className="h-3.5 w-3.5" />
            <span className="text-xs">Exhaustion</span>
          </div>
          <p className="text-lg font-semibold text-destructive">Feb 6</p>
        </div>
        <div>
          <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
            <DollarSign className="h-3.5 w-3.5" />
            <span className="text-xs">This Month</span>
          </div>
          <p className="text-lg font-semibold text-foreground">$4,280</p>
        </div>
      </div>
    </div>
  );
}
