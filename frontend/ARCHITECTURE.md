# SALEP Frontend Architecture & Boilerplate Guide

Dokumen ini ditujukan bagi tim developer untuk memahami standar arsitektur, struktur folder, dan *boilerplate* yang digunakan pada aplikasi Frontend SALEP.

## 🚀 Tech Stack Utama

- **Framework:** [Next.js](https://nextjs.org/) (App Router)
- **Bahasa:** [TypeScript](https://www.typescriptlang.org/)
- **Styling:** [Tailwind CSS](https://tailwindcss.com/)
- **UI Components:** [shadcn/ui](https://ui.shadcn.com/)
- **Data Fetching & State:** [TanStack React Query](https://tanstack.com/query/latest) + Axios
- **Form & Validation:** [React Hook Form](https://react-hook-form.com/) + [Zod](https://zod.dev/)
- **Notifications:** [Sonner](https://sonner.emilkowal.ski/)

---

## 📂 Struktur Folder (`src/`)

Arsitektur kita memisahkan secara tegas antara UI (Components/Pages), State/Caching (Hooks), dan Network (Services).

```text
frontend/src/
├── app/                  # Routing Next.js (App Router)
│   ├── (auth)/           # Route group untuk halaman publik (Login, Register)
│   └── (protected)/      # Route group untuk halaman yang butuh autentikasi (Dashboard, dll)
├── components/           # UI Components
│   ├── common/           # Reusable components spesifik aplikasi kita
│   ├── layout/           # Komponen layout (Sidebar, Header, dll)
│   └── ui/               # Base components dari shadcn/ui (Button, Input, dll)
├── configs/              # Konfigurasi aplikasi (Environment variables, API URLs)
├── hooks/                # Custom React Hooks (Terutama untuk React Query)
│   ├── auth/             # Hooks terkait autentikasi
│   └── [domain]/         # Hooks per domain bisnis (misal: leads, discovery)
├── lib/                  # Utility library (misal: utils.ts untuk tailwind-merge)
├── providers/            # React Context Providers (QueryClientProvider, ThemeProvider)
├── services/             # Layer API Call (Axios requests murni)
│   ├── auth-service.ts
│   └── [domain]-service.ts
├── types/                # TypeScript Interfaces & Types global
├── utils/                # Helper functions murni
│   └── api/              # Setup Axios instance & interceptors
└── validations/          # Skema validasi menggunakan Zod
```

---

## 🏗️ Pola Arsitektur (The Flow)

Untuk menjaga *clean code* dan memudahkan *debugging*, kita memisahkan proses data fetching menjadi 3 layer. **DILARANG** melakukan `fetch` atau `axios.get` langsung di dalam UI Component.

### Alur Kerja (The 3-Layer Flow):
1. **Service Layer (`src/services`)**: Murni melakukan HTTP Request via Axios. Mengembalikan data (berupa Promise) atau melempar Error.
2. **Hook Layer (`src/hooks`)**: Menggunakan TanStack React Query (`useQuery` / `useMutation`) untuk memanggil Service Layer. Bertugas menangani *caching*, *loading state*, *error handling* global, dan *invalidation*.
3. **UI Component (`src/app` atau `src/components`)**: Hanya memanggil Custom Hook dan me-render UI berdasarkan state (`isLoading`, `data`, `error`).

---

## 💻 Contoh Implementasi Boilerplate

Berikut adalah contoh bagaimana membuat fitur baru dengan arsitektur ini (misal: Fitur Leads).

### 1. Buat Service Layer (`src/services/leads-service.ts`)
Fokus pada endpoint API, payload, dan response.
```typescript
import { Get, Post } from "@/utils/api/apiService";
import { apiConfig } from "@/configs/api-config";
import { Lead } from "@/types/lead";

const BASE = apiConfig.service_user; // Sesuaikan base URL

export const leadsService = {
  getLeads: async (): Promise<Lead[]> => {
    // Fungsi Get, Post dll sudah dibungkus dengan standard response
    const res = await Get<Lead[]>(`${BASE}/leads`);
    if (!res.status) throw new Error(res.message);
    return res.data;
  },
  
  createLead: async (data: Partial<Lead>): Promise<Lead> => {
    const res = await Post<Lead>(`${BASE}/leads`, data);
    if (!res.status) throw new Error(res.message);
    return res.data;
  }
};
```

### 2. Buat Custom Hook (`src/hooks/leads/use-leads.ts`)
Fokus pada React Query, Caching, dan Notification (Toast).
```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { leadsService } from "@/services/leads-service";
import { toast } from "sonner";

// 1. Definisikan Query Keys untuk kemudahan invalidasi
export const leadsKeys = {
  all: ["leads"] as const,
  lists: () => [...leadsKeys.all, "list"] as const,
};

// 2. Hook untuk GET Data (useQuery)
export function useGetLeads() {
  return useQuery({
    queryKey: leadsKeys.lists(),
    queryFn: leadsService.getLeads,
  });
}

// 3. Hook untuk POST/PUT/DELETE (useMutation)
export function useCreateLead() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: leadsService.createLead,
    onSuccess: () => {
      // Refresh list leads setelah berhasil membuat baru
      queryClient.invalidateQueries({ queryKey: leadsKeys.lists() });
      toast.success("Lead berhasil ditambahkan!");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Gagal menambahkan lead.");
    },
  });
}
```

### 3. Gunakan di UI Component (`src/app/(protected)/leads/page.tsx`)
UI Component menjadi sangat bersih karena tidak ada logika fetching data.
```tsx
"use client";

import { useGetLeads, useCreateLead } from "@/hooks/leads/use-leads";
import { Button } from "@/components/ui/button";

export default function LeadsPage() {
  const { data: leads, isLoading, isError, error } = useGetLeads();
  const createMutation = useCreateLead();

  if (isLoading) return <div>Loading leads...</div>;
  if (isError) return <div>Error: {error?.message}</div>;

  const handleCreate = () => {
    createMutation.mutate({ name: "New Lead", score: 85 });
  };

  return (
    <div>
      <h1>Daftar Leads</h1>
      <Button 
        onClick={handleCreate} 
        disabled={createMutation.isPending}
      >
        {createMutation.isPending ? "Menyimpan..." : "Tambah Lead"}
      </Button>

      <ul>
        {leads?.map((lead) => (
          <li key={lead.id}>{lead.name} - Score: {lead.score}</li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 📝 Aturan Main Tambahan (Guidelines)

1. **Routing (`app/`)**
   - Gunakan `(auth)` untuk route yang **tidak butuh** login (Login, Register).
   - Gunakan `(protected)` untuk route yang **butuh** login (Dashboard, Leads).
   - Penempatan file di Next.js App Router: `page.tsx` (untuk view utama), `layout.tsx` (untuk wrapper UI/Sidebar). Letakkan komponen pendukung spesifik page di dalam folder `_components/` (misal: `app/(auth)/login/_components/login.tsx`).

2. **Validasi (Zod + React Hook Form)**
   - Semua form HARUS menggunakan `react-hook-form` yang divalidasi menggunakan skema `Zod`.
   - Simpan skema di dalam folder `src/validations/`.

3. **Styling (Tailwind + shadcn)**
   - Sebisa mungkin gunakan komponen dari `src/components/ui` (shadcn) yang sudah disediakan.
   - Jangan menulis *inline styles* (`style={{...}}`). Selalu gunakan Tailwind classes (`className="..."`).
   - Gunakan fungsi `cn()` dari `src/lib/utils.ts` jika perlu menggabungkan Tailwind classes secara dinamis.

4. **Koneksi API SALEP (Session Cookie)**
   - API SALEP memakai sesi cookie `HttpOnly` yang dibuat backend saat login sebagai Marketing atau Sales. Gunakan helper `src/utils/api/apiService.ts`; Axios mengirim request dengan `withCredentials: true`. Jangan menyimpan token sesi di `localStorage`.
   - URL backend berasal dari `NEXT_PUBLIC_API_URL` dan tidak memuat `/api/v1`. Endpoint SALEP diawali `/api/v1`.
   - `src/utils/api/axiosInstance.ts` adalah shared client untuk seluruh service. Response envelope standar dan response raw FastAPI diproses oleh `apiService.ts`.

---
*Dokumentasi ini dibuat agar kita memiliki pemahaman dan standar koding yang sama. Happy Coding! 🚀*
