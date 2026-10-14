"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { sirupService } from "@/services/sirup-service";
import { sirupDataService } from "@/services/sirup-data-service";
import type { InaprocSyncRequest, SirupFilters } from "@/types/salep";

export const sirupQueryKeys = {
  all: ["inaproc-sirup"] as const,
  tracks: () => [...sirupQueryKeys.all, "tracks"] as const,
  list: (filters: SirupFilters & { page?: number; limit?: number }) => [...sirupQueryKeys.all, "list", filters] as const,
};

export function useInaprocTracks(enabled = true) {
  return useQuery({
    queryKey: sirupQueryKeys.tracks(),
    queryFn: sirupService.tracks,
    staleTime: 5 * 60_000,
    enabled,
    retry: false,
  });
}

export function useSirupSync() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: InaprocSyncRequest) => sirupService.sync(request),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["inaproc-final"] });
      await queryClient.invalidateQueries({ queryKey: sirupQueryKeys.all });
    },
  });
}

export function useSirupPackages(
  filters: SirupFilters & { page?: number; limit?: number },
  enabled = true,
) {
  return useQuery({
    queryKey: sirupQueryKeys.list(filters),
    queryFn: () => sirupDataService.list(filters),
    staleTime: 30_000,
    enabled,
  });
}
