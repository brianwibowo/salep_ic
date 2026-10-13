# SALEP — Rencana Pengembangan Sales Intelligence Inaproc

Dokumen ini menjadi acuan desain dan implementasi SALEP untuk menangkap peluang IT dari Threads dan ekosistem INAPROC, memelihara histori perubahan tender/kontrak, membantu marketing melakukan validasi, lalu menyajikan prioritas peluang yang relevan untuk sales.

Status: Phase 0 sampai Phase 4 sudah tersedia dalam repository. Migrasi produksi tetap membutuhkan `DATABASE_URL` dan eksekusi Alembic pada deployment.

## 1. Keputusan produk

### 1.1 Definisi sumber

| Track SALEP | Sumber | Makna bisnis | Perlakuan |
|---|---|---|---|
| `social` | Threads | Sinyal kebutuhan atau niat membeli yang muncul di publik | Scrape, normalisasi, klasifikasi, review marketing |
| `sirup` | Si-RUP | Rencana umum pengadaan sebelum proses pemilihan | Sinyal awal, bukan jaminan tender |
| `tender` | SPSE Tender | Pemilihan penyedia yang sedang atau baru berjalan | Prioritas tinggi untuk monitoring tahap dan deadline |
| `non_tender` | SPSE Non Tender | Proses non-tender yang tercatat di SPSE | Tetap masuk pipeline pengadaan |
| `pencatatan_non_tender` | SPSE Pencatatan Non Tender | Pencatatan paket non-SPK/non-tender | Track terpisah karena endpoint dan detailnya berbeda |
| `swakelola` | SPSE Pencatatan Swakelola | Pengadaan/pelaksanaan swakelola yang tercatat | Perlu klasifikasi peluang vendor dengan hati-hati |
| `darurat` | SPSE Pencatatan Pengadaan Darurat | Pengadaan darurat yang tercatat | Ditandai dengan konteks dan risiko berbeda |
| `final` | Derived dari SPSE | Tender atau kontrak yang telah mencapai status akhir | Tidak dibuat sebagai scraper/endpoint fiktif |

Si-RUP adalah sinyal perencanaan. SPSE memuat beberapa jalur proses pengadaan, bukan hanya tender dan negosiasi. `Final` adalah sudut pandang analitik atas status SPSE.

### 1.2 Definisi Final

`Final` mencakup tiga alasan utama:

- `contract_completed`: status kontrak **Selesai**;
- `contract_terminated`: status kontrak **Pemutusan Kontrak**;
- `contract_stopped`: status kontrak **Penghentian Kontrak**.

Status tambahan yang dibutuhkan agar data tidak menyesatkan:

- `tender_completed_no_contract`: tahap tender selesai tetapi kontrak belum terbentuk atau belum tersedia secara publik;
- `unknown_final_reason`: data status tidak cukup untuk menentukan alasan.

Status tender dan status kontrak disimpan sebagai dua field yang berbeda. Satu tender dapat selesai tetapi kontraknya belum selesai. Karena itu dashboard Final tidak boleh menyatukan keduanya dalam satu label.

### 1.3 Cakupan waktu

Default seluruh pencarian INAPROC adalah **dua tahun anggaran terakhir yang dipilih pengguna**. Backend menerima daftar tahun secara eksplisit, misalnya `[2025, 2026]`; jangan menyimpulkan tahun dari `date.today()`.

Konfigurasi awal:

```text
fiscal_years = [tahun_aktif - 1, tahun_aktif]
```

Tahun aktif harus dapat diubah dari UI karena tahun anggaran, tahun kalender, dan default portal tidak selalu sama.

## 2. Link publik yang menjadi sumber resmi

### Si-RUP

