import { apiConfig } from "@/configs/api-config";
import { Get, Post, unwrapResponse } from "@/utils/api/apiService";
import { SalepSession } from "@/types/salep";

const BASE_URL = apiConfig.service_salep;

export const salepAuthService = {
  login: async (username: string, password: string): Promise<SalepSession> => {
    const res = await Post<SalepSession>(`${BASE_URL}/auth/login`, { username, password });
    return unwrapResponse(res);
  },

  me: async (): Promise<SalepSession> => {
    const res = await Get<SalepSession>(`${BASE_URL}/auth/me`);
    return unwrapResponse(res);
  },

  logout: async (): Promise<void> => {
    const res = await Post<{ ok: boolean }>(`${BASE_URL}/auth/logout`);
    unwrapResponse(res);
  },
};
