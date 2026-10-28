import { apiConfig } from "@/configs/api-config";
import type { PaginatedResponse, PaginationFilter } from "@/types/pagination";
import { Delete, Get, Patch, Post, unwrapResponse } from "@/utils/api/apiService";
import type { Lead, LeadStats, SalesUser, TenderScheduleResponse } from "@/types/salep";

export interface ReviewLeadInput {
  leadId: string;
  status: Lead["marketing_status"];
  expectedVersion: number;
  salesUserId?: string;
  reviewNote?: string;
}

export interface LeadFilters extends PaginationFilter {
  status?: string;
  sales_status?: string;
  source?: string;
  search?: string;
  sales_user_id?: string;
  assignment_status?: "all" | "assigned" | "unassigned";
  date_from?: string;
  date_to?: string;
}

const BASE_URL = apiConfig.service_salep;

export const salepLeadsService = {
  detail: async (leadId: string): Promise<Lead> => unwrapResponse(
    await Get<Lead>(`${BASE_URL}/leads/${encodeURIComponent(leadId)}`),
  ),

  salesUsers: async (includeInactive = false): Promise<SalesUser[]> => unwrapResponse(
    await Get<SalesUser[]>(`${BASE_URL}/leads/sales-users${includeInactive ? "?include_inactive=true" : ""}`),
  ),
  list: async (filters: LeadFilters = {}): Promise<PaginatedResponse<Lead>> => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== "") params.set(key, String(value));
    });
    const query = params.toString();

    const res = await Get<PaginatedResponse<Lead>>(
      `${BASE_URL}/leads${query ? `?${query}` : ""}`,
    );
    return unwrapResponse(res);
  },

  stats: async (): Promise<LeadStats> => {
    const res = await Get<LeadStats>(`${BASE_URL}/leads/stats`);
    return unwrapResponse(res);
  },

  delete: async (leadId: string): Promise<{ deleted: boolean }> => {
    const res = await Delete<{ deleted: boolean }>(
      `${BASE_URL}/leads/${encodeURIComponent(leadId)}`,
    );
    return unwrapResponse(res);
  },

  updateMarketingStatus: async ({
    leadId, status, expectedVersion, salesUserId, reviewNote,
  }: ReviewLeadInput): Promise<Lead> => {
    const payload = {
      marketing_status: status,
      expected_version: expectedVersion,
      sales_user_id: status === "valid" ? salesUserId : null,
      review_note: reviewNote?.trim() || null,
    };
    const res = await Patch<Lead>(
      `${BASE_URL}/leads/${encodeURIComponent(leadId)}/status`,
      payload,
    );
    return unwrapResponse(res);
  },

  updateSalesStatus: async (
    leadId: string,
    sales_status: Lead["sales_status"],
    note: string,
  ): Promise<Lead> => {
    const res = await Patch<Lead>(
      `${BASE_URL}/leads/${encodeURIComponent(leadId)}/sales-status`,
      { sales_status, note },
    );
    return unwrapResponse(res);
  },

  getSpseSchedule: async (leadId: string): Promise<TenderScheduleResponse> => {
    const res = await Get<TenderScheduleResponse>(
      `${BASE_URL}/spse/leads/${encodeURIComponent(leadId)}/jadwal`,
    );
    return unwrapResponse(res);
  },

  analyzeUrl: async (url: string, save_to_sheet = true): Promise<Lead> => {
    const res = await Post<Lead>(`${BASE_URL}/leads/analyze-url`, {
      url,
      save_to_sheet,
    });
    return unwrapResponse(res);
  },
};
