import { apiConfig } from "@/configs/api-config";
import { Get } from "../utils/api/apiService";
import { User } from "@/types/user";

const BASE = apiConfig.service_user;
export const userService = {
  getAll: async () => {
    const response = await Get<User[]>(`${BASE}/user/list`);
    return response.data;
  },
};
