"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { salepAuthService } from "@/services/salep-auth-service";

export const sessionQueryKey = ["salep-session"] as const;
type LoginCredentials = { username: string; password: string };

export function useSession() {
  return useQuery({
    queryKey: sessionQueryKey,
    queryFn: salepAuthService.me,
    retry: false,
    staleTime: 30_000,
  });
}

export function useLogin() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ username, password }: LoginCredentials) => salepAuthService.login(username, password),
    onSuccess: (session) => {
      queryClient.setQueryData(sessionQueryKey, session);
      const roleLabel = {
        marketing: "Marketing",
        sales: "Sales",
        super_admin: "Super Admin",
      }[session.role];
      toast.success(`Masuk sebagai ${roleLabel}`);
      router.replace(session.role === "super_admin" ? "/admin/users" : "/dashboard");
    },
    onError: (error: Error) => toast.error(error.message || "Login gagal"),
  });
}

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: salepAuthService.logout,
    onSettled: async () => {
      queryClient.clear();
      router.replace("/login");
    },
    onError: (error: Error) => toast.error(error.message || "Logout gagal"),
  });
}