- [Si-RUP Cari Paket](https://sirup.inaproc.id/sirup/caripaketctr/index)
- [Si-RUP Rekap](https://sirup.inaproc.id/sirup/home/rekapitulasiindex)
- [Si-RUP Panduan](https://sirup.inaproc.id/sirup/unduhctr/unduh)
- [Si-RUP FAQ](https://sirup.inaproc.id/sirup/faqctr/indexdaftarfaq)
- [Si-RUP Berita](https://sirup.inaproc.id/sirup/beritactr/indexpublic)
- Detail paket penyedia: `https://sirup.inaproc.id/sirup/rup/detailPaketPenyedia2020?idPaket={id_paket}`

Halaman Cari Paket menyediakan filter keyword, K/L/PD, produk dalam negeri, usaha kecil/koperasi, lokasi, jenis pengadaan, metode, pagu, dan bulan pemilihan. Data ditampilkan melalui tabel berpaginasi dan memiliki link detail paket.

### SPSE Nasional

- [SPSE Nasional](https://spse.inaproc.id/nasional/)
- [Tender](https://spse.inaproc.id/nasional/lelang)
- [Non Tender](https://spse.inaproc.id/nasional/nontender)
- [Pencatatan Non Tender](https://spse.inaproc.id/nasional/pencatatan)
- [Pencatatan Swakelola](https://spse.inaproc.id/nasional/swakelola)
- [Pencatatan Pengadaan Darurat](https://spse.inaproc.id/nasional/darurat)
- [Konten Khusus](https://spse.inaproc.id/nasional/publik/special)
- [Daftar Hitam](https://daftar-hitam.inaproc.id/)
- [Data INAPROC](https://data.inaproc.id/)
- [Kontak SPSE](https://spse.inaproc.id/nasional/kontak)
- Detail tender: `https://spse.inaproc.id/nasional/lelang/{kode_tender}/pengumumanlelang`
- Jadwal tender: `https://spse.inaproc.id/nasional/lelang/{kode_tender}/jadwal`

Setiap track SPSE harus memiliki konfigurasi adapter sendiri untuk endpoint tabel, parameter, kolom, dan parser. Jangan mengasumsikan endpoint Tender dapat digunakan untuk semua tab.

Endpoint DataTables publik yang sudah diverifikasi dari konfigurasi halaman saat implementasi:

| Track | Listing | DataTables | Detail |
|---|---|---|---|
| Tender | `/nasional/lelang` | `/nasional/dt/lelang?tahun={tahun}` | `/nasional/lelang/{id}/pengumumanlelang` |
| Non Tender | `/nasional/nontender` | `/nasional/dt/pl?tahun={tahun}` | `/nasional/nontender/{id}/pengumumanpl` |
| Pencatatan Non Tender | `/nasional/pencatatan` | `/nasional/dt/nonspk?tahun={tahun}` | `/nasional/pencatatan/pengumumannonspk?id={id}` |
| Pencatatan Swakelola | `/nasional/swakelola` | `/nasional/dt/swakelola` | `/nasional/swakelola/{id}/pengumuman` |
| Pencatatan Pengadaan Darurat | `/nasional/darurat` | `/nasional/dt/darurat-list` | `/nasional/darurat/pengumumandarurat?id={id}` |

### INAPROC dan tata kelola

- [FAQ Master Satker INAPROC](https://bantuan.inaproc.id/hc/id-id/articles/16763317192591-FAQ-Manajemen-Satuan-Kerja-di-Akun-INAPROC)
- [Perubahan pengelolaan domain SPSE](https://spse.inaproc.id/kapuaskab/publik/detil_special?beritaId=10003969000)

Link privat, login, dashboard internal, dan data yang hanya tersedia setelah autentikasi tidak menjadi target scraper publik.

## 3. Sasaran arsitektur

### 3.1 Prinsip utama

1. **Source of truth adalah database SALEP.** Google Sheets hanya sinkronisasi untuk kebutuhan sales.
2. **Raw data tidak langsung menjadi lead sales.** Semua data melewati normalisasi, deduplikasi, klasifikasi, dan review marketing.
3. **Status adalah histori, bukan hanya nilai terakhir.** Perubahan tahap dan kontrak harus disimpan sebagai event.
4. **Setiap adapter dapat berubah sendiri.** Perubahan markup Si-RUP tidak boleh merusak parser Threads.
5. **Parser harus dapat diaudit.** Setiap record menyimpan URL, waktu pengambilan, metode akses, hash payload, versi parser, dan evidence.
6. **LLM memperkaya data, bukan menjadi sumber fakta.** Fakta angka, status, kode, tanggal, dan instansi harus berasal dari sumber publik.
7. **Retry aman dan idempotent.** Job yang dijalankan ulang tidak boleh membuat peluang duplikat.

### 3.2 Komponen runtime

```text
                 Next.js Frontend
                        │
                   FastAPI API
                        │
        ┌───────────────┴────────────────┐
        │                                │
   Query/analytics API              Job API
        │                                │
   PostgreSQL + read model      Worker + scheduler
        │                                │
        └───────────────┬────────────────┘
                        │
      ┌─────────────────┼─────────────────┐
      │                 │                 │
  Threads/Apify      Si-RUP          SPSE tracks
      │                 │                 │
      └─────────────────┴─────────────────┘
                        │
               Raw snapshot storage
                        │
                 LLM enrichment
```

### 3.3 Struktur backend yang dituju

```text
backend/app/
├── api/
│   └── routes/
│       ├── opportunities.py
│       ├── inaproc.py
│       ├── analytics.py
│       └── jobs.py
├── domain/
│   ├── opportunities/
│   ├── procurement/
│   ├── classification/
│   └── contacts/
├── sources/
│   ├── base.py
│   ├── threads/
│   └── inaproc/
│       ├── sirup.py
│       ├── spse_tender.py
│       ├── spse_non_tender.py
│       ├── spse_swakelola.py
│       └── spse_darurat.py
├── ingestion/
│   ├── fetcher.py
│   ├── browser_fetcher.py
│   ├── retry.py
│   └── snapshots.py
├── services/
│   ├── normalization.py
│   ├── deduplication.py
│   ├── opportunity_service.py
│   ├── analytics_service.py
│   └── sync_service.py
├── workers/
│   ├── scheduler.py
│   └── tasks.py
└── db/
    ├── models.py
    ├── repositories.py
    └── migrations/
```

## 4. Model data kanonik

### 4.1 `source_documents`

Menyimpan dokumen mentah dan hasil pengambilan.

```text
id
source                  threads | sirup | spse
action                  listing | detail | schedule | profile
source_url
external_id
fetched_at
http_status
access_mode             http | browser | apify
payload_uri             object storage atau local fixture
payload_hash
parser_version
run_id
```

Payload mentah tidak perlu disimpan di setiap row lead. Simpan sekali sebagai snapshot, lalu hubungkan melalui `payload_uri` dan `payload_hash`.

### 4.2 `procurement_packages`

```text
id
source                  sirup | spse
track                   sirup | tender | non_tender | swakelola | darurat
external_id
rup_id
kode_tender
package_name
description
organization
satker
location
procurement_type
procurement_method
fiscal_year
budget_amount
hps_amount
contract_type
local_content_flag
small_business_flag
source_url
first_seen_at
last_seen_at
current_stage_code
current_stage_label
current_contract_status
raw_snapshot_id
```

### 4.3 `procurement_events`

```text
id
package_id
event_type              stage_changed | contract_status_changed | winner_changed | schedule_changed
event_code
old_value
new_value
event_at
observed_at
source_snapshot_id
```

### 4.4 `opportunities`

`opportunities` adalah read model untuk marketing dan sales, bukan salinan mentah.

```text
id
source_document_id
package_id atau social_post_id
opportunity_type        social_need | planned_procurement | active_tender | final_market
service_category        managed_service | cloud | server | network | security | software | other
is_it_relevant
relevance_score
managed_service_fit
commercial_signal
confidence
marketing_status        pending | valid | invalid
sales_status
review_reason
evidence_json
last_classified_at
classifier_version
```

### 4.5 Kontak publik dan KYC

Kontak hanya diambil jika tersedia secara publik dan relevan dengan paket, misalnya nama instansi, satker, role, atau kontak resmi yang tercantum pada halaman sumber.

Jangan membuat klaim identitas, hubungan pribadi, atau data sensitif berdasarkan inferensi. Simpan `contact_source_url`, `contact_role`, dan `contact_confidence`. KYC harus menjadi proses terpisah dengan kebijakan akses, audit, dan dasar penggunaan yang jelas.

## 5. Strategi scraper

### 5.1 Si-RUP

Strategi:

1. Gunakan filter keyword dan tahun anggaran.
2. Tambahkan filter jenis pengadaan, metode, lokasi, dan pagu bila dibutuhkan.
3. Ambil row listing dan `idPaket`.
4. Ambil detail hanya untuk paket yang cocok dengan taxonomy IT.
5. Simpan snapshot dan hash.
6. Jalankan sinkronisasi harian serta manual refresh.

Jangan mengambil jutaan row tanpa filter. Dataset besar harus ditangani dengan query terarah, pagination, dan checkpoint.

### 5.2 SPSE

Implementasikan lima adapter track:

```text
SpseTenderAdapter
SpseNonTenderAdapter
SpsePencatatanAdapter
SpseSwakelolaAdapter
SpseDaruratAdapter
```

Masing-masing adapter harus menangani:

- tahun anggaran;
- kategori pengadaan;
- instansi;
- pemenang berkontrak;
- status kontrak;
- jenis kontrak;
- keyword lokal;
- pagination;
- link tahap/jadwal;
- detail paket.

Listing adalah tahap pertama. Detail dan jadwal diambil berdasarkan prioritas:

```text
active deadline dekat > status berubah > paket baru > paket historis
```

Karena deep-link dapat ditolak, fetcher harus:

1. membuka halaman listing terlebih dahulu;
2. mempertahankan cookie/session;
3. mengambil detail melalui HTTP bila berhasil;
4. fallback ke browser Playwright/Camoufox bila halaman membutuhkan JavaScript;
5. mencatat `access_mode` dan alasan fallback.

### 5.3 Final

Final tidak melakukan scrape kedua. Query Final membaca data `procurement_packages` dan event kontrak:

```sql
WHERE fiscal_year IN (:years)
  AND (
    current_contract_status IN ('Selesai', 'Pemutusan Kontrak', 'Penghentian Kontrak')
    OR current_stage_code = 'tender_completed'
  )
```

Semua status harus dinormalisasi ke enum internal. Label asli portal tetap disimpan untuk evidence.

### 5.4 Threads

Pipeline Threads dibuat dua tahap:

1. **Retrieval presisi**
   - query terbatas dan terukur melalui Apify;
   - sort recent;
   - validasi tanggal dan URL;
   - canonical post ID;
   - buang caption kosong, duplikat, dan hasil yang tidak memiliki konteks keyword.
2. **Qualification**
   - intent mencari vendor;
   - kebutuhan IT;
   - spam/advertising likelihood;
   - kebutuhan managed service;
   - confidence dan evidence.

Jangan memperluas keyword secara agresif setiap siklus. Simpan query, actor run ID, jumlah item, dan biaya/kuota untuk mengukur precision dan penggunaan Apify.

## 6. Browser dan anti-block layer

Camoufox dapat dipakai sebagai browser fallback karena kompatibel dengan Playwright dan memiliki fingerprint layer, tetapi tidak boleh dianggap sebagai jaminan lolos semua proteksi. [Camoufox](https://camoufox.com/) [Usage](https://camoufox.com/python/usage/)

Komponen `BrowserFetcher` harus memiliki:

- browser context persisten per host;
- timeout dan cancellation;
- rate limiter per host;
- jitter yang wajar;
- cookie reuse;
- circuit breaker;
- exponential backoff;
- screenshot/HTML fixture saat parser gagal;
- deteksi halaman access denied;
- observability untuk HTTP 403, 429, 5xx, dan perubahan DOM.

Urutan pemilihan metode:

```text
official/public JSON or DataTables
  → HTTP session with token/cookie
  → normal Playwright browser
  → Camoufox browser fallback
  → mark unavailable and retry later
```

Jangan menjadikan CAPTCHA solving, login bypass, atau fingerprint rotation sebagai mekanisme bisnis inti. Untuk data publik, frekuensi kecil, cache, dan query terarah lebih baik daripada scraping agresif.

## 7. LLM dan classification pipeline

### 7.1 Tugas deterministik

Gunakan kode biasa untuk:

- parsing angka dan tanggal;
- normalisasi mata uang;
- normalisasi status tender/kontrak;
- canonical URL;
- deduplication;
- validasi schema;
- perhitungan freshness;
- filter fiscal year;
- penentuan Final.

### 7.2 Tugas LLM

Gunakan LLM untuk:

- memetakan judul/deskripsi ke kategori layanan;
- mengidentifikasi sinyal managed service;
- merangkum pain point;
- mengklasifikasikan intent Threads;
- memberi label spam/irrelevant/uncertain;
- menghasilkan evidence dari teks yang benar-benar tersedia.

LLM tidak boleh:

- mengubah angka pagu/HPS;
- menciptakan nama kontak;
- menyatakan bahwa organisasi pasti membeli layanan;
- menghapus raw record;
- menandai lead valid tanpa review marketing.

Hasil LLM disimpan dengan `model`, `prompt_version`, `input_hash`, `confidence`, dan `evidence`. Cache berdasarkan hash agar record yang sama tidak dianalisis berulang kali.

### 7.3 Skor peluang managed service

Skor tidak boleh hanya berasal dari LLM. Gunakan komponen deterministik:

```text
managed_service_fit =
  30% service/category match
+ 20% explicit recurring-operation signal
+ 15% infrastructure/availability signal
+ 15% budget and package scale
+ 10% organization/repeatability signal
+ 10% freshness and data confidence
```

Bobot harus dapat dikalibrasi dari hasil review marketing dan outcome sales. Simpan breakdown agar sales dapat memahami alasan skor.

## 8. Backend API

Endpoint baru yang disarankan:

```text
GET  /api/v1/inaproc/config
POST /api/v1/inaproc/sirup/search
POST /api/v1/inaproc/spse/search
GET  /api/v1/inaproc/packages/{id}
GET  /api/v1/inaproc/packages/{id}/timeline
GET  /api/v1/final
GET  /api/v1/final/summary
GET  /api/v1/final/filters
POST /api/v1/jobs/inaproc/run
GET  /api/v1/jobs/{run_id}
```

Parameter pencarian:

```text
sources
tracks
fiscal_years
keywords
organizations
locations
procurement_methods
contract_statuses
stage_codes
min_budget
max_budget
page
limit
sort
```

`POST /api/v1/spse/search` lama dipertahankan sementara untuk backward compatibility, lalu diarahkan ke service baru.

Semua response menggunakan envelope yang sama dan mengembalikan `data_freshness`, `source_urls`, serta `pagination`.

### 8.1 Final summary

Response chart minimal:

```json
{
  "period": {"fiscal_years": [2025, 2026]},
  "total_packages": 120,
  "total_budget": 93400000000,
  "by_final_reason": [
    {"key": "contract_completed", "label": "Kontrak selesai", "count": 65, "budget": 48000000000},
    {"key": "contract_terminated", "label": "Pemutusan kontrak", "count": 12, "budget": 9000000000},
    {"key": "contract_stopped", "label": "Penghentian kontrak", "count": 8, "budget": 4000000000},
    {"key": "tender_completed_no_contract", "label": "Tender selesai", "count": 35, "budget": 33000000000}
  ],
  "by_service_category": [],
  "managed_service_opportunities": [],
  "data_quality": {"unknown_reason": 3, "last_synced_at": "..."}
}
```

## 9. Frontend dan chart Final

Sidebar yang dituju:

```text
Leads
├── Sosial Media
└── INAPROC
    ├── Si-RUP
    ├── SPSE
    └── Final
```

Halaman Final memiliki:

1. filter tahun anggaran, alasan Final, track SPSE, instansi, lokasi, kategori IT, rentang pagu, dan freshness;
2. kartu metrik total paket, total pagu, paket IT, dan peluang managed service;
3. donut chart **alasan Final** dengan legend dan jumlah/pagu;
4. donut chart **kategori layanan** dengan kategori `managed_service`, `cloud`, `server`, `network`, `security`, `software`, `other`;
5. chart bar untuk instansi atau satker dengan paket IT terbanyak;
6. tabel detail sebagai drill-down setelah chart diklik;
7. timeline status paket;
8. source link dan timestamp pengambilan.

Aturan visualisasi:

- jangan memakai 3D pie chart;
- maksimal 6–7 slice sebelum kategori lain digabung;
- tampilkan count dan nilai pagu secara terpisah;
- selalu tampilkan legend dan total denominator;
- sediakan tabel aksesibel sebagai fallback chart;
- klik legend/slice harus menerapkan filter ke tabel;
- tampilkan `unknown` secara eksplisit agar chart tidak terlihat lebih presisi daripada datanya.

Service, hook, dan komponen mengikuti pola repository yang sudah ada: service API → React Query hook → UI component. Tidak ada fetch langsung di komponen.

## 10. Migrasi source of truth ke PostgreSQL

Rekomendasi: **migrasikan source of truth ke PostgreSQL sekarang**, tetapi secara bertahap melalui repository abstraction. Jangan melakukan big-bang rewrite.

### Tahap migrasi

1. Tambahkan SQLAlchemy/SQLModel models dan Alembic.
2. Buat interface repository untuk `packages`, `events`, `opportunities`, `snapshots`, dan `scrape_runs`.
3. Pertahankan SQLite adapter untuk unit test dan local fixture.
4. Export data SQLite lama ke format staging.
5. Backfill ke PostgreSQL dengan deterministic IDs.
6. Jalankan dual-read sementara untuk membandingkan jumlah dan sample record.
7. Aktifkan PostgreSQL sebagai production source of truth melalui environment flag.
8. Jadikan Google Sheets sinkronisasi asynchronous.
9. Setelah stabil, hapus ketergantungan business logic langsung pada SQLite.

### Alasan

PostgreSQL dibutuhkan untuk:

- histori status dan event;
- query filter lintas dua tahun;
- agregasi chart;
- job lock dan idempotency;
- concurrent worker;
- audit review marketing;
- indeks `external_id`, `fiscal_year`, `stage_code`, `contract_status`, dan `source`.

Redis belum wajib pada tahap awal. Tambahkan Redis/queue hanya ketika volume job atau concurrency sudah membutuhkannya. Worker terpisah dan tabel `scrape_runs` sudah cukup untuk fase pertama.

## 11. Scheduler dan job design

Setiap job memiliki:

```text
run_id
source
track
requested_at
started_at
finished_at
status
parameters_json
records_seen
records_inserted
records_updated
records_rejected
error_code
error_message
```

Job scheduler:

| Job | Default |
|---|---:|
| Threads retrieval | setiap 30 menit |
| SPSE active tracks | setiap 30–60 menit |
| Si-RUP two-year sync | harian |
| Final status refresh | setiap 6–12 jam |
| Detail enrichment | queue berdasarkan prioritas |
| Analytics materialization | setelah ingestion selesai |

Gunakan database lock atau scheduler terpusat agar dua instance tidak menjalankan job yang sama. Semua job harus dapat dijalankan manual dengan parameter yang sama dengan cron.

## 12. Observability dan kualitas data

Metrics minimum:

- scrape success rate per source/track;
- HTTP 403/429/5xx;
- parser error rate;
- rows fetched dan rows accepted;
- duplicate rate;
- snapshot freshness;
- status transition count;
- LLM cost dan cache hit rate;
- Threads precision berdasarkan sample review;
- marketing valid rate;
- sales conversion per source/track;
- managed service opportunity rate.

Alert ketika:

- tidak ada row baru dalam beberapa siklus padahal source biasanya aktif;
- struktur kolom berubah;
- response kosong mendadak;
- access denied meningkat;
- parser menerima data tetapi semua field penting kosong;
- freshness melewati SLA.

## 13. Pengujian

### Unit test

- parser fixture Si-RUP listing/detail;
- parser fixture untuk kelima tab SPSE;
- normalisasi status kontrak;
- penentuan Final;
- dua tahun anggaran;
- deduplication berdasarkan source + external ID;
- idempotent re-run;
- skor managed service;
- response chart dengan kategori unknown.

### Contract test

Simpan HTML/JSON fixture dari portal yang sudah disanitasi. Test memastikan perubahan kecil pada markup menghasilkan error yang jelas, bukan data kosong yang terlihat valid.

### Golden set Threads

Buat set berlabel manusia, minimal:

- 100 post relevan;
- 100 post tidak relevan/spam/promosi;
- 50 post ambigu;
- beberapa bahasa dan variasi slang.

Target awal:

```text
Threads precision relevan: >= 85%
Duplicate rate: <= 3%
SPSE/Si-RUP parser acceptance: >= 98% pada fixture
Idempotent re-run duplicate: 0
```

Angka tersebut menjadi target evaluasi, bukan klaim hasil sebelum pengukuran.

## 14. Keamanan, privasi, dan tata kelola

- hanya ambil data publik yang diperlukan untuk tujuan sales intelligence;
- simpan URL sumber dan waktu pengambilan;
- minimalkan penyimpanan kontak personal;
- pisahkan data publik paket dari data contact intelligence;
- batasi akses contact/KYC berdasarkan role;
- audit perubahan marketing status dan sales status;
- enkripsi credential Apify, LLM, database, dan object storage;
- jangan scrape area login atau bypass kontrol akses;
- hormati terms, rate limit, dan kebijakan portal;
- sediakan mekanisme penghapusan/retensi raw snapshot.

## 15. Tahapan implementasi

### Phase 0 — Contract dan fixtures

- setujui enum track/status Final;
- buat canonical schema;
- simpan fixture Si-RUP dan seluruh tab SPSE;
- tulis contract test;
- buat taxonomy layanan IT dan managed service.

**Output:** schema, fixture, parser contract, migration design.

### Phase 1 — PostgreSQL foundation

- models dan Alembic;
- repository abstraction;
- `scrape_runs`, snapshots, packages, events, opportunities;
- backfill SQLite;
- read/write verification.

**Output:** database production-ready dan repository tidak bergantung langsung pada SQLite.

### Phase 2 — Si-RUP adapter

- filter dua tahun;
- pagination/checkpoint;
- detail package;
- idempotent upsert;
- daily schedule dan manual run.

**Output:** peluang perencanaan yang dapat dicari dan diaudit.

### Phase 2b — SPSE adapters

- lima track;
- listing dan detail;
- schedule timeline;
- status transition;
- browser fallback;
- active monitoring.

**Output:** satu model paket lintas semua jalur SPSE.

### Phase 4 — Final analytics

- derived Final query;
- reason normalization;
- summary API;
- donut/bar chart;
- drill-down dan timeline.

**Output:** market intelligence Final sesuai tujuan bisnis.

### Phase 5 — Threads precision

- retrieval instrumentation;
- canonical post ID;
- deterministic relevance gate;
- LLM classification/cache;
- golden-set evaluation.

**Output:** Threads menghasilkan lebih sedikit noise dengan precision terukur.

Implementasi Phase 5 menambahkan canonical ID yang tahan variasi URL/provider,
gate relevansi deterministik sebelum LLM, klasifikasi `genuine`,
`suspected_spam`, dan `suspected_fake`, serta metadata quality yang ikut
tersimpan pada LeadRecord dan PostgreSQL. Cache LLM memakai hash konten + model
 + versi prompt agar replay tidak mengulang biaya provider. Golden set awal
berisi 10 contoh dan dievaluasi melalui `backend/scripts/evaluate_threads_golden.py`;
precision dan recall relevansi maupun spam dicetak sebagai JSON.

### Phase 6 — Operational hardening

- separate worker;
- scheduler lock;
- retries/circuit breaker;
- metrics/logging/alerts;
- backup dan retention;
- runbook incident.

**Output:** sistem dapat dipelihara dan dipulihkan tanpa intervensi manual setiap hari.

Implementasi Phase 6 menambahkan worker terpisah (`app.worker`), process role
API/worker pada deployment, PostgreSQL advisory lock dengan file fallback,
retry exponential backoff, circuit breaker, metrics `/metrics`, readiness
`/ready`, alert webhook cooldown, backup checksum + retention, retention SQL
untuk snapshot/cache, serta runbook incident di `OPERATIONS_RUNBOOK.md`.

## 16. Definition of Done

Fitur dianggap siap ketika:

- dua tahun anggaran dapat dipilih dan diproses konsisten;
- lima track SPSE dan Si-RUP memiliki adapter terpisah;
- Final menampilkan selesai, putus, dan henti dengan alasan yang benar;
- setiap record dapat ditelusuri ke URL dan snapshot sumber;
- re-run job tidak membuat duplikat;
- chart memiliki legend, denominator, unknown, dan drill-down;
- raw data tidak langsung tampil sebagai lead sales;
- marketing tetap menjadi gate validasi;
- LLM output memiliki confidence dan evidence;
- PostgreSQL menjadi source of truth;
- Google Sheets tetap tersedia sebagai sinkronisasi sales;
- scheduler dapat dijalankan manual maupun otomatis;
- parser, migration, API, dan chart memiliki test yang relevan;
- access denied atau perubahan markup menghasilkan alert, bukan data palsu.

## 17. Keputusan lanjutan yang perlu dikunci

1. Default dua tahun: gunakan `[tahun aktif - 1, tahun aktif]` atau tetapkan eksplisit `2025` dan `2026` untuk deployment pertama.
2. Apakah `tender_completed_no_contract` ditampilkan di halaman Final utama atau hanya filter tambahan.
3. Apakah contact intelligence publik langsung masuk Phase 4, atau setelah pipeline paket dan histori stabil.
4. Nama produk managed service dan taxonomy layanan yang akan dipakai untuk scoring.

Rekomendasi awal saya: gunakan dua tahun dinamis, tampilkan tender selesai tanpa kontrak sebagai kategori terpisah, tunda enrichment kontak sampai data paket stabil, dan gunakan PostgreSQL sebagai source of truth sejak Phase 1.
