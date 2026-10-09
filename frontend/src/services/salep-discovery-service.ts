import { apiConfig } from "@/configs/api-config";
import { Get, Post, Put, unwrapResponse } from "@/utils/api/apiService";
import { SchedulerStatus, SearchResult } from "@/types/salep";
import {
  DiscoveryConfig,
  ManualSearchInput,
} from "@/validations/salep-validation";

export type {
  DiscoveryConfig,
  ManualSearchInput,
} from "@/validations/salep-validation";

const BASE_URL = apiConfig.service_salep;

export const salepDiscoveryService = {
  status: async (): Promise<SchedulerStatus> => {
    const res = await Get<SchedulerStatus>(`${BASE_URL}/scheduler/status`);
    return unwrapResponse(res);
  },

  saveConfig: async (config: DiscoveryConfig): Promise<SchedulerStatus> => {
    const res = await Put<SchedulerStatus>(`${BASE_URL}/scheduler/config`, config);
    return unwrapResponse(res);
  },

  trigger: async (): Promise<{ status: string; message: string }> => {
    const res = await Post<{ status: string; message: string }>(`${BASE_URL}/scheduler/trigger`);
    return unwrapResponse(res);
  },

  start: async (): Promise<{ status: string }> => {
    const res = await Post<{ status: string }>(`${BASE_URL}/scheduler/start`);
    return unwrapResponse(res);
  },

  stop: async (): Promise<{ status: string }> => {
    const res = await Post<{ status: string }>(`${BASE_URL}/scheduler/stop`);
    return unwrapResponse(res);
  },

  search: async (input: ManualSearchInput): Promise<SearchResult> => {
    const res = await Post<SearchResult>(`${BASE_URL}/search`, input);
    return unwrapResponse(res);
  },
};
