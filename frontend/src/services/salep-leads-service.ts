import { salepApi } from "@/services/salep-api";
import { Lead, LeadStats } from "@/types/salep";

export interface LeadFilters {
  offset?: number;
  limit?: number;
  status?: string;
  sales_status?: string;
  source?: string;
  search?: string;
}

export const salepLeadsService = {
  list: (filters: LeadFilters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== "") params.set(key, String(value));
    });
    return salepApi<Lead[]>(`/api/v1/leads?${params.toString()}`);
  },
  stats: () => salepApi<LeadStats>("/api/v1/leads/stats"),
  updateMarketingStatus: (leadId: string, marketing_status: Lead["marketing_status"]) =>
    salepApi<Lead>(`/api/v1/leads/${encodeURIComponent(leadId)}/status`, {
      method: "PATCH",
      body: JSON.stringify({ marketing_status }),
    }),
  updateSalesStatus: (leadId: string, sales_status: Lead["sales_status"]) =>
    salepApi<Lead>(`/api/v1/leads/${encodeURIComponent(leadId)}/sales-status`, {
      method: "PATCH",
      body: JSON.stringify({ sales_status }),
    }),
};
