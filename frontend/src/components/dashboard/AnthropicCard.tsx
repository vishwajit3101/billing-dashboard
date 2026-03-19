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

  // X-Axis Optimization Logic: fallback to zeros if history is empty to ensure graph renders
  const chartData = data?.history && data.history.length > 0
    ? data.history.map((h) => ({ day: h.day, credits: h.credits }))
    : Array.from({ length: days }, (_, i) => ({
      day: new Date(Date.now() - (days - 1 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      credits: 0
    }));

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
                  tickFormatter={(value) => {
                    try {
                      const d = new Date(value);
                      if (isNaN(d.getTime())) return value;
                      return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
                    } catch {
                      return value;
                    }
                  }}
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
        <div>
          <div className="flex items-center gap-1 text-muted-foreground mb-0.5">
            <DollarSign className="h-3 w-3" />
            <span className="text-[10px]">This Month</span>
          </div>
          <p className="text-sm font-semibold text-foreground">
            {data?.history ? `$${data.history.reduce((sum, h) => sum + h.credits, 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "$0.00"}
          </p>
        </div>
      </div>
    </div>
  );
}
