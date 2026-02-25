import { StatusBadge } from "./StatusBadge";
import { TrendingDown, DollarSign, Calendar, Zap } from "lucide-react";
import {
  ResponsiveContainer,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import { ToolData } from "@/lib/api";
import { cn } from "@/lib/utils";

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

interface AnthropicCardProps {
  data?: ToolData;
  onRiskClick?: () => void;
}

export function AnthropicCard({ data, onRiskClick }: AnthropicCardProps) {
  const creditsRemaining = data?.credits_remaining ?? 0;
  const percentRemaining = data?.percent_remaining ?? 0;
  const status = data?.status ?? "healthy";
  const dailyAvg = data?.daily_avg_usage ?? 0;
  const exhaustion = data?.predicted_exhaustion ?? "N/A";

  const isLow = status === "critical";
  const isWarning = status === "at_risk";

  return (
    <div className="relative flex flex-col rounded-lg border border-border bg-card p-4 card-shadow h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-anthropic-muted">
            <Zap className="h-5 w-5 text-anthropic" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-foreground">Anthropic</h2>
            <p className="text-xs text-muted-foreground">Claude API Credits</p>
          </div>
        </div>
        <TooltipProvider>
          <UITooltip>
            <TooltipTrigger asChild>
              <button onClick={onRiskClick} className="cursor-pointer">
                {isLow && <StatusBadge status="critical" label="Credits Critical" />}
                {isWarning && <StatusBadge status="warning" label="Credits Low" />}
                {!isLow && !isWarning && <StatusBadge status="healthy" label="Healthy" />}
              </button>
            </TooltipTrigger>
            <TooltipContent>Click to view risk details</TooltipContent>
          </UITooltip>
        </TooltipProvider>
      </div>

      {/* Main Metric */}
      <div className="mb-3">
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-foreground">
            {creditsRemaining.toLocaleString()}
          </span>
          <span className="text-sm text-muted-foreground">credits left</span>
        </div>
        <TooltipProvider>
          <UITooltip>
            <TooltipTrigger asChild>
              <div className="mt-1.5 flex items-center gap-3 cursor-pointer" onClick={onRiskClick}>
                <div className="h-1.5 flex-1 rounded-full bg-secondary">
                  <div
                    className="h-1.5 rounded-full bg-anthropic transition-all"
                    style={{ width: `${percentRemaining}%` }}
                  />
                </div>
                <span className="text-xs font-medium text-muted-foreground">
                  {percentRemaining.toFixed(1)}%
                </span>
              </div>
            </TooltipTrigger>
            <TooltipContent>Click to view risk details</TooltipContent>
          </UITooltip>
        </TooltipProvider>
      </div>

      {/* Chart */}
      <div className="mb-3 flex-1 min-h-0">
        <p className="mb-1 text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Daily Usage Trend
        </p>
        <ResponsiveContainer width="100%" height="85%">
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
              tick={{ fontSize: 9, fill: "hsl(var(--muted-foreground))" }}
              interval="preserveStartEnd"
            />
            <YAxis hide />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
                fontSize: "11px",
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
      <div className="grid grid-cols-3 gap-3 pt-3 border-t border-border">
        <div>
          <div className="flex items-center gap-1 text-muted-foreground mb-0.5">
            <TrendingDown className="h-3 w-3" />
            <span className="text-[10px]">Avg Daily</span>
          </div>
          <p className="text-sm font-semibold text-foreground">{dailyAvg.toLocaleString()}</p>
        </div>
        <div>
          <div className="flex items-center gap-1 text-muted-foreground mb-0.5">
            <Calendar className="h-3 w-3" />
            <span className="text-[10px]">Exhaustion</span>
          </div>
          <p className={cn("text-sm font-semibold", isLow ? "text-destructive" : "text-foreground")}>
            {exhaustion}
          </p>
        </div>
        <div>
          <div className="flex items-center gap-1 text-muted-foreground mb-0.5">
            <DollarSign className="h-3 w-3" />
            <span className="text-[10px]">This Month</span>
          </div>
          <p className="text-sm font-semibold text-foreground">$4,280</p>
        </div>
      </div>
    </div>
  );
}
