import { useQuery } from "@tanstack/react-query";
import { userService } from "@/services/user-service";

export const userKeys = {
  all: ["users"] as const,
  list: () => [...userKeys.all, "list"] as const,
};

export function useUsers() {
  return useQuery({
    queryKey: userKeys.list(),
    queryFn: userService.getAll,
  });
}
