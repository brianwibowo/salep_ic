"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  DiscoveryConfig,
  salepDiscoveryService,
} from "@/services/salep-discovery-service";
import { leadsQueryKeys } from "@/hooks/leads/use-leads";

export const schedulerQueryKey = ["salep-scheduler"] as const;

export function useSchedulerStatus(enabled = true) {
  return useQuery({
    queryKey: schedulerQueryKey,
    queryFn: salepDiscoveryService.status,
    enabled,
  });
}

export function useSaveDiscoveryConfig() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (config: DiscoveryConfig) => salepDiscoveryService.saveConfig(config),
    onSuccess: (status) => client.setQueryData(schedulerQueryKey, status),
  });
}

export function useSchedulerAction(action: "start" | "stop" | "trigger") {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => salepDiscoveryService[action](),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: schedulerQueryKey });
      if (action === "trigger") {
        await client.invalidateQueries({ queryKey: leadsQueryKeys.all });
      }
    },
  });
}

export function useManualSearch() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: salepDiscoveryService.search,
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: leadsQueryKeys.all });
      await client.invalidateQueries({ queryKey: schedulerQueryKey });
    },
  });
}
