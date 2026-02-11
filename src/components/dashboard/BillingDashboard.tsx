import { useState } from "react";
import { DashboardHeader } from "./DashboardHeader";
import { RiskBanner } from "./RiskBanner";
import { AnthropicCard } from "./AnthropicCard";
import { AWSCard } from "./AWSCard";
import { ToolCard } from "./ToolCard";
import { RiskDetailPanel } from "./RiskDetailPanel";

export function BillingDashboard() {
  const [riskPanel, setRiskPanel] = useState<{ open: boolean; type: "anthropic" | "aws" | "tavily" | "fullenrich" | "buyercaddy" }>({
    open: false,
    type: "anthropic",
  });

  return (
    <div className="h-screen overflow-hidden bg-background p-4">
      <div className="mx-auto max-w-[1440px] h-full flex flex-col">
        {/* Header */}
        <DashboardHeader />

        {/* Risk Banner */}
        <div className="mt-3">
          <RiskBanner toolsAtRisk={2} servicesOverBudget={1} nextExhaustion="Feb 6" />
        </div>

        {/* Dashboard Grid */}
        <div className="mt-3 flex-1 grid grid-rows-[1fr_auto] gap-3 min-h-0">
          {/* Top Row - Primary Tools */}
          <div className="grid grid-cols-5 gap-4 min-h-0">
            <div className="col-span-3 min-h-0">
              <AnthropicCard onRiskClick={() => setRiskPanel({ open: true, type: "anthropic" })} />
            </div>
            <div className="col-span-2 min-h-0">
              <AWSCard onRiskClick={() => setRiskPanel({ open: true, type: "aws" })} />
            </div>
          </div>

          {/* Bottom Row - Supporting Tools (3 columns) */}
          <div className="grid grid-cols-3 gap-4">
            <ToolCard
              tool="tavily"
              name="Tavily"
              creditsUsed={7200}
              creditsTotal={10000}
              sparklineData={[320, 280, 410, 350, 390, 420, 380]}
              onClick={() => setRiskPanel({ open: true, type: "tavily" })}
            />
            <ToolCard
              tool="fullenrich"
              name="FullEnrich"
              creditsUsed={4500}
              creditsTotal={5000}
              sparklineData={[180, 220, 190, 240, 210, 250, 230]}
              onClick={() => setRiskPanel({ open: true, type: "fullenrich" })}
            />
            <ToolCard
              tool="buyercaddy"
              name="Buyercaddy"
              creditsUsed={1200}
              creditsTotal={8000}
              sparklineData={[80, 120, 90, 110, 140, 100, 130]}
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
      />
    </div>
  );
}
