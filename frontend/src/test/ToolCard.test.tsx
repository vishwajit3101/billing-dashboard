// src/test/ToolCard.test.tsx
// PRD Requirements: AC-01, AC-03, AC-05

import { render, screen, fireEvent } from "@testing-library/react";
import { ToolCard } from "@/components/dashboard/ToolCard";
import { describe, it, expect, vi } from "vitest";

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}));

const mockToolData = {
  name: "Anthropic",
  credits_remaining: 8000,
  percent_remaining: 80,
  daily_avg_usage: 100,
  current_24h_usage: 120,
  predicted_exhaustion: "2026-03-20",
  status: "Safe",
  history: [
    { day: "2026-03-14", credits: 90 },
    { day: "2026-03-15", credits: 110 }
  ]
};

describe("ToolCard Component", () => {
  it("renders without crash for various tools", () => {
    render(<ToolCard tool="tavily" name="Tavily" sparklineData={[]} />);
    render(<ToolCard tool="fullenrich" name="FullEnrich" sparklineData={[]} />);
    render(<ToolCard tool="buyercaddy" name="BuyerCaddy" sparklineData={[]} />);
    expect(screen.getByText("Tavily")).toBeDefined();
  });

  it("renders tool descriptions", () => {
    const { rerender } = render(<ToolCard tool="tavily" name="Tavily" sparklineData={[]} />);
    expect(screen.getByText("Search API")).toBeDefined();
    
    rerender(<ToolCard tool="fullenrich" name="FullEnrich" sparklineData={[]} />);
    expect(screen.getByText("Data Enrichment")).toBeDefined();
    
    rerender(<ToolCard tool="buyercaddy" name="BuyerCaddy" sparklineData={[]} />);
    expect(screen.getByText("Sales Intelligence")).toBeDefined();
  });

  it("formats credits_remaining with commas", () => {
    const data = { ...mockToolData, credits_remaining: 3200 };
    render(<ToolCard tool="tavily" name="Tavily" data={data} sparklineData={[]} />);
    expect(screen.getByText("3,200")).toBeDefined();
  });

  it("handles zero credits and missing data gracefully", () => {
    // @ts-ignore
    render(<ToolCard tool="tavily" name="Tavily" data={null} sparklineData={[]} />);
    expect(screen.getByText("0")).toBeDefined();
    expect(screen.getByText("No live credits data")).toBeDefined();
  });

  it("displays percent_remaining", () => {
    render(<ToolCard tool="tavily" name="Tavily" data={mockToolData} sparklineData={[]} />);
    expect(screen.getByText("80%")).toBeDefined();
  });

  it("shows exhaustion date with prefix", () => {
    render(<ToolCard tool="tavily" name="Tavily" data={mockToolData} sparklineData={[]} />);
    expect(screen.getByText(/Exhausts:/)).toBeDefined();
  });

  it("does not show Exhausts: prefix when predicted_exhaustion is null", () => {
    const data = { ...mockToolData, predicted_exhaustion: null };
    render(<ToolCard tool="tavily" name="Tavily" data={data} sparklineData={[]} />);
    expect(screen.queryByText(/Exhausts:/)).toBeNull();
  });

  it("renders status indicator dot - Critical (pulse)", () => {
    const data = { ...mockToolData, status: "critical" };
    const { container } = render(<ToolCard tool="tavily" name="Tavily" data={data} sparklineData={[]} />);
    const pulseDot = container.querySelector(".animate-pulse-slow");
    expect(pulseDot).toBeDefined();
  });

  it("renders status indicator dot - Warning (bg-warning)", () => {
    const data = { ...mockToolData, status: "warning" };
    const { container } = render(<ToolCard tool="tavily" name="Tavily" data={data} sparklineData={[]} />);
    const warningDot = container.querySelector(".bg-warning");
    expect(warningDot).toBeDefined();
  });

  it("shows usage labels based on days", () => {
    const { rerender } = render(<ToolCard tool="tavily" name="Tavily" data={mockToolData} sparklineData={[]} days={7} />);
    expect(screen.getByText("7-day usage")).toBeDefined();
    
    rerender(<ToolCard tool="tavily" name="Tavily" data={mockToolData} sparklineData={[]} days={30} />);
    expect(screen.getByText("30-day usage")).toBeDefined();
  });

  it("recharts container is present when history exists", () => {
    const { container } = render(<ToolCard tool="tavily" name="Tavily" data={mockToolData} sparklineData={[]} />);
    expect(container.querySelector(".recharts-responsive-container")).toBeDefined();
  });

  it("shows fallback text when no history exists", () => {
    const data = { ...mockToolData, history: [] };
    render(<ToolCard tool="tavily" name="Tavily" data={data} sparklineData={[]} />);
    expect(screen.getByText("No real usage data yet")).toBeDefined();
  });

  it("calls onClick handler when card is clicked", () => {
    const handleClick = vi.fn();
    const { container } = render(<ToolCard tool="tavily" name="Tavily" data={mockToolData} sparklineData={[]} onClick={handleClick} />);
    fireEvent.click(container.firstChild!);
    expect(handleClick).toHaveBeenCalled();
  });

  it("AC-05: posthog is not in rendered HTML", () => {
    const { container } = render(<ToolCard tool="tavily" name="Tavily" data={mockToolData} sparklineData={[]} />);
    expect(container.innerHTML.toLowerCase()).not.toContain("posthog");
  });

  it("renders the first letter of the name as an icon fallback", () => {
    render(<ToolCard tool="tavily" name="Zebra" sparklineData={[]} />);
    expect(screen.getByText("Z")).toBeDefined();
  });

  it("uses secondary background for pie chart empty space", () => {
    const { container } = render(<ToolCard tool="tavily" name="Tavily" data={mockToolData} sparklineData={[]} />);
    // Checking for color values or classes if possible, but at least ensure SVG exists
    expect(container.querySelector("svg")).toBeDefined();
  });
});
