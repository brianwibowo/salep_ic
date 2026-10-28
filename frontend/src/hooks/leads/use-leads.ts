"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { LeadFilters, salepLeadsService } from "@/services/salep-leads-service";
import type { Lead } from "@/types/salep";

export const leadsQueryKeys = {
  all: ["salep-leads"] as const,
  list: (filters: LeadFilters) => [...leadsQueryKeys.all, "list", filters] as const,
  stats: () => [...leadsQueryKeys.all, "stats"] as const,
  detail: (id: string) => [...leadsQueryKeys.all, "detail", id] as const,
};

export function useLeadDetail(lead: Lead) {
  return useQuery({
    queryKey: leadsQueryKeys.detail(lead.lead_id),
    queryFn: () => salepLeadsService.detail(lead.lead_id),
    initialData: lead,
    staleTime: 0,
    refetchOnWindowFocus: false,
  });
}

export function useAssignableSales(enabled: boolean, includeInactive = false) {
  return useQuery({
    queryKey: ["salep-sales-users", includeInactive],
    queryFn: () => salepLeadsService.salesUsers(includeInactive),
    enabled,
    staleTime: 0,
  });
}

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

export function useDeleteLead() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: salepLeadsService.delete,
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: leadsQueryKeys.all });
      toast.success("Lead dihapus dari daftar aktif. Riwayat tetap tersimpan.");
    },
    onError: (error: Error) => toast.error(error.message || "Lead gagal dihapus"),
  });
}

export function useUpdateLeadStatus(onUpdated: (lead: Lead) => void) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: salepLeadsService.updateMarketingStatus,
    onSuccess: async (lead) => {
      // Notify before the versioned form remounts when the detail cache changes.
      onUpdated(lead);
      client.setQueryData(leadsQueryKeys.detail(lead.lead_id), lead);
      await client.invalidateQueries({ queryKey: leadsQueryKeys.all });
      toast.success(lead.marketing_status === "valid" ? "Review dan assignment tersimpan" : "Review tersimpan");
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
      note,
    }: {
      leadId: string;
      status: "Belum Dihubungi" | "Sedang Dihubungi" | "Closing" | "Batal";
      note: string;
    }) =>
      salepLeadsService.updateSalesStatus(
        leadId,
        status,
        note.trim(),
      ),
    onSuccess: async (lead) => {
      client.setQueryData(leadsQueryKeys.detail(lead.lead_id), lead);
      await client.invalidateQueries({ queryKey: leadsQueryKeys.all });
    },
    onError: (error: Error) => toast.error(error.message || "Status tindak lanjut gagal diperbarui"),
  });
}

export function useSpseSchedule(leadId: string | null) {
  return useQuery({
    queryKey: [...leadsQueryKeys.all, "spse-schedule", leadId] as const,
    queryFn: () => salepLeadsService.getSpseSchedule(leadId!),
    enabled: Boolean(leadId),
  });
}

export function useAnalyzeUrl() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({
      url,
      save_to_sheet = true,
    }: {
      url: string;
      save_to_sheet?: boolean;
    }) => salepLeadsService.analyzeUrl(url, save_to_sheet),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: leadsQueryKeys.all });
    },
  });
}

