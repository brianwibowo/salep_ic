"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { sirupService } from "@/services/sirup-service";
import type { InaprocSyncRequest } from "@/types/salep";

export const sirupQueryKeys = {
  all: ["inaproc-sirup"] as const,
  tracks: () => [...sirupQueryKeys.all, "tracks"] as const,
};

export function useInaprocTracks() {
  return useQuery({
    queryKey: sirupQueryKeys.tracks(),
    queryFn: sirupService.tracks,
    staleTime: 5 * 60_000,
  });
}

export function useSirupSync() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: InaprocSyncRequest) => sirupService.sync(request),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["inaproc-final"] });
    },
  });
}
