import { cn } from "@/lib/utils";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts";

import { ToolData } from "@/lib/api";

type ToolType = "tavily" | "fullenrich" | "buyercaddy";

interface ToolCardProps {
  tool: ToolType;
  name: string;
  data?: ToolData;
  sparklineData: number[];
  days?: number;
  onClick?: () => void;
}

const toolConfig: Record<
  ToolType,
  { color: string; bgClass: string; description: string }
> = {
  tavily: {
    color: "hsl(var(--tavily))",
    bgClass: "bg-tavily-muted",
    description: "Search API",
  },
  fullenrich: {
    color: "hsl(var(--fullenrich))",
    bgClass: "bg-fullenrich-muted",
    description: "Data Enrichment",
  },
  buyercaddy: {
    color: "hsl(var(--buyercaddy))",
    bgClass: "bg-buyercaddy-muted",
    description: "Sales Intelligence",
  },
};

export function ToolCard({
  tool,
  name,
  data,
  sparklineData,
  days = 7,
  onClick,
}: ToolCardProps) {
  const config = toolConfig[tool];
  const hasLiveData = Boolean(data);
  const creditsRemaining = data?.credits_remaining ?? 0;
  const percentRemaining = data?.percent_remaining ?? 0;
  const status = data?.status ?? "Unknown";
  const exhaustionDate = data?.predicted_exhaustion;
  const hasRealHistory = Boolean(data?.history && data.history.length > 0);
  const hasFallbackSparkline = sparklineData.length > 0;

  const isCritical = status.toLowerCase() === "critical";
  const isWarning = status.toLowerCase() === "warning";

  const pieData = [
    { name: "Used", value: 100 - percentRemaining },
    { name: "Remaining", value: percentRemaining },
  ];

  // Use real history if available, otherwise fallback to index-based mapping
  const sparkData = hasRealHistory
    ? data.history.map((h, i) => ({ index: i, value: h.credits }))
    : sparklineData.map((value, index) => ({ index, value }));

  return (
    <div
      className="relative flex flex-col rounded-lg border border-border bg-card p-3 card-shadow h-full cursor-pointer transition-shadow hover:card-shadow-md"
      onClick={onClick}
    >
      {/* Alert Indicator */}
      {(isCritical || isWarning) && (
        <div
          className={cn(
            "absolute top-3 right-3 h-2 w-2 rounded-full",
            isCritical ? "bg-destructive animate-pulse-slow" : "bg-warning"
          )}
        />
      )}

      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        <div
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-lg",
            config.bgClass
          )}
        >
          <span
            className="text-sm font-bold"
            style={{ color: config.color }}
          >
            {name.charAt(0)}
          </span>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">{name}</h3>
          <p className="text-[10px] text-muted-foreground">{config.description}</p>
        </div>
      </div>

      {/* Ring Chart & Credits */}
      <div className="flex items-center gap-3 mb-2">
        <div className="relative h-14 w-14 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={20}
                outerRadius={26}
                startAngle={90}
                endAngle={-270}
                paddingAngle={2}
                dataKey="value"
              >
                <Cell fill={config.color} />
                <Cell fill="hsl(var(--secondary))" />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-[10px] font-bold text-foreground">
              {percentRemaining.toFixed(0)}%
            </span>
          </div>
        </div>
        <div>
          <p className="text-lg font-bold text-foreground">
            {creditsRemaining.toLocaleString()}
          </p>
          <div className="flex items-center gap-1.5 flex-wrap">
            <p className="text-[10px] text-muted-foreground whitespace-nowrap">
              {hasLiveData ? "credits left" : "No live credits data"}
            </p>
            {exhaustionDate && (
              <>
                <span className="text-[8px] text-muted-foreground">•</span>
                <p className="text-[9px] font-medium text-warning whitespace-nowrap">
                  Exhausts: {new Date(exhaustionDate).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                </p>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Sparkline */}
      <div className="pt-2 border-t border-border">
        <p className="mb-1 text-[10px] text-muted-foreground">{days}-day usage</p>
        {(hasRealHistory || hasFallbackSparkline) ? (
          <ResponsiveContainer width="100%" height={24}>
            <LineChart data={sparkData}>
              <Line
                type="monotone"
                dataKey="value"
                stroke={config.color}
                strokeWidth={1.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-[10px] text-muted-foreground">No real usage data yet</p>
        )}
      </div>
    </div>
  );
}
