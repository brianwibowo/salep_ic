import { apiConfig } from "@/configs/api-config";
import { Delete, Get, Post, unwrapResponse } from "@/utils/api/apiService";

const BASE_URL = apiConfig.service_salep;

export type NewAccountRole = "marketing" | "sales";

export interface AdminUser {
  user_id: string;
  username: string;
  role: NewAccountRole | "super_admin";
  active: boolean;
  created_at: number;
}

export const salepAdminService = {
  listUsers: async (): Promise<AdminUser[]> => {
    const res = await Get<AdminUser[]>(`${BASE_URL}/admin/users`);
    return unwrapResponse(res);
  },

  createUser: async (input: {
    username: string;
    password: string;
    role: NewAccountRole;
  }) => {
    const res = await Post<{
      user_id: string;
      username: string;
      role: NewAccountRole;
    }>(`${BASE_URL}/admin/users`, input);

    return unwrapResponse(res);
  },

  deactivateUser: async (username: string) => {
    const res = await Delete<{
      user_id: string;
      username: string;
      role: AdminUser["role"];
      active: boolean;
    }>(`${BASE_URL}/admin/users/${encodeURIComponent(username)}`);

    return unwrapResponse(res);
  },
};
