import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { authService, LoginData } from "@/services/auth-service";
import { LoginForm } from "@/validations/auth-validation";

export function useLogin() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation<LoginData, Error, LoginForm>({
    mutationFn: authService.login,
    onSuccess: (data) => {
      queryClient.clear();
      toast.success(`Welcome back, ${data.user.fullName}!`);
      router.push("/dashboard");
    },
    onError: (error) => {
      toast.error(error.message || "Login gagal, coba lagi");
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation<void, Error, void>({
    mutationFn: authService.logout,
    onSuccess: () => {
      // Reset semua cached queries setelah logout
      queryClient.clear();
      router.push("/login");
    },
    onError: (error) => {
      toast.error(error.message || "Logout gagal");
    },
  });
}
