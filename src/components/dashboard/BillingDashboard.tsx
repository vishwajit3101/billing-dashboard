import { DashboardHeader } from "./DashboardHeader";
import { AnthropicCard } from "./AnthropicCard";
import { AWSCard } from "./AWSCard";
import { ToolCard } from "./ToolCard";

export function BillingDashboard() {
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-[1440px]">
        {/* Header */}
        <DashboardHeader />

        {/* Dashboard Grid */}
        <div className="mt-6 grid gap-5">
          {/* Top Row - Primary Tools */}
          <div className="grid grid-cols-5 gap-5">
            {/* Anthropic - Takes 3 columns */}
            <div className="col-span-3">
              <AnthropicCard />
            </div>
            {/* AWS - Takes 2 columns */}
            <div className="col-span-2">
              <AWSCard />
            </div>
          </div>

          {/* Bottom Row - Supporting Tools */}
          <div className="grid grid-cols-3 gap-5">
            <ToolCard
              tool="tavily"
              name="Tavily"
              creditsUsed={7200}
              creditsTotal={10000}
              sparklineData={[320, 280, 410, 350, 390, 420, 380]}
            />
            <ToolCard
              tool="fullenrich"
              name="FullEnrich"
              creditsUsed={4500}
              creditsTotal={5000}
              sparklineData={[180, 220, 190, 240, 210, 250, 230]}
            />
            <ToolCard
              tool="buyercaddy"
              name="Buyercaddy"
              creditsUsed={1200}
              creditsTotal={8000}
              sparklineData={[80, 120, 90, 110, 140, 100, 130]}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
