"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { salepAuthService } from "@/services/salep-auth-service";
import { SalepRole } from "@/types/salep";

export const sessionQueryKey = ["salep-session"] as const;

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
    mutationFn: (role: SalepRole) => salepAuthService.login(role),
    onSuccess: (session) => {
      queryClient.setQueryData(sessionQueryKey, session);
      toast.success(`Masuk sebagai ${session.role === "marketing" ? "Marketing" : "Sales"}`);
      router.replace("/dashboard");
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
