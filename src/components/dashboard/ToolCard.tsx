import { cn } from "@/lib/utils";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts";

type ToolType = "tavily" | "fullenrich" | "buyercaddy";

interface ToolCardProps {
  tool: ToolType;
  name: string;
  creditsUsed: number;
  creditsTotal: number;
  sparklineData: number[];
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
  creditsUsed,
  creditsTotal,
  sparklineData,
}: ToolCardProps) {
  const config = toolConfig[tool];
  const creditsRemaining = creditsTotal - creditsUsed;
  const percentUsed = (creditsUsed / creditsTotal) * 100;
  const percentRemaining = 100 - percentUsed;
  const isLow = percentRemaining < 15;
  const isWarning = percentRemaining < 30 && !isLow;

  const pieData = [
    { name: "Used", value: creditsUsed },
    { name: "Remaining", value: creditsRemaining },
  ];

  const sparkData = sparklineData.map((value, index) => ({
    index,
    value,
  }));

  return (
    <div className="relative flex flex-col rounded-lg border border-border bg-card p-5 card-shadow h-full">
      {/* Alert Indicator */}
      {(isLow || isWarning) && (
        <div
          className={cn(
            "absolute top-4 right-4 h-2.5 w-2.5 rounded-full",
            isLow ? "bg-destructive animate-pulse-slow" : "bg-warning"
          )}
        />
      )}

      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-lg",
            config.bgClass
          )}
        >
          <span
            className="text-lg font-bold"
            style={{ color: config.color }}
          >
            {name.charAt(0)}
          </span>
        </div>
        <div>
          <h3 className="text-base font-semibold text-foreground">{name}</h3>
          <p className="text-xs text-muted-foreground">{config.description}</p>
        </div>
      </div>

      {/* Ring Chart & Credits */}
      <div className="flex items-center gap-4 mb-4">
        <div className="relative h-20 w-20">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={28}
                outerRadius={38}
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
            <span className="text-sm font-bold text-foreground">
              {percentRemaining.toFixed(0)}%
            </span>
          </div>
        </div>
        <div>
          <p className="text-2xl font-bold text-foreground">
            {creditsRemaining.toLocaleString()}
          </p>
          <p className="text-xs text-muted-foreground">credits remaining</p>
        </div>
      </div>

      {/* Sparkline */}
      <div className="pt-3 border-t border-border">
        <p className="mb-2 text-xs text-muted-foreground">7-day usage</p>
        <ResponsiveContainer width="100%" height={32}>
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
      </div>
    </div>
  );
}
