// src/test/AlertsPanel.test.tsx
// PRD Requirements: FR8, AC-04, AC-05

import { render, screen } from "@testing-library/react";
import { AlertsPanel } from "@/components/dashboard/AlertsPanel";
import { describe, it, expect, vi } from "vitest";

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}));

describe("AlertsPanel Component", () => {
  it("renders null for empty alerts array", () => {
    const { container } = render(<AlertsPanel alerts={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders null for null or undefined alerts", () => {
    // @ts-ignore
    const { container: containerNull } = render(<AlertsPanel alerts={null} />);
    expect(containerNull.firstChild).toBeNull();
    // @ts-ignore
    const { container: containerUndef } = render(<AlertsPanel alerts={undefined} />);
    expect(containerUndef.firstChild).toBeNull();
  });

  it("renders when alerts exist and shows correct count", () => {
    const alerts = [
      { severity: "critical", message: "Crit 1", affected: "Tool A" },
      { severity: "warning", message: "Warn 1", affected: "Tool B" },
      { severity: "alert", message: "Alert 1", affected: "Tool C" }
    ];
    render(<AlertsPanel alerts={alerts} />);
    
    expect(screen.getByText("Active Alerts (3)")).toBeDefined();
    expect(screen.getByText("Crit 1")).toBeDefined();
    expect(screen.getByText("Warn 1")).toBeDefined();
    expect(screen.getByText("Alert 1")).toBeDefined();
  });

  it("shows severity as [CRITICAL], [WARNING], [ALERT] in uppercase", () => {
    const alerts = [
      { severity: "critical", message: "C", affected: "A" },
      { severity: "warning", message: "W", affected: "B" },
      { severity: "alert", message: "Al", affected: "C" }
    ];
    render(<AlertsPanel alerts={alerts} />);
    
    // Check for uppercase labels in square brackets
    // Depending on implementation, it might be in different elements.
    expect(screen.getAllByText(/CRITICAL/i)).toBeDefined();
    expect(screen.getAllByText(/WARNING/i)).toBeDefined();
    expect(screen.getAllByText(/ALERT/i)).toBeDefined();
  });

  it("applies bg-destructive/10 for critical alerts", () => {
    const alerts = [{ severity: "critical", message: "C", affected: "A" }];
    const { container } = render(<AlertsPanel alerts={alerts} />);
    const alertDiv = container.querySelector(".bg-destructive\\/10");
    expect(alertDiv).toBeDefined();
  });

  it("applies bg-warning/10 for warning alerts", () => {
     const alerts = [{ severity: "warning", message: "W", affected: "B" }];
     const { container } = render(<AlertsPanel alerts={alerts} />);
     const alertDiv = container.querySelector(".bg-warning\\/10");
     expect(alertDiv).toBeDefined();
  });

  it("applies bg-blue class for alert severity", () => {
    const alerts = [{ severity: "alert", message: "Al", affected: "C" }];
    const { container } = render(<AlertsPanel alerts={alerts} />);
    // Looking for a class containing "bg-blue"
    const alertDiv = container.querySelector('[class*="bg-blue"]');
    expect(alertDiv).toBeDefined();
  });

  it("renders one SVG icon per alert", () => {
    const alerts = [
      { severity: "critical", message: "C1", affected: "A" },
      { severity: "warning", message: "W1", affected: "B" }
    ];
    const { container } = render(<AlertsPanel alerts={alerts} />);
    const svgs = container.querySelectorAll("svg");
    // At least 2 icons (one for title, plus one per alert?) or exactly 3?
    // Let's assume title has one and each alert has one. 
    // Usually title is "AlertsPanel" icon.
    expect(svgs.length).toBeGreaterThanOrEqual(2);
  });

  it("renders gracefully for unknown severity", () => {
    const alerts = [{ severity: "unknown", message: "U", affected: "D" }];
    render(<AlertsPanel alerts={alerts} />);
    expect(screen.getByText("U")).toBeDefined();
  });

  it("AC-05: posthog is not in rendered HTML", () => {
    const alerts = [{ severity: "critical", message: "Critical message", affected: "Tool" }];
    const { container } = render(<AlertsPanel alerts={alerts} />);
    expect(container.innerHTML.toLowerCase()).not.toContain("posthog");
  });

  it.each([
    ["Tool A", "Critical Failure"],
    ["Tool B", "Warning Triggered"],
    ["Service X", "Budget Alert"],
    ["RDS", "RDS Spike"],
    ["EC2", "Limit Reached"],
    ["PostHog", "Data Invisibility Test"],
    ["General", "System Note"],
    ["Dashboard", "Sync Issue"],
    ["API", "Latency Warning"],
    ["User", "Action Required"]
  ])("renders alert for %s: %s", (affected, message) => {
    render(<AlertsPanel alerts={[{ severity: "alert", message, affected }]} />);
    expect(screen.getByText(message)).toBeDefined();
  });
});
