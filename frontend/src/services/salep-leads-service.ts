import { apiConfig } from "@/configs/api-config";
import { Get, Patch, unwrapResponse } from "@/utils/api/apiService";
import { Lead, LeadStats } from "@/types/salep";

export interface LeadFilters {
  offset?: number;
  limit?: number;
  status?: string;
  sales_status?: string;
  source?: string;
  search?: string;
}

const BASE_URL = apiConfig.service_salep;

export const salepLeadsService = {
  list: async (filters: LeadFilters = {}): Promise<Lead[]> => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== "") params.set(key, String(value));
    });
    const query = params.toString();

    const res = await Get<Lead[]>(`${BASE_URL}/leads${query ? `?${query}` : ""}`);
    return unwrapResponse(res);
  },

  stats: async (): Promise<LeadStats> => {
    const res = await Get<LeadStats>(`${BASE_URL}/leads/stats`);
    return unwrapResponse(res);
  },

  updateMarketingStatus: async (
    leadId: string,
    marketing_status: Lead["marketing_status"],
  ): Promise<Lead> => {
    const res = await Patch<Lead>(
      `${BASE_URL}/leads/${encodeURIComponent(leadId)}/status`,
      { marketing_status }
    );
    return unwrapResponse(res);
  },

  updateSalesStatus: async (
    leadId: string,
    sales_status: Lead["sales_status"]
  ): Promise<Lead> => {
    const res = await Patch<Lead>(
      `${BASE_URL}/leads/${encodeURIComponent(leadId)}/sales-status`,
      { sales_status }
    );
    return unwrapResponse(res);
  },
};
