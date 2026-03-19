// src/test/RiskBanner.test.tsx
// PRD Requirements: AC-01, AC-03, AC-05

import { render, screen } from "@testing-library/react";
import { RiskBanner } from "@/components/dashboard/RiskBanner";
import { describe, it, expect, vi } from "vitest";

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}));

describe("RiskBanner Component", () => {
  it("renders null when no tools at risk and no services over budget", () => {
    const { container } = render(<RiskBanner toolsAtRisk={0} servicesOverBudget={0} nextExhaustion="2026-03-20" />);
    expect(container.firstChild).toBeNull();
  });

  it("renders when tools are at risk", () => {
    render(<RiskBanner toolsAtRisk={2} servicesOverBudget={0} nextExhaustion="2026-03-20" />);
    expect(screen.getByText(/2 tools at risk/)).toBeDefined();
  });

  it("renders when services are over budget", () => {
    render(<RiskBanner toolsAtRisk={0} servicesOverBudget={1} nextExhaustion="2026-03-20" />);
    expect(screen.getByText(/1 service over budget/)).toBeDefined();
  });

  it("shows both counts when both are > 0", () => {
    render(<RiskBanner toolsAtRisk={3} servicesOverBudget={2} nextExhaustion="2026-03-20" />);
    expect(screen.getByText(/3 tools at risk/)).toBeDefined();
    expect(screen.getByText(/2 services over budget/)).toBeDefined();
  });

  it("handles singular/plural grammar correctly", () => {
    const { rerender } = render(<RiskBanner toolsAtRisk={1} servicesOverBudget={1} nextExhaustion="2026-03-20" />);
    expect(screen.getByText(/1 tool at risk/)).toBeDefined();
    expect(screen.queryByText(/tools at risk/)).toBeNull();
    expect(screen.getByText(/1 service over budget/)).toBeDefined();
    expect(screen.queryByText(/services over budget/)).toBeNull();
    
    rerender(<RiskBanner toolsAtRisk={2} servicesOverBudget={2} nextExhaustion="2026-03-20" />);
    expect(screen.getByText(/2 tools at risk/)).toBeDefined();
    expect(screen.getByText(/2 services over budget/)).toBeDefined();
  });

  it("displays the exhaustion date", () => {
    render(<RiskBanner toolsAtRisk={1} servicesOverBudget={0} nextExhaustion="2026-03-20" />);
    expect(screen.getByText("2026-03-20")).toBeDefined();
  });

  it("renders N/A when nextExhaustion is not available", () => {
    render(<RiskBanner toolsAtRisk={1} servicesOverBudget={0} nextExhaustion="N/A" />);
    expect(screen.getByText("N/A")).toBeDefined();
  });

  it("renders Warning icon SVG", () => {
    const { container } = render(<RiskBanner toolsAtRisk={1} servicesOverBudget={0} nextExhaustion="2026-03-20" />);
    expect(container.querySelector("svg")).toBeDefined();
  });

  it("AC-05: posthog is not in rendered HTML", () => {
    const { container } = render(<RiskBanner toolsAtRisk={1} servicesOverBudget={1} nextExhaustion="2026-03-20" />);
    expect(container.innerHTML.toLowerCase()).not.toContain("posthog");
  });

  it("renders for 0 tools but 1 service", () => {
    render(<RiskBanner toolsAtRisk={0} servicesOverBudget={1} nextExhaustion="2026-03-20" />);
    expect(screen.getByText(/1 service over budget/)).toBeDefined();
  });

  it("renders for 1 tool but 0 services", () => {
    render(<RiskBanner toolsAtRisk={1} servicesOverBudget={0} nextExhaustion="2026-03-20" />);
    expect(screen.getByText(/1 tool at risk/)).toBeDefined();
  });

  it("shows pipe separator when both counts > 0", () => {
    render(<RiskBanner toolsAtRisk={1} servicesOverBudget={1} nextExhaustion="2026-03-20" />);
    const separators = screen.getAllByText("|");
    expect(separators.length).toBeGreaterThanOrEqual(1);
  });

  it("handles large counts gracefully", () => {
    render(<RiskBanner toolsAtRisk={99} servicesOverBudget={99} nextExhaustion="2026-03-20" />);
    expect(screen.getByText(/99 tools at risk/)).toBeDefined();
    expect(screen.getByText(/99 services over budget/)).toBeDefined();
  });
});
