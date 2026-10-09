import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  financeService,
  TransactionFilter,
  TransactionForm,
} from "@/services/finance-service";

export const financeKeys = {
  all: ["finance"] as const,
  transactions: (filters?: TransactionFilter) =>
    [...financeKeys.all, "transactions", filters] as const,
  transaction: (id: string) =>
    [...financeKeys.all, "transactions", id] as const,
};

export function useTransactions(filters?: TransactionFilter) {
  return useQuery({
    queryKey: financeKeys.transactions(filters),
    queryFn: () => financeService.getTransactions(filters),
  });
}

export function useTransaction(id: string) {
  return useQuery({
    queryKey: financeKeys.transaction(id),
    queryFn: () => financeService.getTransactionById(id),
    enabled: !!id, // hanya fetch kalau id ada
  });
}

export function useCreateTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TransactionForm) =>
      financeService.createTransaction(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: financeKeys.transactions() });
      toast.success("Transaksi berhasil dibuat");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Gagal membuat transaksi");
    },
  });
}

export function useUpdateTransaction(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<TransactionForm>) =>
      financeService.updateTransaction(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: financeKeys.transactions() });
      queryClient.invalidateQueries({ queryKey: financeKeys.transaction(id) });
      toast.success("Transaksi berhasil diupdate");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Gagal mengupdate transaksi");
    },
  });
}

export function useDeleteTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => financeService.deleteTransaction(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: financeKeys.transactions() });
      toast.success("Transaksi berhasil dihapus");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Gagal menghapus transaksi");
    },
  });
}
