import { CalendarDays, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function DashboardHeader() {
  const lastSynced = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  return (
    <header className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
          <span className="text-lg font-bold text-primary-foreground">O</span>
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Operator.ai Billing Dashboard
          </h1>
          <p className="text-sm text-muted-foreground">
            Real-time cost monitoring & risk visibility
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-xs text-muted-foreground">
          Last synced: {lastSynced}
        </span>
        <div className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2">
          <CalendarDays className="h-4 w-4 text-muted-foreground" />
          <Select defaultValue="30d">
            <SelectTrigger className="w-[140px] border-0 bg-transparent p-0 h-auto focus:ring-0">
              <SelectValue placeholder="Select range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="14d">Last 14 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button variant="outline" size="sm" className="gap-2">
          <Download className="h-4 w-4" />
          Export Report
        </Button>
      </div>
    </header>
  );
}
