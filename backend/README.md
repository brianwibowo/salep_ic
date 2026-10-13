# SALEP — AI Sales Intelligence Platform

> Real-time keyword search → raw leads → AI analysis → product/service matching → lead scoring → Google Sheets.

## Quick Start

### 1. Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# Test dependencies (includes SQLAlchemy/Alembic/psycopg and pytest)
pip install -r requirements-dev.txt

# Copy environment config
cp .env.example .env
# Edit .env with your API keys
```

### 2. Configure `.env`

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Optional: Google Sheets
GOOGLE_SHEETS_ID=your-spreadsheet-id
GOOGLE_SERVICE_ACCOUNT_JSON=service-account.json
```

### 3. Run

```bash
uvicorn app.main:app --reload
```

API available at: `http://localhost:8000`
Docs at: `http://localhost:8000/docs`

API responses use a consistent envelope:

```json
{
  "status": true,
  "message": "Request berhasil",
  "data": {}
}
```

### 4. Docker

```bash
docker compose up --build
```

## API Endpoints

### Health Check
```
GET /health
```

### Search Leads (Full Pipeline)
```
POST /api/v1/search
```
```json
{
  "keywords": ["butuh aplikasi inventory"],
  "start_date": "2026-10-05",
  "end_date": "2026-10-05",
  "sources": ["mock"],
  "limit": 20
}
```

The leads list supports filtering and pagination:

```
GET /api/v1/leads?page=1&limit=50&status=pending&source=threads&search=hosting
```

Paginated responses return `data.items` and `data.pagination` with `page`, `limit`, and `total`.

### Analyze Single Lead (Dev/Testing)
```
POST /api/v1/leads/analyze
```
```json
{
  "content": "Kami sedang mencari vendor ERP untuk perusahaan distribusi."
}
```

## Architecture

```
Keyword → Source Search → Raw Leads → SALEP AI Agent → Structured JSON → Google Sheets
```

## Testing

```bash
# Deterministic full suite; provider tests are skipped by default
PYTHONPATH=. pytest -q tests

# Opt in to live LLM/SPSE tests only in a controlled environment
PYTHONPATH=. pytest --run-external -q tests/test_agent.py tests/test_spse_source.py
```

## Project Structure

```
salep/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── api/routes/           # API endpoints
│   ├── agent/                # SALEP AI Agent
│   │   ├── salep_agent.py    # Agent + Runner
│   │   ├── instructions.py   # System prompt
│   │   ├── schemas.py        # Pydantic models
│   │   └── tools.py          # Agent tools
│   ├── sources/              # Source adapters
│   │   ├── base.py           # Protocol
│   │   └── mock_source.py    # Mock adapter
│   ├── services/             # Business logic
│   │   ├── search_service.py # Search + dedup
│   │   ├── lead_service.py   # Pipeline orchestrator
│   │   ├── scoring_service.py # Deterministic scoring
│   │   └── google_sheets.py  # Sheets storage
│   └── core/                 # Config + logging
├── data/products.json        # Product catalog
├── tests/                    # Test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Workspace & discovery

- Login demo memilih Marketing atau Sales. Cookie HttpOnly menyimpan token sesi opaque; role diverifikasi server, bukan parameter `role` atau localStorage. Sesi berlaku 24 jam. Logout wajib sebelum berganti role. Ini belum autentikasi akun/password untuk produksi.
- Marketing mengatur discovery dan validasi. Sales hanya membaca lead `valid` dan memperbarui tindak lanjutnya. Prospek baru menunggu review marketing; lead lama mempertahankan statusnya.
- Dashboard memakai pagination database (10/25/50 baris), pencarian, filter status, dan detail skor.
- Default discovery: Threads, setiap 30 menit, dua keyword bergiliran. Keyword mencakup software, hosting/VPS, cloud, managed service, jaringan, keamanan, backup, ERP, CRM, dan otomasi. Pengaturan UI tersimpan di `data/discovery.json` dan mengungguli environment untuk keyword/sumber/batas hasil.
- Jalankan **satu worker** untuk scheduler internal. Siklus pertama berjalan setelah interval awal. Tombol “Jalankan sekali” tidak menunggu jadwal. Mulai/berhenti berlaku selama proses server hidup; `AUTO_SEARCH_ENABLED` menentukan startup berikutnya.
- Jika `DATABASE_URL` dan `INAPROC_AUTO_SYNC_ENABLED=true` tersedia, heartbeat yang sama juga menyinkronkan Si-RUP serta lima track SPSE untuk tahun anggaran aktif dan satu tahun sebelumnya. Kegagalan portal dicatat sebagai warning dan tidak membatalkan discovery sosial.
- Pencarian manual memakai 1–10 keyword eksplisit, tanpa ekspansi sinonim otomatis yang menambah pemakaian Apify. Actor Threads tetap sama. Filter tanggal dilakukan pada hasil bertanggal; posting tanpa tanggal tetap disertakan. Batas hasil tidak sama dengan jumlah posting yang ditagihkan actor.
- Alternatif cron eksternal: set `AUTO_SEARCH_ENABLED=false` untuk menghindari dua scheduler, lalu gunakan `*/30 * * * * cd /path/to/salep && SALEP_API_URL=http://127.0.0.1:8000 bash scripts/run_search.sh`. Script memakai pool konfigurasi yang sama dan sesi marketing sementara. API lain juga memerlukan login `/api/v1/auth/login` dan cookie responsnya.

