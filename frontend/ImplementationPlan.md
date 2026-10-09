API Layer Restructuring — TanStack React Query + Service Layer
Restructure cara fetching data agar lebih clean dan konsisten menggunakan React Query + service layer.

Proposed Structure
src/
├── utils/
│   └── api/
│       ├── axiosInstance.ts     ← tetap, minor fix (buka noRetryRoutes)
│       └── apiService.ts        ← tetap, tidak berubah
└── services/                    ← PINDAH ke sini (dari utils/services/)
    ├── auth-service.ts          ← sudah ada, tetap
    ├── finance-service.ts       ← contoh nanti
    └── inventory-service.ts     ← contoh nanti
└── hooks/                       ← BARU: React Query hooks per fitur
    ├── auth/
    │   └── use-auth.ts
    ├── finance/
    │   └── use-finance.ts
    └── inventory/
        └── use-inventory.ts
Pola yang Diusulkan
1. Service Layer (sudah ada, sedikit penyesuaian)
Service layer bertugas hanya untuk memanggil API dan mengembalikan data mentah. Khusus untuk mutasi (login, logout, create, update, delete), service throw error agar React Query bisa menangkapnya via onError.

ts
// services/finance-service.ts
import { Get, Post, Put, Delete } from "@/utils/api/apiService";
import { apiConfig } from "@/configs/api-config";
const BASE = apiConfig.service_user;
export const financeService = {
  getTransactions: async () => {
    const res = await Get<Transaction[]>(`${BASE}/finance/transactions`);
    if (!res.status) throw new Error(res.message);
    return res.data;
  },
  createTransaction: async (data: TransactionForm) => {
    const res = await Post<Transaction>(`${BASE}/finance/transactions`, data);
    if (!res.status) throw new Error(res.message);
    return res.data;
  },
};
2. React Query Hooks
Hooks bertugas sebagai bridge antara komponen dan service:

useQuery untuk fetching (GET)
useMutation untuk aksi (POST, PUT, DELETE)
ts
// hooks/finance/use-finance.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { financeService } from "@/services/finance-service";
import { toast } from "sonner";
export const financeKeys = {
  all: ["finance"] as const,
  transactions: () => [...financeKeys.all, "transactions"] as const,
};
export function useTransactions() {
  return useQuery({
    queryKey: financeKeys.transactions(),
    queryFn: financeService.getTransactions,
  });
}
export function useCreateTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: financeService.createTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: financeKeys.transactions() });
      toast.success("Transaksi berhasil dibuat");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}
3. Pemakaian di Component
tsx
// Di komponen apapun
export function TransactionList() {
  const { data, isLoading, error } = useTransactions();
  const createTransaction = useCreateTransaction();
  if (isLoading) return <Skeleton />;
  if (error) return <ErrorState />;
  return (
    <div>
      {data?.map(t => <TransactionItem key={t.id} {...t} />)}
      <Button onClick={() => createTransaction.mutate(newData)}>
        Tambah Transaksi
      </Button>
    </div>
  );
}
Yang Berubah
File	Aksi
utils/api/axiosInstance.ts
Minor fix: buka comment noRetryRoutes
utils/services/auth-service.ts
Pindah ke src/services/auth-service.ts
src/services/	Folder baru untuk semua service
src/hooks/	Folder baru untuk semua React Query hooks
NOTE

apiService.ts (Get, Post, Put, dll) tidak berubah — tetap sebagai low-level HTTP wrapper. Service layer yang ada (auth-service.ts) hanya dipindah folder saja, logika internalnya tidak berubah kecuali perlu throw error.

Verification Plan
Automated Tests
Tidak ada test file yang sudah ada. Verifikasi dilakukan secara manual.

Manual Verification
Jalankan npm run build — pastikan tidak ada TypeScript error
Jalankan npm run dev dan buka http://localhost:3000/login
Coba login — pastikan token tersimpan di localStorage dan redirect ke /dashboard
Buka DevTools → Network tab — pastikan Authorization header terkirim di setiap request