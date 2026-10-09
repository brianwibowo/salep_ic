# SALEP Frontend

Frontend SALEP menggunakan Next.js dan terhubung ke FastAPI di folder `../backend`.

## Menjalankan secara lokal

1. Siapkan backend di `../backend`. Saat dijalankan dari folder itu, backend membaca konfigurasi dari `backend/.env`; isi API key yang diperlukan dan gunakan `APP_ENV=development` untuk sesi cookie lokal lewat HTTP.
2. Buat `.env.local` di folder ini berdasarkan `env.example`. Nilai default mengarah ke `http://localhost:8000`.
3. Jalankan backend pada port 8000, lalu dari root `salep_ic` buka terminal kedua:

```powershell
cd frontend
Copy-Item env.example .env.local
npm install
npm run dev
```

Buka `http://localhost:3000`. Login demo memilih role Marketing atau Sales; backend membuat sesi cookie HttpOnly. Login ini belum memakai akun/password.

## Integrasi API

Client SALEP ada di `src/services/salep-api.ts` dan menggunakan `credentials: include` untuk sesi cookie. API berjalan pada `/api/v1` di backend. Halaman ringkasan dan leads membaca data SQLite backend; Marketing juga dapat mengatur serta menjalankan discovery.

`NEXT_PUBLIC_API_URL` harus berisi root URL backend, tanpa akhiran `/api/v1`. Untuk host yang berbeda, backend perlu mengizinkan origin frontend di konfigurasi CORS.
