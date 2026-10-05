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
