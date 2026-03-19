// src/test/api.test.ts
// PRD Requirements: FR7, FR10, AC-01, AC-03, AC-05

import { fetchDashboardData, getExportUrl } from "@/lib/api";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockResponse = {
  tools: [
    { name: "Anthropic", credits_remaining: 100, percent_remaining: 50, daily_avg_usage: 10, status: "Safe" },
    { name: "Tavily", credits_remaining: 100, percent_remaining: 50, daily_avg_usage: 10, status: "Safe" },
    { name: "FullEnrich", credits_remaining: 100, percent_remaining: 50, daily_avg_usage: 10, status: "Safe" },
    { name: "Buyercaddy", credits_remaining: 100, percent_remaining: 50, daily_avg_usage: 10, status: "Safe" }
  ],
  aws: { current_spend: 100 },
  alerts: [],
  alert_count: 0,
  last_updated: "2026-03-15T10:00:00Z",
  filtered_days: 30,
  date_range: { from: "2026-02-14", to: "2026-03-15" }
};

describe("API Library", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it("fetchDashboardData calls URL with days=30 by default", async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockResponse
    });
    
    await fetchDashboardData();
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/dashboard?days=30"));
  });

  it("fetchDashboardData calls URL with specified days", async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockResponse
    });
    
    await fetchDashboardData(7);
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/dashboard?days=7"));
  });

  it("fetchDashboardData returns correctly formatted data", async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockResponse
    });
    
    const data = await fetchDashboardData();
    expect(data.tools).toHaveLength(4);
    expect(data.aws.current_spend).toBe(100);
    expect(data.alert_count).toBe(0);
  });

  it("fetchDashboardData throws on error response", async () => {
    (global.fetch as any).mockResolvedValue({
      ok: false
    });
    
    await expect(fetchDashboardData()).rejects.toThrow("Failed to fetch dashboard data");
  });

  it("getExportUrl returns correct format and days", () => {
    const url = getExportUrl(7, "json");
    expect(url).toContain("/export");
    expect(url).toContain("days=7");
    expect(url).toContain("format=json");
    expect(url.startsWith("http")).toBe(true);
  });

  it("getExportUrl defaults to csv and 30 days", () => {
    const url = getExportUrl();
    expect(url).toContain("days=30");
    expect(url).toContain("format=csv");
  });
});
