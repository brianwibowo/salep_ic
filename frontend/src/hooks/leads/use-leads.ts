"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { LeadFilters, salepLeadsService } from "@/services/salep-leads-service";

export const leadsQueryKeys = {
  all: ["salep-leads"] as const,
  list: (filters: LeadFilters) => [...leadsQueryKeys.all, "list", filters] as const,
  stats: () => [...leadsQueryKeys.all, "stats"] as const,
};

export function useLeads(filters: LeadFilters = {}) {
  return useQuery({
    queryKey: leadsQueryKeys.list(filters),
    queryFn: () => salepLeadsService.list(filters),
  });
}

export function useLeadStats() {
  return useQuery({
    queryKey: leadsQueryKeys.stats(),
    queryFn: salepLeadsService.stats,
  });
}

export function useUpdateLeadStatus() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ leadId, status }: { leadId: string; status: "pending" | "valid" | "invalid" }) =>
      salepLeadsService.updateMarketingStatus(leadId, status),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: leadsQueryKeys.all });
    },
    onError: (error: Error) => toast.error(error.message || "Status lead gagal diperbarui"),
  });
}

export function useUpdateSalesStatus() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({
      leadId,
      status,
    }: {
      leadId: string;
      status: "Belum Dihubungi" | "Sedang Dihubungi" | "Closing" | "Batal";
    }) => salepLeadsService.updateSalesStatus(leadId, status),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: leadsQueryKeys.all });
    },
    onError: (error: Error) => toast.error(error.message || "Status tindak lanjut gagal diperbarui"),
  });
}
