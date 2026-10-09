import { apiConfig } from "@/configs/api-config";
import { PaginationFilter } from "@/types/pagination";
import { Transaction } from "@/types/transaction";
import { Delete, Get, Post, Put } from "@/utils/api/apiService";

const BASE = apiConfig.service_user;

export interface TransactionFilter extends PaginationFilter {
  invoice_number?: string;
  payment_status?: string;
  status?: string;
}

export interface TransactionForm {
  invoice_number: string;
  subtotal: number;
  discount_amount: number;
  total_amount: number;
  payment_method: string;
  payment_status: string;
  cash_received: number;
  change_amount: number;
  status: string;
  transaction_date: Date;
}

export const financeService = {
  getTransactions: async (
    filters?: TransactionFilter,
  ): Promise<Transaction[]> => {
    const params = new URLSearchParams();
    if (filters?.invoice_number)
      params.set("invoice_number", filters.invoice_number);
    if (filters?.payment_status)
      params.set("payment_status", filters.payment_status);
    if (filters?.status) params.set("status", filters.status);
    if (filters?.page) params.set("page", String(filters.page));
    if (filters?.limit) params.set("limit", String(filters.limit));

    const query = params.toString();
    const res = await Get<Transaction[]>(
      `${BASE}/finance/transactions${query ? `?${query}` : ""}`,
    );
    if (!res.status || !res.data) throw new Error(res.message);
    return res.data;
  },

  getTransactionById: async (id: string): Promise<Transaction> => {
    const res = await Get<Transaction>(`${BASE}/finance/transactions/${id}`);
    if (!res.status || !res.data) throw new Error(res.message);
    return res.data;
  },

  createTransaction: async (data: TransactionForm): Promise<Transaction> => {
    const res = await Post<Transaction, TransactionForm>(
      `${BASE}/finance/transactions`,
      data,
    );
    if (!res.status || !res.data) throw new Error(res.message);
    return res.data;
  },

  updateTransaction: async (
    id: string,
    data: Partial<TransactionForm>,
  ): Promise<Transaction> => {
    const res = await Put<Transaction, Partial<TransactionForm>>(
      `${BASE}/finance/transactions/${id}`,
      data,
    );
    if (!res.status || !res.data) throw new Error(res.message);
    return res.data;
  },

  deleteTransaction: async (id: string): Promise<void> => {
    const res = await Delete(`${BASE}/finance/transactions/${id}`);
    if (!res.status) throw new Error(res.message);
  },
};
