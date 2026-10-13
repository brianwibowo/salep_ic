"use client";

import { useQuery } from "@tanstack/react-query";
import { finalAnalyticsService, type FinalFilters } from "@/services/final-analytics-service";

export const finalQueryKeys = {
  all: ["inaproc-final"] as const,
  summary: (filters: FinalFilters) => [...finalQueryKeys.all, "summary", filters] as const,
  list: (filters: FinalFilters) => [...finalQueryKeys.all, "list", filters] as const,
};

export function useFinalSummary(filters: FinalFilters) {
  return useQuery({
    queryKey: finalQueryKeys.summary(filters),
    queryFn: () => finalAnalyticsService.summary(filters),
    staleTime: 60_000,
  });
}

export function useFinalPackages(filters: FinalFilters & { page?: number; limit?: number }) {
  return useQuery({
    queryKey: finalQueryKeys.list(filters),
    queryFn: () => finalAnalyticsService.list(filters),
    staleTime: 60_000,
  });
}
