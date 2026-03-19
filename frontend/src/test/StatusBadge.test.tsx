// src/test/StatusBadge.test.tsx
// PRD Requirements: AC-01, AC-05

import { render, screen } from "@testing-library/react";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { describe, it, expect, vi } from "vitest";

// Mock ResizeObserver as requested
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}));

describe("StatusBadge Component", () => {
  it("renders label text", () => {
    render(<StatusBadge status="safe" label="Healthy" />);
    expect(screen.getByText("Healthy")).toBeDefined();
  });

  it("applies critical styling and destructive class", () => {
    const { container } = render(<StatusBadge status="critical" label="Critical" />);
    // According to StatusBadge.tsx: config.bgClass is "bg-destructive/10"
    expect(container.firstChild).toHaveClass("bg-destructive/10");
    expect(container.firstChild).toHaveClass("text-destructive");
  });

  it("applies warning styling", () => {
    const { container } = render(<StatusBadge status="warning" label="Warning" />);
    expect(container.firstChild).toHaveClass("bg-warning/10");
    expect(container.firstChild).toHaveClass("text-warning");
  });

  it("applies safe styling", () => {
    const { container } = render(<StatusBadge status="safe" label="Safe" />);
    expect(container.firstChild).toHaveClass("bg-success/10");
    expect(container.firstChild).toHaveClass("text-success");
  });

  it("renders an SVG icon", () => {
    const { container } = render(<StatusBadge status="safe" label="Safe" />);
    const svg = container.querySelector("svg");
    expect(svg).toBeDefined();
    // Lucide names can vary, checking for "lucide" and "icon" related classes
    expect(svg).toHaveClass("lucide");
  });

  it("renders gracefully for unknown status", () => {
    // Should fallback to safe
    const { container } = render(<StatusBadge status="unknown" label="Unknown" />);
    expect(container.firstChild).toHaveClass("bg-success/10");
  });

  it("is case-insensitive for status prop", () => {
    const { container } = render(<StatusBadge status="CRITICAL" label="Critical" />);
    expect(container.firstChild).toHaveClass("bg-destructive/10");
  });

  it("supports optional className prop", () => {
    const { container } = render(<StatusBadge status="safe" label="Safe" className="custom-class" />);
    expect(container.firstChild).toHaveClass("custom-class");
  });

  it("AC-05: posthog is not in rendered HTML", () => {
    const { container } = render(<StatusBadge status="safe" label="Healthy Label" />);
    expect(container.innerHTML.toLowerCase()).not.toContain("posthog");
  });

  it.each([
    ["critical", "Critical", "bg-destructive/10"],
    ["warning", "Warning", "bg-warning/10"],
    ["safe", "Safe", "bg-success/10"],
    ["SAFE", "Safe", "bg-success/10"],
    ["CRITICAL", "Critical", "bg-destructive/10"],
    ["WARNING", "Warning", "bg-warning/10"],
    ["unknown", "Unknown", "bg-success/10"],
    ["expired", "Expired", "bg-success/10"],
    ["low", "Low", "bg-success/10"],
    ["high", "High", "bg-success/10"],
  ])("Status %s renders correctly", (status, label, expectedClass) => {
    const { container } = render(<StatusBadge status={status} label={label} />);
    expect(container.firstChild).toHaveClass(expectedClass);
    expect(screen.getByText(label)).toBeDefined();
  });

  it.each([
    "Custom 1", "Custom 2", "Custom 3", "Custom 4", "Custom 5",
    "99.9%", "0%", "N/A", "Active", "Pending"
  ])("renders various label text: %s", (label) => {
    render(<StatusBadge status="safe" label={label} />);
    expect(screen.getByText(label)).toBeDefined();
  });
});
