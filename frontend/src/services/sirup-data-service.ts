import { apiConfig } from "@/configs/api-config";
import { Get, unwrapResponse } from "@/utils/api/apiService";
import type { SirupFilters, SirupListResponse } from "@/types/salep";

const BASE_URL = `${apiConfig.service_salep}/inaproc/sirup`;

export const sirupDataService = {
  list: async (
    filters: SirupFilters & { page?: number; limit?: number },
  ): Promise<SirupListResponse> => {
    const params = new URLSearchParams();
    if (filters.fiscal_year) params.set("fiscal_year", String(filters.fiscal_year));
    if (filters.search?.trim()) params.set("search", filters.search.trim());
    if (filters.procurement_type) params.set("procurement_type", filters.procurement_type);
    if (filters.procurement_method) params.set("procurement_method", filters.procurement_method);
    if (filters.date_from) params.set("date_from", filters.date_from);
    if (filters.date_to) params.set("date_to", filters.date_to);
    if (filters.sort) params.set("sort", filters.sort);
    params.set("page", String(filters.page ?? 1));
    params.set("limit", String(filters.limit ?? 25));
    const response = await Get<SirupListResponse>(`${BASE_URL}?${params.toString()}`);
    return unwrapResponse(response);
  },
};
