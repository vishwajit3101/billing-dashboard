import { useState } from "react";
import { DashboardHeader } from "./DashboardHeader";
import { RiskBanner } from "./RiskBanner";
import { AnthropicCard } from "./AnthropicCard";
import { AWSCard } from "./AWSCard";
import { ToolCard } from "./ToolCard";
import { RiskDetailPanel } from "./RiskDetailPanel";

import { useDashboard } from "@/hooks/useDashboard";

import { getExportUrl } from "@/lib/api";

export function BillingDashboard() {
  const [range, setRange] = useState("30d");
  const days = parseInt(range);
  const { data, isLoading, error } = useDashboard(days);
  const [riskPanel, setRiskPanel] = useState<{ open: boolean; type: "anthropic" | "aws" | "tavily" | "fullenrich" | "buyercaddy" }>({
    open: false,
    type: "anthropic",
  });

  const handleExport = () => {
    const url = getExportUrl(days, "csv");
    window.open(url, "_blank");
  };

  if (isLoading) {
    return <div className="h-screen flex items-center justify-center bg-background text-foreground">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="h-screen flex items-center justify-center bg-background text-destructive">Error loading dashboard</div>;
  }

  const findTool = (name: string) => data?.tools.find(t => t.name.toLowerCase() === name.toLowerCase());

  const toolsAtRisk = data?.tools.filter(t => t.status.toLowerCase() !== "safe").length ?? 0;
  const servicesOverBudget = (data?.aws.monthly_spend ?? 0) > (data?.aws.monthly_budget ?? 0) ? 1 : 0;
  const nextExhaustion = data?.tools
    .filter(t => t.predicted_exhaustion && t.predicted_exhaustion !== "N/A")
    .sort((a, b) => new Date(a.predicted_exhaustion!).getTime() - new Date(b.predicted_exhaustion!).getTime())[0]?.predicted_exhaustion ?? "N/A";

  return (
    <div className="h-screen overflow-hidden bg-background p-4">
      <div className="mx-auto max-w-[1440px] h-full flex flex-col">
        {/* Header */}
        <DashboardHeader
          selectedRange={range}
          onRangeChange={setRange}
          onExport={handleExport}
        />

        {/* Risk Banner */}
        <div className="mt-3">
          <RiskBanner
            toolsAtRisk={toolsAtRisk}
            servicesOverBudget={servicesOverBudget}
            nextExhaustion={nextExhaustion}
          />
        </div>

        {/* Dashboard Grid */}
        <div className="mt-3 flex-1 grid grid-rows-[1fr_auto] gap-3 min-h-0">
          {/* Top Row - Primary Tools */}
          <div className="grid grid-cols-5 gap-4 min-h-0">
            <div className="col-span-3 min-h-0">
              <AnthropicCard
                data={findTool("Anthropic")}
                onRiskClick={() => setRiskPanel({ open: true, type: "anthropic" })}
              />
            </div>
            <div className="col-span-2 min-h-0">
              <AWSCard
                data={data?.aws}
                onRiskClick={() => setRiskPanel({ open: true, type: "aws" })}
              />
            </div>
          </div>

          {/* Bottom Row - Supporting Tools (3 columns) */}
          <div className="grid grid-cols-3 gap-4">
            <ToolCard
              tool="tavily"
              name="Tavily"
              data={findTool("Tavily")}
              sparklineData={
                (findTool("Tavily")?.history && findTool("Tavily")!.history!.length > 0)
                  ? findTool("Tavily")!.history!.map(h => h.credits)
                  : [320, 280, 410, 350, 390, 420, 380]
              }
              onClick={() => setRiskPanel({ open: true, type: "tavily" })}
            />
            <ToolCard
              tool="fullenrich"
              name="FullEnrich"
              data={findTool("FullEnrich")}
              sparklineData={
                (findTool("FullEnrich")?.history && findTool("FullEnrich")!.history!.length > 0)
                  ? findTool("FullEnrich")!.history!.map(h => h.credits)
                  : [180, 220, 190, 240, 210, 250, 230]
              }
              onClick={() => setRiskPanel({ open: true, type: "fullenrich" })}
            />
            <ToolCard
              tool="buyercaddy"
              name="Buyercaddy"
              data={findTool("Buyercaddy")}
              sparklineData={
                (findTool("Buyercaddy")?.history && findTool("Buyercaddy")!.history!.length > 0)
                  ? findTool("Buyercaddy")!.history!.map(h => h.credits)
                  : [80, 120, 90, 110, 140, 100, 130]
              }
              onClick={() => setRiskPanel({ open: true, type: "buyercaddy" })}
            />
          </div>
        </div>
      </div>

      {/* Risk Detail Side Panel */}
      <RiskDetailPanel
        open={riskPanel.open}
        onOpenChange={(open) => setRiskPanel((prev) => ({ ...prev, open }))}
        type={riskPanel.type}
        dashboardData={data}
      />
    </div>
  );
}
