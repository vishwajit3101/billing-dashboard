// billing-dashboard/src/hooks/useDashboard.ts
import { useQuery } from "@tanstack/react-query";
import { fetchDashboardData } from "@/lib/api";

export function useDashboard(days: number = 30) {
    return useQuery({
        queryKey: ["dashboard", days],
        queryFn: () => fetchDashboardData(days),
        refetchInterval: 1000 * 60 * 5, // Refetch every 5 minutes
    });
}
