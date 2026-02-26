import { cn } from "@/lib/utils";
import { AlertTriangle, AlertCircle, CheckCircle } from "lucide-react";

type StatusType = "Critical" | "Warning" | "Safe";

interface StatusBadgeProps {
  status: string; // Keep string for loose matching if needed
  label: string;
  className?: string;
}

const statusConfig: Record<string, any> = {
  critical: {
    icon: AlertCircle,
    bgClass: "bg-destructive/10",
    textClass: "text-destructive",
    iconClass: "text-destructive",
  },
  warning: {
    icon: AlertTriangle,
    bgClass: "bg-warning/10",
    textClass: "text-warning",
    iconClass: "text-warning",
  },
  safe: {
    icon: CheckCircle,
    bgClass: "bg-success/10",
    textClass: "text-success",
    iconClass: "text-success",
  },
};

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const config = statusConfig[status.toLowerCase()] || statusConfig.safe;
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
        config.bgClass,
        config.textClass,
        className
      )}
    >
      <Icon className={cn("h-3 w-3", config.iconClass)} />
      {label}
    </div>
  );
}
