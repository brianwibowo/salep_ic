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
# Unit tests (no API key needed)
pytest tests/test_scoring.py tests/test_deduplication.py -v

# Agent tests (requires OPENAI_API_KEY)
pytest tests/test_agent.py -v
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
- Pencarian manual memakai 1–10 keyword eksplisit, tanpa ekspansi sinonim otomatis yang menambah pemakaian Apify. Actor Threads tetap sama. Filter tanggal dilakukan pada hasil bertanggal; posting tanpa tanggal tetap disertakan. Batas hasil tidak sama dengan jumlah posting yang ditagihkan actor.
- Alternatif cron eksternal: set `AUTO_SEARCH_ENABLED=false` untuk menghindari dua scheduler, lalu gunakan `*/30 * * * * cd /path/to/salep && SALEP_API_URL=http://127.0.0.1:8000 bash scripts/run_search.sh`. Script memakai pool konfigurasi yang sama dan sesi marketing sementara. API lain juga memerlukan login `/api/v1/auth/login` dan cookie responsnya.

Tes lokal tanpa panggilan provider:

```bash
pytest tests/test_api_endpoints.py tests/test_discovery.py tests/test_scoring.py tests/test_deduplication.py tests/test_leads_rbac.py -q
```
