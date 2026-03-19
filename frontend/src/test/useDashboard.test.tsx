// src/test/useDashboard.test.tsx
// PRD Requirements: FR7, FR9, AC-05

import { renderHook, waitFor } from "@testing-library/react";
import { useDashboard } from "@/hooks/useDashboard";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import React from 'react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

const mockResponse = {
  tools: [
    { name: "Anthropic", credits_remaining: 100, percent_remaining: 50, daily_avg_usage: 10, status: "Safe" },
    { name: "Tavily", credits_remaining: 100, percent_remaining: 50, daily_avg_usage: 10, status: "Safe" },
    { name: "FullEnrich", credits_remaining: 100, percent_remaining: 50, daily_avg_usage: 10, status: "Safe" },
    { name: "Buyercaddy", credits_remaining: 100, percent_remaining: 50, daily_avg_usage: 10, status: "Safe" }
  ],
  aws: { current_spend: 120 },
  alerts: [],
  alert_count: 0
};

describe("useDashboard Hook", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
    queryClient.clear();
  });

  it("starts in loading state", () => {
    (global.fetch as any).mockReturnValue(new Promise(() => {})); // Never resolves
    const { result } = renderHook(() => useDashboard(), { wrapper });
    expect(result.current.isLoading).toBe(true);
  });

  it("returns data after successful fetch", async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockResponse
    });
    
    const { result } = renderHook(() => useDashboard(), { wrapper });
    
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    
    expect(result.current.data?.tools).toHaveLength(4);
    expect(result.current.data?.aws.current_spend).toBe(120);
  });

  it("handles fetch with specified days", async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockResponse
    });
    
    renderHook(() => useDashboard(7), { wrapper });
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("days=7"));
  });

  it("handles fetch errors", async () => {
     (global.fetch as any).mockResolvedValue({
      ok: false
    });
    
    const { result } = renderHook(() => useDashboard(), { wrapper });
    
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  it("handles network throws", async () => {
     (global.fetch as any).mockRejectedValue(new Error("Network Error"));
    
    const { result } = renderHook(() => useDashboard(), { wrapper });
    
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toContain("Network Error");
  });
});
