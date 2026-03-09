import { AlertCircle, AlertTriangle, Info } from "lucide-react";
import { Alert } from "@/lib/api";
import { cn } from "@/lib/utils";

interface AlertsPanelProps {
    alerts: Alert[];
}

const severityConfig: Record<string, { icon: typeof AlertCircle; color: string; bg: string }> = {
    critical: { icon: AlertCircle, color: "text-destructive", bg: "bg-destructive/10" },
    warning: { icon: AlertTriangle, color: "text-warning", bg: "bg-warning/10" },
    alert: { icon: Info, color: "text-blue-500", bg: "bg-blue-500/10" },
};

export function AlertsPanel({ alerts }: AlertsPanelProps) {
    if (!alerts || alerts.length === 0) return null;

    return (
        <div className="rounded-lg border border-border bg-card p-3 card-shadow">
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                Active Alerts ({alerts.length})
            </h3>
            <div className="space-y-2 max-h-[140px] overflow-y-auto pr-1">
                {alerts.map((alert, i) => {
                    const config = severityConfig[alert.severity] || severityConfig.alert;
                    const Icon = config.icon;
                    return (
                        <div
                            key={i}
                            className={cn(
                                "flex items-start gap-2 rounded-md px-2.5 py-1.5 text-xs",
                                config.bg
                            )}
                        >
                            <Icon className={cn("h-3.5 w-3.5 mt-0.5 shrink-0", config.color)} />
                            <div className="flex-1 min-w-0">
                                <span className={cn("font-medium", config.color)}>
                                    [{alert.severity.toUpperCase()}]
                                </span>{" "}
                                <span className="text-foreground">{alert.message}</span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
