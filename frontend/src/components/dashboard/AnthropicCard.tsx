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

const mockUsageData: Record<number, { day: string; credits: number }[]> = {
  7: [
    { day: "Feb 21", credits: 14100 },
    { day: "Feb 22", credits: 12900 },
    { day: "Feb 23", credits: 15600 },
    { day: "Feb 24", credits: 14800 },
    { day: "Feb 25", credits: 16200 },
    { day: "Feb 26", credits: 15100 },
    { day: "Feb 27", credits: 17800 },
  ],
  14: [
    { day: "Feb 14", credits: 13200 },
    { day: "Feb 15", credits: 14100 },
    { day: "Feb 16", credits: 12900 },
    { day: "Feb 17", credits: 15600 },
    { day: "Feb 18", credits: 14800 },
    { day: "Feb 19", credits: 16200 },
    { day: "Feb 20", credits: 15100 },
    { day: "Feb 21", credits: 17800 },
    { day: "Feb 22", credits: 16500 },
    { day: "Feb 23", credits: 18200 },
    { day: "Feb 24", credits: 17100 },
    { day: "Feb 25", credits: 19500 },
    { day: "Feb 26", credits: 18800 },
    { day: "Feb 27", credits: 20100 },
  ],
  30: [
    { day: "Jan 29", credits: 15100 },
    { day: "Jan 30", credits: 17800 },
    { day: "Jan 31", credits: 16500 },
    { day: "Feb 1", credits: 18200 },
    { day: "Feb 2", credits: 17100 },
    { day: "Feb 3", credits: 19500 },
    { day: "Feb 4", credits: 18400 },
    { day: "Feb 5", credits: 20200 },
    { day: "Feb 6", credits: 19100 },
    { day: "Feb 7", credits: 21800 },
    { day: "Feb 8", credits: 20500 },
    { day: "Feb 9", credits: 22200 },
    { day: "Feb 10", credits: 21100 },
    { day: "Feb 11", credits: 23500 },
    { day: "Feb 12", credits: 22400 },
    { day: "Feb 13", credits: 24200 },
    { day: "Feb 14", credits: 23100 },
    { day: "Feb 15", credits: 25800 },
    { day: "Feb 16", credits: 24500 },
    { day: "Feb 17", credits: 26200 },
    { day: "Feb 18", credits: 25100 },
    { day: "Feb 19", credits: 27500 },
    { day: "Feb 20", credits: 26400 },
    { day: "Feb 21", credits: 28200 },
    { day: "Feb 22", credits: 27100 },
    { day: "Feb 23", credits: 29500 },
    { day: "Feb 24", credits: 28400 },
    { day: "Feb 25", credits: 30200 },
    { day: "Feb 26", credits: 29100 },
    { day: "Feb 27", credits: 31800 },
  ],
  90: [
    { day: "Dec 01", credits: 10200 },
    { day: "Dec 15", credits: 12400 },
    { day: "Jan 01", credits: 14100 },
    { day: "Jan 15", credits: 16800 },
    { day: "Feb 01", credits: 19500 },
    { day: "Feb 15", credits: 22100 },
    { day: "Feb 27", credits: 25400 },
  ],
};

interface AnthropicCardProps {
  data?: ToolData;
  onRiskClick?: () => void;
  days: number;
  isLoading?: boolean;
}

export function AnthropicCard({ data, onRiskClick, days, isLoading }: AnthropicCardProps) {
  const creditsRemaining = data?.credits_remaining ?? 0;
  const percentRemaining = data?.percent_remaining ?? 0;
  const status = data?.status ?? "Safe";
  const dailyAvg = data?.daily_avg_usage ?? 0;
  const exhaustion = data?.predicted_exhaustion ?? "N/A";

  const isCritical = status.toLowerCase() === "critical";
  const isWarning = status.toLowerCase() === "warning";

  // Use real data from backend
  const dynamicExhaustion = exhaustion;

  // X-Axis Optimization Logic
  const chartData = data?.history && data.history.length > 0
    ? data.history.map((h) => ({ day: h.day, credits: h.credits }))
    : (mockUsageData[days] || mockUsageData[30]);

  const tickInterval = { 7: 1, 14: 2, 30: 5, 90: 14 }[days as 7 | 14 | 30 | 90] || 5;
  const ticks = chartData
    .filter((_, i) => i % tickInterval === 0 || i === chartData.length - 1)
    .map(d => d.day);

  return (
    <div className="relative flex flex-col rounded-lg border border-border bg-card p-4 card-shadow h-full overflow-hidden transition-all duration-300">
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
                {isCritical && <StatusBadge status="critical" label="Credits Critical" />}
                {isWarning && <StatusBadge status="warning" label="Credits Low" />}
                {!isCritical && !isWarning && <StatusBadge status="safe" label="Safe" />}
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
      <div className="mb-3 flex-1 min-h-0 relative">
        <p className="mb-1 text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Daily Usage Trend
        </p>

        {isLoading ? (
          <div className="flex h-full w-full items-center justify-center bg-muted/20 animate-pulse rounded-lg mt-2">
            <div className="text-xs text-muted-foreground">Fetching usage data...</div>
          </div>
        ) : (
          <div className="h-[85%] w-full animate-in fade-in duration-500">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={chartData}
                margin={{
                  top: 10,
                  right: 20,
                  left: 20,
                  bottom: days === 90 ? 25 : 10
                }}
              >
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
                  ticks={ticks}
                  interval={0}
                  padding={{ left: 0, right: 0 }}
                  tick={{
                    fontSize: 9,
                    fill: "hsl(var(--muted-foreground))",
                    angle: days === 90 ? -35 : 0,
                    textAnchor: days === 90 ? 'end' : 'middle'
                  } as any}
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
                  isAnimationActive={true}
                  animationDuration={800}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
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
          <p className={cn("text-sm font-semibold", isCritical ? "text-destructive" : "text-foreground")}>
            {dynamicExhaustion}
          </p>
        </div>
      </div>
    </div>
  );
}
