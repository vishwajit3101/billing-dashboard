// billing-dashboard/src/lib/api.ts

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export interface ToolSnapshot {
    recorded_at: string;
    credits_remaining: number;
    percent_remaining: number;
    daily_avg_usage: number;
    predicted_exhaustion: string | null;
    status: string;
    total_credits: number;
}

export interface ToolData {
    name: string;
    credits_remaining: number;
    percent_remaining: number;
    daily_avg_usage: number;
    current_24h_usage?: number;
    predicted_exhaustion: string | null;
    status: string;
    history?: { day: string, credits: number }[];
    snapshots?: ToolSnapshot[];
}

export interface AWSService {
    service: string;
    amount: number;
}

export interface AWSData {
    current_spend: number;
    budget: number;
    budget_pct: number;
    weekly_change?: number;
    monthly_trend: { month: string, label: string, spend: number }[];
    cost_by_service: AWSService[];
    status: string;
    filtered_days: number;
}

export interface Alert {
    severity: string;
    message: string;
    affected: string;
}

export interface DashboardResponse {
    tools: ToolData[];
    aws: AWSData;
    alerts: Alert[];
    alert_count: number;
    last_updated: string;
    filtered_days: number;
    date_range: {
        from: string;
        to: string;
    };
}

export async function fetchDashboardData(days: number = 30): Promise<DashboardResponse> {
    const response = await fetch(`${API_BASE_URL}/dashboard?days=${days}`);
    if (!response.ok) {
        throw new Error('Failed to fetch dashboard data');
    }
    return response.json();
}

export function getExportUrl(days: number = 30, format: 'json' | 'csv' = 'csv'): string {
    return `${API_BASE_URL}/export?days=${days}&format=${format}`;
}
