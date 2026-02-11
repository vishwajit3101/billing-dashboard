import { AlertTriangle } from "lucide-react";

interface RiskBannerProps {
  toolsAtRisk: number;
  servicesOverBudget: number;
  nextExhaustion: string;
}

export function RiskBanner({ toolsAtRisk, servicesOverBudget, nextExhaustion }: RiskBannerProps) {
  const hasRisk = toolsAtRisk > 0 || servicesOverBudget > 0;

  if (!hasRisk) return null;

  return (
    <div className="flex items-center gap-3 rounded-lg border border-warning/30 bg-warning/5 px-4 py-2">
      <AlertTriangle className="h-4 w-4 text-warning shrink-0" />
      <p className="text-sm text-foreground">
        <span className="font-semibold">⚠ {toolsAtRisk} tool{toolsAtRisk !== 1 ? "s" : ""} at risk</span>
        <span className="mx-2 text-muted-foreground">|</span>
        <span className="font-semibold">{servicesOverBudget} service{servicesOverBudget !== 1 ? "s" : ""} over budget</span>
        <span className="mx-2 text-muted-foreground">|</span>
        <span>Next exhaustion: <span className="font-semibold text-destructive">{nextExhaustion}</span></span>
      </p>
    </div>
  );
}