Tes lokal tanpa panggilan provider:

```bash
pytest tests/test_api_endpoints.py tests/test_discovery.py tests/test_scoring.py tests/test_deduplication.py tests/test_leads_rbac.py -q
```

## PostgreSQL migration

The production source of truth can be enabled incrementally with
`DATABASE_URL`. When the variable is empty, the existing SQLite repository is
kept for local development and tests. PostgreSQL should be prepared through
the checked-in Alembic migration before switching the application backend:

```bash
cd backend
export DATABASE_URL='postgresql+psycopg://salep:password@localhost:5432/salep'
alembic upgrade head
```

Then restart the API with the same `DATABASE_URL`. `DATABASE_AUTO_CREATE` is
available for disposable local databases, but should remain `false` in
production so schema changes are always reviewed and applied by migration.

### Inaproc Phase 2

`POST /api/v1/inaproc/sync` ingests the requested fiscal years into the
PostgreSQL source of truth. With no `tracks` filter it visits Si-RUP and all
five SPSE public tracks sequentially: Tender, Non Tender, Pencatatan Non
Tender, Pencatatan Swakelola, and Pencatatan Pengadaan Darurat. Each track uses
its own DataTables endpoint, tokenized session, pagination cursor, and detail
URL. `fetch_details=true` enriches the listing record when the detail page is
available; a temporary detail failure does not discard a valid listing row.

The exact public routes are exposed by `GET /api/v1/inaproc/tracks`. Every
upsert records a normalized source snapshot and emits `stage_changed` or
`contract_status_changed` events when a package moves through its lifecycle.
Final analytics can therefore distinguish completed, terminated, stopped, and
tender-completed-without-contract packages without an LLM.

### Final analytics

Final is a deterministic projection of SPSE packages in PostgreSQL. It is not
a sixth scraper. The API defaults to the active and previous fiscal year:

```text
GET /api/v1/inaproc/final/summary?fiscal_years=2025&fiscal_years=2026
GET /api/v1/inaproc/final?fiscal_years=2025&fiscal_years=2026&page=1&limit=25
```

Reason normalization prioritizes explicit contract status, then completed
tender stage, and keeps an unknown final reason visible when the portal signals
an ending state without enough evidence. The frontend route `/final` renders
the summary as a reason donut with percentages, total pagu/HPS, two-year
filters, and linked package evidence.

Phase 4 adds explainable sales intelligence to that projection: each package
gets an IT service category, keyword evidence, managed-service fit, a
high/medium/low priority score, and a recommended next action. Summary
breakdowns are available by organization, SPSE track, category, and priority;
the frontend uses these as clickable drill-down filters.

To backfill the existing SQLite leads without deleting it, run a dry run first
and then repeat without `--dry-run`:

```bash
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite-path data/salep_leads.db \
  --database-url "$DATABASE_URL" \
  --dry-run

python scripts/migrate_sqlite_to_postgres.py \
  --sqlite-path data/salep_leads.db \
  --database-url "$DATABASE_URL"
```

Phase 0 contract fixtures are in `tests/fixtures/inaproc/`. They cover the
canonical Si-RUP mapping and all Final reasons: contract completed, contract
terminated, contract stopped, and tender completed without a contract.

### Threads precision (Phase 5)

Threads records receive a canonical `threads:<post-id>` identity from the
provider ID, post code, URL path, or a content fingerprint fallback. The
deterministic gate runs before any LLM call and records relevance score/reason,
spam label/score, and quality flags. Clear non-buying, spam, and suspected fake
posts are dropped before analysis; accepted records retain the evidence for
marketing review. Successful LLM responses are cached by normalized content,
model, and prompt version in PostgreSQL (with an in-memory fallback for local
development).

Run the checked-in golden set after changing the rules:

```bash
PYTHONPATH=backend python scripts/evaluate_threads_golden.py
```

The fixture and regression tests are in `tests/fixtures/threads/golden_set.json`
and `tests/test_threads_precision.py`.

### Operational hardening (Phase 6)

Production compose menjalankan API dan scheduler sebagai proses terpisah:
`SALEP_PROCESS_ROLE=api` untuk Uvicorn dan `SALEP_PROCESS_ROLE=worker` untuk
`python -m app.worker`. Scheduler memakai PostgreSQL advisory lock dengan file
lock fallback, sehingga API dapat direplikasi tanpa menjalankan discovery ganda.
Source calls memakai retry exponential backoff dan circuit breaker. Metrics
Prometheus-compatible tersedia di `/metrics`, readiness di `/ready`, dan alert
webhook dikontrol oleh `ALERT_WEBHOOK_URL` serta cooldown.

Backup serta retention dijalankan eksplisit dari [OPERATIONS_RUNBOOK.md](../OPERATIONS_RUNBOOK.md):

```bash
PYTHONPATH=. python scripts/backup.py --database-url "$DATABASE_URL"
PYTHONPATH=. python scripts/retention.py --database-url "$DATABASE_URL" --dry-run
```
