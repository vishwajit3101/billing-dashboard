import { X, ExternalLink, Bell, TrendingDown, Calendar, DollarSign, ArrowUpRight, Server } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  LineChart,
  Line,
} from "recharts";

interface RiskDetailPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  type: "anthropic" | "aws";
}

const anthropicUsage = [
  { day: "Feb 4", credits: 15600 },
  { day: "Feb 5", credits: 14800 },
  { day: "Feb 6", credits: 16200 },
  { day: "Feb 7", credits: 15100 },
  { day: "Feb 8", credits: 17800 },
  { day: "Feb 9", credits: 16500 },
  { day: "Feb 10", credits: 18200 },
];

const awsMonthly = [
  { month: "Sep", spend: 8200 },
  { month: "Oct", spend: 9100 },
  { month: "Nov", spend: 8800 },
  { month: "Dec", spend: 10200 },
  { month: "Jan", spend: 12400 },
  { month: "Feb", spend: 14100 },
];

const awsServices = [
  { service: "EC2", cost: 5200 },
  { service: "RDS", cost: 3800 },
  { service: "S3", cost: 2100 },
  { service: "Lambda", cost: 1800 },
  { service: "Other", cost: 1200 },
];

export function RiskDetailPanel({ open, onOpenChange, type }: RiskDetailPanelProps) {
  if (type === "anthropic") {
    return (
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className="w-[420px] sm:max-w-[420px] overflow-y-auto">
          <SheetHeader className="pb-4 border-b border-border">
            <SheetTitle className="flex items-center gap-2 text-foreground">
              <div className="h-8 w-8 rounded-lg bg-anthropic-muted flex items-center justify-center">
                <span className="text-sm font-bold text-anthropic">A</span>
              </div>
              Anthropic Risk Details
            </SheetTitle>
            <SheetDescription>Claude API credit monitoring & predictions</SheetDescription>
          </SheetHeader>

          <div className="space-y-6 pt-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg border border-border p-3">
                <p className="text-xs text-muted-foreground mb-1">Credits Remaining</p>
                <p className="text-2xl font-bold text-foreground">42,350</p>
              </div>
              <div className="rounded-lg border border-border p-3">
                <p className="text-xs text-muted-foreground mb-1">Avg Daily Usage</p>
                <p className="text-2xl font-bold text-foreground">15,420</p>
              </div>
            </div>

            <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3">
              <div className="flex items-center gap-2 mb-1">
                <Calendar className="h-4 w-4 text-destructive" />
                <p className="text-xs font-medium text-destructive">Predicted Exhaustion</p>
              </div>
              <p className="text-xl font-bold text-destructive">February 6, 2026</p>
              <p className="text-xs text-muted-foreground mt-1">Based on 7-day rolling average</p>
            </div>

            {/* 7-day Chart */}
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                Last 7-Day Usage
              </p>
              <ResponsiveContainer width="100%" height={160}>
                <AreaChart data={anthropicUsage}>
                  <defs>
                    <linearGradient id="panelAnthropicGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(var(--anthropic))" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="hsl(var(--anthropic))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: "11px" }}
                    formatter={(value: number) => [value.toLocaleString(), "Credits Used"]}
                  />
                  <Area type="monotone" dataKey="credits" stroke="hsl(var(--anthropic))" strokeWidth={2} fill="url(#panelAnthropicGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Actions */}
            <div className="space-y-2 pt-2 border-t border-border">
              <Button variant="outline" className="w-full justify-start gap-2" size="sm">
                <TrendingDown className="h-4 w-4" />
                View usage details
              </Button>
              <Button variant="outline" className="w-full justify-start gap-2" size="sm">
                <Bell className="h-4 w-4" />
                Notify finance
              </Button>
              <Button variant="outline" className="w-full justify-start gap-2" size="sm">
                <ExternalLink className="h-4 w-4" />
                Open refill link
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[420px] sm:max-w-[420px] overflow-y-auto">
        <SheetHeader className="pb-4 border-b border-border">
          <SheetTitle className="flex items-center gap-2 text-foreground">
            <div className="h-8 w-8 rounded-lg bg-aws-muted flex items-center justify-center">
              <Server className="h-4 w-4 text-aws" />
            </div>
            AWS Risk Details
          </SheetTitle>
          <SheetDescription>Cloud infrastructure cost analysis</SheetDescription>
        </SheetHeader>

        <div className="space-y-6 pt-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border border-border p-3">
              <p className="text-xs text-muted-foreground mb-1">Current Spend</p>
              <p className="text-2xl font-bold text-destructive">$14,100</p>
            </div>
            <div className="rounded-lg border border-border p-3">
              <p className="text-xs text-muted-foreground mb-1">Budget</p>
              <p className="text-2xl font-bold text-foreground">$12,000</p>
            </div>
          </div>

          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3">
            <div className="flex items-center gap-2 mb-1">
              <ArrowUpRight className="h-4 w-4 text-destructive" />
              <p className="text-xs font-medium text-destructive">Weekly Increase</p>
            </div>
            <p className="text-xl font-bold text-destructive">+18.2%</p>
            <p className="text-xs text-muted-foreground mt-1">Compared to previous week</p>
          </div>

          {/* Monthly Spend Chart */}
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
              Monthly Spend Trend
            </p>
            <ResponsiveContainer width="100%" height={140}>
              <LineChart data={awsMonthly}>
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                <YAxis hide />
                <Tooltip
                  contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: "11px" }}
                  formatter={(value: number) => [`$${value.toLocaleString()}`, "Spend"]}
                />
                <Line type="monotone" dataKey="spend" stroke="hsl(var(--aws))" strokeWidth={2} dot={{ fill: "hsl(var(--aws))", strokeWidth: 0, r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Service Breakdown */}
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
              Cost by Service
            </p>
            <ResponsiveContainer width="100%" height={120}>
              <BarChart data={awsServices} layout="vertical" barSize={12}>
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="service" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "hsl(var(--foreground))" }} width={50} />
                <Tooltip
                  contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: "11px" }}
                  formatter={(value: number) => [`$${value.toLocaleString()}`, "Cost"]}
                />
                <Bar dataKey="cost" fill="hsl(var(--aws))" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Actions */}
          <div className="space-y-2 pt-2 border-t border-border">
            <Button variant="outline" className="w-full justify-start gap-2" size="sm">
              <ExternalLink className="h-4 w-4" />
              View AWS Cost Explorer
            </Button>
            <Button variant="outline" className="w-full justify-start gap-2" size="sm">
              <TrendingDown className="h-4 w-4" />
              Reduce usage suggestions
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
