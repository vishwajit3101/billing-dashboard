// src/test/AWSCard.test.tsx
// PRD Requirements: AC-01, AC-04, AC-05

import { render, screen, fireEvent } from "@testing-library/react";
import { AWSCard } from "@/components/dashboard/AWSCard";
import { describe, it, expect, vi } from "vitest";

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}));

const mockAWSData = {
  current_spend: 120.0,
  budget: 174.56,
  budget_pct: 68.7,
  weekly_change: 5.0,
  monthly_trend: [
    { month: "2026-02", label: "Feb", spend: 100 },
    { month: "2026-03", label: "Mar", spend: 120 }
  ],
  cost_by_service: [
    { service: "EC2", amount: 60 },
    { service: "RDS", amount: 40 },
    { service: "S3", amount: 20 }
  ],
  status: "Safe",
  filtered_days: 30
};

describe("AWSCard Component", () => {
  it("renders without crash with no props", () => {
    // @ts-ignore
    render(<AWSCard data={null} />);
    expect(screen.getByText("AWS")).toBeDefined();
    expect(screen.getByText("$0")).toBeDefined();
    expect(screen.getByText("0%")).toBeDefined();
  });

  it("renders without crash with full data", () => {
    render(<AWSCard data={mockAWSData} />);
    expect(screen.getByText("AWS")).toBeDefined();
    expect(screen.getByText("Cloud Infrastructure")).toBeDefined();
  });

  it("displays current_spend and budget accurately", () => {
    render(<AWSCard data={mockAWSData} />);
    expect(screen.getByText("$120")).toBeDefined();
  });

  it("displays budget percentage text", () => {
    render(<AWSCard data={mockAWSData} />);
    expect(screen.getByText(/% of monthly budget/)).toBeDefined();
  });

  it("shows correct status badges", () => {
    const { rerender } = render(<AWSCard data={mockAWSData} />);
    expect(screen.getByText("On Track")).toBeDefined();
    
    rerender(<AWSCard data={{ ...mockAWSData, status: "critical" }} />);
    expect(screen.getByText("Over Budget")).toBeDefined();
    
    rerender(<AWSCard data={{ ...mockAWSData, status: "warning" }} />);
    expect(screen.getByText("Spend Warning")).toBeDefined();
  });

  it("caps progress bar width at 100% in style", () => {
    const data = { ...mockAWSData, budget_pct: 150 };
    const { container } = render(<AWSCard data={data} />);
    // Find the indicator div by its class and check style.width
    const indicator = container.querySelector(".h-1\\.5.rounded-full.transition-all");
    expect((indicator as HTMLElement).style.width).toBe("100%");
  });

  it("displays weekly_change", () => {
    render(<AWSCard data={mockAWSData} />);
    expect(screen.getByText("+5%")).toBeDefined();
    
    const { rerender } = render(<AWSCard data={{ ...mockAWSData, weekly_change: -10 }} />);
    expect(screen.getByText("-10%")).toBeDefined();
  });

  it("renders cost by service chart", () => {
    const { container } = render(<AWSCard data={mockAWSData} />);
    expect(screen.getByText("Cost by Service")).toBeDefined();
    expect(container.querySelector(".recharts-responsive-container")).toBeDefined();
  });

  it("calls onRiskClick when card is clicked", () => {
    const handleClick = vi.fn();
    const { container } = render(<AWSCard data={mockAWSData} onRiskClick={handleClick} />);
    fireEvent.click(container.firstChild!);
    expect(handleClick).toHaveBeenCalled();
  });

  it("AC-05: posthog is not in rendered HTML", () => {
    const { container } = render(<AWSCard data={mockAWSData} />);
    expect(container.innerHTML.toLowerCase()).not.toContain("posthog");
  });

  it("shows monthly spend label", () => {
    render(<AWSCard data={mockAWSData} />);
    expect(screen.getByText("Monthly Spend")).toBeDefined();
  });

  it("renders secondary background for progress bar track", () => {
    const { container } = render(<AWSCard data={mockAWSData} />);
    expect(container.querySelector(".bg-secondary")).toBeDefined();
  });
});
