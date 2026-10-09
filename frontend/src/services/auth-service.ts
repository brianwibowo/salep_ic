import { Post } from "@/utils/api/apiService";
import { apiConfig } from "@/configs/api-config";
import { LoginForm } from "@/validations/auth-validation";

export interface LoginData {
  accessToken: string;
  refreshToken: string;
  user: {
    id: string;
    email: string;
    fullName: string;
  };
}

const BASE = apiConfig.service_user;

export const authService = {
  login: async (data: LoginForm): Promise<LoginData> => {
    const res = await Post<LoginData, LoginForm>(`${BASE}/auth/login`, data);
    if (!res.status || !res.data) throw new Error(res.message);

    if (typeof window !== "undefined") {
      localStorage.setItem("accessToken", res.data.accessToken);
      localStorage.setItem("refreshToken", res.data.refreshToken);
      localStorage.setItem("user", JSON.stringify(res.data.user));
    }

    return res.data;
  },

  logout: async (): Promise<void> => {
    const user = authService.getCurrentUser();
    if (!user) return;

    const res = await Post(`${BASE}/auth/logout/${user.id}`, {
      refreshToken: user.refreshToken,
    });

    if (!res.status) throw new Error(res.message);

    if (typeof window !== "undefined") {
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("user");
    }
  },

  getCurrentUser: (): (LoginData["user"] & { refreshToken: string }) | null => {
    if (typeof window === "undefined") return null;
    const userStr = localStorage.getItem("user");
    const refreshToken = localStorage.getItem("refreshToken");
    return userStr && refreshToken
      ? { ...JSON.parse(userStr), refreshToken }
      : null;
  },

  isAuthenticated: (): boolean => {
    if (typeof window === "undefined") return false;
    return !!localStorage.getItem("accessToken");
  },
};
