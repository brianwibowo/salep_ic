import { apiConfig } from "@/configs/api-config";
import { Get, unwrapResponse } from "@/utils/api/apiService";
import type { FinalAnalyticsSummary, FinalPackage, FinalReason } from "@/types/salep";

const BASE_URL = `${apiConfig.service_salep}/inaproc/final`;

export interface FinalFilters {
  fiscal_years: number[];
  reasons?: FinalReason[];
  tracks?: string[];
  categories?: string[];
  search?: string;
}

function query(filters: FinalFilters) {
  const params = new URLSearchParams();
  const currentYear = new Date().getFullYear();
  const isDefaultYears =
    Array.isArray(filters.fiscal_years) &&
    filters.fiscal_years.length === 2 &&
    filters.fiscal_years.includes(currentYear - 1) &&
    filters.fiscal_years.includes(currentYear);

  // Jika tahun sama dengan default ([current-1, current]), jangan kirim param fiscal_years
  // agar kompatibel dengan backend staging yang sedang berjalan
  if (!isDefaultYears && filters.fiscal_years?.length) {
    filters.fiscal_years.forEach((year) => params.append("fiscal_years", String(year)));
  }
  filters.reasons?.forEach((reason) => params.append("reasons", reason));
  filters.tracks?.forEach((track) => params.append("tracks", track));
  filters.categories?.forEach((category) => params.append("categories", category));
  if (filters.search) params.set("search", filters.search);
  return params.toString();
}

export const finalAnalyticsService = {
  summary: async (filters: FinalFilters): Promise<FinalAnalyticsSummary> => {
    const suffix = query(filters);
    const response = await Get<FinalAnalyticsSummary>(`${BASE_URL}/summary?${suffix}`);
    return unwrapResponse(response);
  },

  list: async (filters: FinalFilters & { page?: number; limit?: number }): Promise<{ items: FinalPackage[]; pagination: { page: number; limit: number; total: number; pages: number } }> => {
    const suffix = query(filters);
    const params = new URLSearchParams(suffix);
    params.set("page", String(filters.page ?? 1));
    params.set("limit", String(filters.limit ?? 25));
    const response = await Get<{ items: FinalPackage[]; pagination: { page: number; limit: number; total: number; pages: number } }>(`${BASE_URL}?${params.toString()}`);
    return unwrapResponse(response);
  },
};
