import { cn } from "@/lib/utils";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

interface PostHogCardProps {
  eventsToday: number;
  eventsThisMonth: number;
  monthlyLimit: number;
  eventTrendData: { day: string; events: number }[];
  topEvents: { name: string; count: number }[];
}

export function PostHogCard({
  eventsToday = 12450,
  eventsThisMonth = 847320,
  monthlyLimit = 1000000,
  eventTrendData = [
    { day: "Mon", events: 42000 },
    { day: "Tue", events: 38500 },
    { day: "Wed", events: 45200 },
    { day: "Thu", events: 41800 },
    { day: "Fri", events: 52100 },
    { day: "Sat", events: 28400 },
    { day: "Sun", events: 31200 },
  ],
  topEvents = [
    { name: "page_view", count: 324500 },
    { name: "button_click", count: 186200 },
    { name: "form_submit", count: 89400 },
    { name: "api_call", count: 247220 },
  ],
}: Partial<PostHogCardProps>) {
  const percentUsed = (eventsThisMonth / monthlyLimit) * 100;
  const isWarning = percentUsed > 70;
  const isCritical = percentUsed > 90;

  return (
    <div className="relative flex flex-col rounded-lg border border-border bg-card p-3 card-shadow h-full">
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
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-posthog-muted">
            <span className="text-sm font-bold text-posthog">P</span>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">PostHog</h3>
            <p className="text-[10px] text-muted-foreground">Event Analytics</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-lg font-bold text-foreground">
            {eventsToday.toLocaleString()}
          </p>
          <p className="text-[10px] text-muted-foreground">events today</p>
        </div>
      </div>

      {/* Monthly Usage Bar */}
      <div className="mb-2">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-muted-foreground">Monthly events</span>
          <span className="text-[10px] font-medium text-foreground">
            {(eventsThisMonth / 1000).toFixed(0)}K / {(monthlyLimit / 1000000).toFixed(0)}M
          </span>
        </div>
        <div className="h-1.5 w-full rounded-full bg-secondary overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all",
              isCritical ? "bg-destructive" : isWarning ? "bg-warning" : "bg-posthog"
            )}
            style={{ width: `${Math.min(percentUsed, 100)}%` }}
          />
        </div>
        <p className="text-[10px] text-muted-foreground mt-0.5">
          {percentUsed.toFixed(1)}% of monthly quota
        </p>
      </div>

      {/* Event Trend Sparkline */}
      <div className="flex-1 min-h-0">
        <p className="text-[10px] text-muted-foreground mb-1">7-day event volume</p>
        <ResponsiveContainer width="100%" height={36}>
          <AreaChart data={eventTrendData}>
            <defs>
              <linearGradient id="posthogGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(var(--posthog))" stopOpacity={0.3} />
                <stop offset="100%" stopColor="hsl(var(--posthog))" stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area
              type="monotone"
              dataKey="events"
              stroke="hsl(var(--posthog))"
              strokeWidth={1.5}
              fill="url(#posthogGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Top Events Mini List */}
      <div className="pt-2 border-t border-border mt-1">
        <p className="text-[10px] text-muted-foreground mb-1">Top events</p>
        <div className="grid grid-cols-2 gap-x-2 gap-y-0.5">
          {topEvents.slice(0, 4).map((event) => (
            <div key={event.name} className="flex items-center justify-between">
              <span className="text-[9px] text-muted-foreground truncate max-w-[60px]">
                {event.name}
              </span>
              <span className="text-[9px] font-medium text-foreground">
                {(event.count / 1000).toFixed(0)}K
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
