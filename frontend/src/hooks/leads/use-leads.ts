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

export function useDeleteLead() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: salepLeadsService.delete,
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: leadsQueryKeys.all });
      toast.success("Lead berhasil dihapus");
    },
    onError: (error: Error) => toast.error(error.message || "Lead gagal dihapus"),
  });
}

export function useUpdateLeadStatus() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({
      leadId,
      status,
      reviewNote,
    }: {
      leadId: string;
      status: "pending" | "valid" | "invalid";
      reviewNote?: string;
    }) => salepLeadsService.updateMarketingStatus(leadId, status, reviewNote),
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
      note,
    }: {
      leadId: string;
      status: "Belum Dihubungi" | "Sedang Dihubungi" | "Closing" | "Batal";
      note?: string;
    }) =>
      salepLeadsService.updateSalesStatus(
        leadId,
        status,
        note?.trim() || "Pembaruan status tindak lanjut",
      ),
    onSuccess: async () => {
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

