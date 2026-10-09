import { salepApi } from "@/services/salep-api";
import { SalepRole, SalepSession } from "@/types/salep";

export const salepAuthService = {
  login: (role: SalepRole) =>
    salepApi<SalepSession>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ role }),
    }),
  me: () => salepApi<SalepSession>("/api/v1/auth/me"),
  logout: () =>
    salepApi<{ ok: boolean }>("/api/v1/auth/logout", { method: "POST" }),
};
