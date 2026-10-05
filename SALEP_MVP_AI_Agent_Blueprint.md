# SALEP --- AI Sales Intelligence Platform MVP

> **Sales Intelligence Platform (SALEP)**\
> MVP: real-time keyword search → raw leads → AI analysis →
> product/service matching → lead scoring → Google Sheets.

## 1. Product Goal

SALEP membantu sales menemukan calon klien yang kemungkinan membutuhkan
layanan IT.

**MVP bukan membuat model AI sendiri.** Kita menggunakan LLM melalui API
dan membangun AI Agent di atasnya.

``` text
Keyword
  ↓
Real-time Source Search
  ↓
Raw Lead Results
  ↓
SALEP AI Agent
  ↓
Intent + Need + Product Matching + Lead Score
  ↓
Structured Lead JSON
  ↓
Google Sheets
  ↓
Sales
```

Contoh input:

``` text
keyword: "butuh aplikasi inventory"
time_range: "last 24 hours"
```

Contoh raw post:

``` text
Ada rekomendasi vendor yang bisa bikin aplikasi inventory?
Bisnis kami masih menggunakan Excel dan mulai kesulitan
tracking stok beberapa gudang.
```

Contoh output:

``` json
{
  "is_potential_lead": true,
  "intent": "looking_for_vendor",
  "industry": "distribution",
  "needs": ["inventory_system", "multi_warehouse"],
  "recommended_services": [
    {
      "name": "Custom Software Development",
      "match_score": 94,
      "reason": "The prospect explicitly needs an inventory system."
    }
  ],
  "lead_score": 92,
  "confidence": 0.94,
  "evidence": [
    "mencari vendor",
    "aplikasi inventory",
    "beberapa gudang"
  ]
}
```

------------------------------------------------------------------------

# 2. Scope MVP

## In Scope

-   Keyword-based real-time search.
-   Related/similar keyword expansion.
-   Time filter.
-   Source adapter architecture.
-   Raw result normalization.
-   AI lead qualification.
-   Intent detection.
-   Need/pain-point extraction.
-   Product/service matching.
-   Lead scoring.
-   Confidence score.
-   Evidence from source text.
-   Duplicate detection.
-   Google Sheets storage.
-   REST API dengan FastAPI.
-   Dockerization.
-   Basic logging.
-   Manual search endpoint.

## Out of Scope

-   Training LLM sendiri.
-   Fully autonomous sales outreach.
-   Automatic DM.
-   Sensitive identity/KYC verification.
-   Private/access-controlled data.
-   CRM integration.
-   Complex multi-agent architecture.
-   n8n.
-   Web dashboard.

Dashboard dan PostgreSQL menjadi fase berikutnya.

------------------------------------------------------------------------

# 3. Product Principle

Optimalkan **qualified sales opportunities**, bukan jumlah scraping.

MVP success metrics:

-   Relevant lead precision.
-   Percentage of leads with explicit IT buying intent.
-   Product matching accuracy.
-   Duplicate rate.
-   Search latency.
-   Number of qualified leads stored successfully.

------------------------------------------------------------------------

# 4. Architecture

``` text
                       Sales User
                           │
                         REST
                           │
                    ┌──────▼──────┐
                    │   FastAPI   │
                    └──────┬──────┘
                           │
                  ┌────────▼────────┐
                  │ Search Service  │
                  └────────┬────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
       Source Adapter  Source Adapter  Source Adapter
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                   Raw Lead Normalizer
                           │
                           ▼
                    SALEP AI Agent
                 ┌─────────┼─────────┐
                 ▼         ▼         ▼
              Intent     Need     Product
              Analysis  Extraction Matching
                 └─────────┼─────────┘
                           ▼
                      Lead Scoring
                           │
                           ▼
                  Structured Lead JSON
                           │
                           ▼
                    Google Sheets
```

------------------------------------------------------------------------

# 5. Technology Stack

  Layer          Technology          Purpose
  -------------- ------------------- ----------------------
  Language       Python 3.11+        Backend + agent
  Agent          OpenAI Agents SDK   Agent runtime
  Model          OpenAI API          LLM reasoning
  API            FastAPI             REST API
  Validation     Pydantic            Typed schemas
  Storage MVP    Google Sheets       Sales-facing data
  Container      Docker              Packaging
  Hosting        VPS                 Production runtime
  Future DB      PostgreSQL          Scalable persistence
  Future queue   Redis               Background jobs

OpenAI Agents SDK menyediakan Agent, tools, structured outputs,
guardrails, sessions, dan tracing. Agent + Runner menangani agent loop
dan tool execution.\
Official docs: https://openai.github.io/openai-agents-python/\
Quickstart: https://openai.github.io/openai-agents-python/quickstart/

------------------------------------------------------------------------

# 6. Why Not n8n Yet?

n8n adalah workflow automation/orchestration platform, bukan pengganti
Agent.

Untuk MVP:

``` text
API
 ↓
Search
 ↓
Analyze
 ↓
Save
```

cukup kita implementasikan langsung di Python.

Nanti n8n berguna untuk:

``` text
Schedule
 ↓
Trigger SALEP
 ↓
Analyze
 ↓
If score >= 80
 ↓
Notify Sales
```

Jadi:

-   **SALEP Agent = intelligence**
-   **n8n = optional automation**

------------------------------------------------------------------------

# 7. AI Agent Design

MVP menggunakan **satu Agent**.

Tugas Agent:

1.  Understand raw prospect content.
2.  Detect commercial/IT intent.
3.  Extract needs.
4.  Extract pain points.
5.  Match needs against company services.
6.  Produce evidence.
7.  Produce confidence.
8.  Produce structured output.

Agent tidak boleh:

-   mengarang fakta;
-   mengklaim identitas terverifikasi;
-   menyimpulkan data sensitif;
-   mengarang kebutuhan;
-   menghubungi prospek.

------------------------------------------------------------------------

# 8. Product Knowledge

Agent membutuhkan katalog layanan perusahaan.

`data/products.json`:

``` json
[
  {
    "id": "svc-001",
    "name": "Custom Software Development",
    "description": "Development of custom business applications.",
    "keywords": [
      "custom software",
      "business application",
      "internal system"
    ]
  },
  {
    "id": "svc-002",
    "name": "Web Development",
    "description": "Corporate and business web application development.",
    "keywords": [
      "website",
      "web app",
      "company website"
    ]
  },
  {
    "id": "svc-003",
    "name": "Mobile App Development",
    "description": "Android and iOS application development.",
    "keywords": [
      "android app",
      "ios app",
      "mobile application"
    ]
  },
  {
    "id": "svc-004",
    "name": "AI Automation",
    "description": "AI-powered workflow and business process automation.",
    "keywords": [
      "AI",
      "automation",
      "AI agent"
    ]
  }
]
```

Jangan membiarkan Agent merekomendasikan layanan yang tidak ada di
katalog.

------------------------------------------------------------------------

# 9. Structured Output

Gunakan Pydantic:

``` python
from pydantic import BaseModel, Field


class ProductMatch(BaseModel):
    product_id: str
    product_name: str
    match_score: int = Field(ge=0, le=100)
    reason: str


class LeadAnalysis(BaseModel):
    is_potential_lead: bool
    intent: str
    industry: str | None
    needs: list[str]
    pain_points: list[str]
    recommended_services: list[ProductMatch]
    lead_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]
```

Structured Outputs lebih aman daripada meminta model mengembalikan JSON
bebas karena schema dapat divalidasi.\
Docs: https://developers.openai.com/api/docs/guides/structured-outputs

------------------------------------------------------------------------

# 10. Intent Taxonomy

Gunakan nilai terkontrol:

``` text
looking_for_vendor
requesting_recommendation
evaluating_solution
problem_identification
general_discussion
learning
job_seeking
irrelevant
unknown
```

High-value:

``` text
looking_for_vendor
requesting_recommendation
evaluating_solution
```

Low-value:

``` text
learning
general_discussion
job_seeking
irrelevant
```

------------------------------------------------------------------------

# 11. Lead Scoring

Gunakan formula deterministic di aplikasi:

``` text
Intent strength       0–40
Problem clarity       0–20
IT relevance          0–20
Product fit           0–20
----------------------------
Total                 0–100
```

Contoh:

``` text
Explicit vendor search      35/40
Clear business problem      18/20
Strong IT relevance         20/20
Strong product match        18/20
-----------------------------------
Total                       91/100
```

LLM memberikan evidence dan klasifikasi; aplikasi menghitung score final
bila memungkinkan.

------------------------------------------------------------------------

# 12. Real-Time Search

Real-time berarti user melakukan query saat itu dan sistem memanggil
source yang dikonfigurasi, bukan hanya membaca dataset lama.

Request:

``` http
POST /api/v1/search
Content-Type: application/json
```

``` json
{
  "keywords": [
    "butuh aplikasi inventory",
    "mencari vendor ERP"
  ],
  "time_range": {
    "from": "2026-10-04T00:00:00Z",
    "to": "2026-10-05T23:59:59Z"
  },
  "sources": ["source_a"],
  "limit": 50
}
```

Response:

``` json
{
  "query_id": "qry_123",
  "total_found": 17,
  "total_analyzed": 17,
  "qualified": 7,
  "leads": []
}
```

------------------------------------------------------------------------

# 13. Similar Keyword Search

Exact matching saja tidak cukup.

Query:

``` text
"butuh aplikasi inventory"
```

dapat diperluas menjadi:

``` text
inventory system
inventory application
stock management system
warehouse management
sistem stok
aplikasi gudang
software inventory
ERP inventory
```

## MVP

Gunakan keyword groups sederhana:

``` json
{
  "inventory": [
    "inventory",
    "stock management",
    "warehouse management",
    "sistem stok",
    "aplikasi gudang"
  ]
}
```

## Later

Gunakan embeddings/semantic search.

Jangan memasukkan vector database ke MVP sebelum kebutuhan terbukti.

------------------------------------------------------------------------

# 14. Source Adapter

Jangan coupling Agent langsung ke Threads/LinkedIn/X/Facebook.

Gunakan interface:

``` python
from typing import Protocol


class SourceAdapter(Protocol):

    async def search(
        self,
        keywords: list[str],
        start_date: str,
        end_date: str,
        limit: int
    ) -> list[dict]:
        ...
```

Struktur:

``` text
app/
└── sources/
    ├── base.py
    ├── source_a.py
    ├── source_b.py
    └── source_c.py
```

Dengan ini source dapat diganti tanpa mengubah Agent.

------------------------------------------------------------------------

# 15. Source/Compliance Boundary

Untuk sumber sosial, gunakan:

-   official API;
-   authorized data provider;
-   atau mekanisme akses yang memang diizinkan.

Jangan membuat MVP bergantung pada bypass:

-   login;
-   CAPTCHA;
-   rate limit;
-   access control;
-   private profiles;
-   platform restrictions.

Jika suatu source tidak mendukung kemampuan pencarian yang diperlukan
melalui akses yang tersedia, adapter mengembalikan status unsupported.

``` json
{
  "source": "example",
  "status": "unsupported",
  "reason": "Required search capability is unavailable through configured access."
}
```

Ini juga membuat arsitektur kita lebih tahan terhadap perubahan
platform.

------------------------------------------------------------------------

# 16. Normalized Raw Lead

Semua source harus menghasilkan bentuk yang sama:

``` json
{
  "source": "example_source",
  "source_url": "https://example.com/post/123",
  "author_name": "Example Person",
  "author_profile_url": "https://example.com/profile/123",
  "published_at": "2026-10-05T08:00:00Z",
  "content": "We are looking for a vendor to build an inventory system.",
  "matched_keyword": "inventory system"
}
```

Agent hanya bekerja dengan normalized data.

------------------------------------------------------------------------

# 17. Duplicate Detection

Post yang sama dapat ditemukan oleh banyak keyword.

``` text
Keyword A → Post X
Keyword B → Post X
Keyword C → Post X
```

Primary key:

``` text
source + source_url
```

Fallback:

``` text
hash(normalized_content + author + published_at)
```

Jangan memasukkan post yang sama berkali-kali ke spreadsheet.

------------------------------------------------------------------------

# 18. Google Sheets Schema

Recommended columns:

  Column                 Meaning
  ---------------------- ---------------------------------
  lead_id                Internal ID
  source                 Source
  source_url             Original URL
  author_name            Public author
  author_profile_url     Public profile
  published_at           Original timestamp
  matched_keyword        Search keyword
  content                Raw content
  is_potential_lead      Qualification
  intent                 Intent category
  industry               Detected industry
  needs                  Extracted needs
  pain_points            Pain points
  recommended_services   Product match
  lead_score             0--100
  confidence             0--1
  evidence               Supporting text
  analyzed_at            Analysis timestamp
  status                 New/Reviewed/Rejected/Contacted

------------------------------------------------------------------------

# 19. Google Sheets Service

Agent jangan mengakses spreadsheet secara langsung.

Gunakan service:

``` text
app/
└── services/
    └── google_sheets.py
```

Interface:

``` python
append_lead(lead)
append_leads(leads)
find_existing_lead(source_url)
```

Arsitektur:

``` text
Agent
 ↓
Structured Result
 ↓
Application Service
 ↓
Google Sheets Service
 ↓
Google Sheets
```

Agent bertugas memahami data.

Application bertugas menyimpan data.

------------------------------------------------------------------------

# 20. API Endpoints

## Health

``` http
GET /health
```

``` json
{
  "status": "ok"
}
```

## Search

``` http
POST /api/v1/search
```

``` json
{
  "keywords": ["butuh aplikasi ERP"],
  "start_date": "2026-10-05",
  "end_date": "2026-10-05",
  "sources": ["source_a"],
  "limit": 20
}
```

## Analyze one lead

Untuk development/testing:

``` http
POST /api/v1/leads/analyze
```

``` json
{
  "content": "Kami sedang mencari vendor ERP."
}
```

## Get job status

Jika nanti menggunakan background processing:

``` http
GET /api/v1/jobs/{job_id}
```

------------------------------------------------------------------------

# 21. Project Structure

``` text
salep/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── health.py
│   │       ├── search.py
│   │       └── leads.py
│   │
│   ├── agent/
│   │   ├── salep_agent.py
│   │   ├── instructions.py
│   │   ├── schemas.py
│   │   └── tools.py
│   │
│   ├── sources/
│   │   ├── base.py
│   │   ├── source_a.py
│   │   └── source_b.py
│   │
│   ├── services/
│   │   ├── search_service.py
│   │   ├── lead_service.py
│   │   ├── scoring_service.py
│   │   └── google_sheets.py
│   │
│   └── core/
│       ├── config.py
│       └── logging.py
│
├── data/
│   └── products.json
│
├── tests/
│   ├── test_agent.py
│   ├── test_scoring.py
│   └── test_deduplication.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

------------------------------------------------------------------------

# 22. Environment Variables

`.env.example`

``` env
OPENAI_API_KEY=
OPENAI_MODEL=

GOOGLE_SHEETS_ID=
GOOGLE_SERVICE_ACCOUNT_JSON=

APP_ENV=development
LOG_LEVEL=INFO
```

Never commit:

``` text
.env
service-account.json
API keys
private credentials
```

------------------------------------------------------------------------

# 23. Dependencies

Initial:

``` txt
openai-agents
fastapi
uvicorn[standard]
pydantic
pydantic-settings
python-dotenv
gspread
google-auth
httpx
```

Later only if required:

``` txt
redis
sqlalchemy
psycopg
alembic
```

------------------------------------------------------------------------

# 24. Agent Implementation

Simplified:

``` python
from agents import Agent, Runner
from pydantic import BaseModel, Field


class ProductMatch(BaseModel):
    product_id: str
    product_name: str
    match_score: int = Field(ge=0, le=100)
    reason: str


class LeadAnalysis(BaseModel):
    is_potential_lead: bool
    intent: str
    industry: str | None
    needs: list[str]
    pain_points: list[str]
    recommended_services: list[ProductMatch]
    lead_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]


agent = Agent(
    name="SALEP Agent",
    instructions=(
        "You are SALEP, a sales intelligence analyst. "
        "Analyze public prospect content. "
        "Determine IT/commercial intent, business needs, pain points, "
        "relevant company services, and supporting evidence. "
        "Never invent information."
    ),
    output_type=LeadAnalysis,
)


async def analyze_lead(content: str):
    result = await Runner.run(agent, content)
    return result.final_output
```

------------------------------------------------------------------------

# 25. Agent Tools

First tool:

``` python
@function_tool
def search_products(keyword: str):
    """
    Search company products/services relevant to a keyword.
    """
    ...
```

Second tool:

``` python
@function_tool
def get_product(product_id: str):
    """
    Get detailed information about a company service.
    """
    ...
```

Later:

``` text
search_products()
get_product()
save_lead()
get_lead()
```

Tools should be narrow and explicit. Do not give the Agent unrestricted
database access.

OpenAI function/tool calling is designed to connect models to
application functions and external data:\
https://developers.openai.com/api/docs/guides/function-calling

------------------------------------------------------------------------

# 26. Search → Agent → Sheets

Core application flow:

``` python
async def run_search(request):

    keywords = expand_keywords(request.keywords)

    raw_results = await search_sources(
        keywords=keywords,
        start_date=request.start_date,
        end_date=request.end_date,
        limit=request.limit
    )

    normalized = normalize_results(raw_results)

    unique_results = deduplicate(normalized)

    analyses = []

    for lead in unique_results:
        analysis = await analyze_lead(lead.content)

        final_lead = build_lead_record(
            lead,
            analysis
        )

        analyses.append(final_lead)

    await save_to_google_sheets(analyses)

    return analyses
```

Ini adalah inti MVP.

------------------------------------------------------------------------

# 27. Real-Time Processing Strategy

Untuk MVP gunakan:

``` text
Request
 ↓
Search
 ↓
Analyze
 ↓
Save
 ↓
Response
```

Dengan `limit` kecil, misalnya 20--50.

Jangan langsung menganalisis 5.000 result dalam satu HTTP request.

Setelah MVP:

``` text
Request
 ↓
Create Job
 ↓
Return job_id
 ↓
Worker
 ↓
Search
 ↓
Analyze
 ↓
Save
```

Kemudian:

``` http
GET /api/v1/jobs/{job_id}
```

menghasilkan:

``` json
{
  "status": "running",
  "processed": 142,
  "total": 500
}
```

------------------------------------------------------------------------

# 28. Testing

Buat evaluation dataset:

``` text
tests/evaluation/leads.json
```

### High intent

``` text
Mencari vendor untuk membuat aplikasi HRIS.
```

Expected:

``` text
is_potential_lead = true
```

### Medium intent

``` text
Ada yang pernah menggunakan ERP untuk perusahaan distribusi?
```

Expected:

``` text
potential lead = medium
```

### Low intent

``` text
Saya sedang belajar membuat aplikasi inventory.
```

Expected:

``` text
is_potential_lead = false
```

### Irrelevant

``` text
Jual laptop gaming murah.
```

Expected:

``` text
is_potential_lead = false
```

Measure:

``` text
Precision
Recall
False Positive Rate
Product Match Accuracy
```

------------------------------------------------------------------------

# 29. Logging

Setiap search mempunyai:

``` text
query_id
timestamp
keywords
sources
result_count
analyzed_count
qualified_count
duration
error_count
```

Jangan log API keys atau informasi sensitif yang tidak dibutuhkan.

------------------------------------------------------------------------

# 30. Error Handling

Handle:

``` text
Source unavailable
API timeout
LLM timeout
LLM rate limit
Google Sheets unavailable
Invalid AI output
Duplicate lead
```

Satu lead gagal tidak boleh menggagalkan seluruh batch:

``` text
Lead 1 → success
Lead 2 → success
Lead 3 → failed
Lead 4 → success
```

Simpan failure reason di log.

------------------------------------------------------------------------

# 31. Docker

`Dockerfile`:

``` dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`docker-compose.yml` MVP:

``` yaml
services:
  salep-api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

Later:

``` yaml
services:
  salep-api:
    ...

  salep-worker:
    ...

  postgres:
    ...

  redis:
    ...
```

------------------------------------------------------------------------

# 32. VPS Deployment

Initial:

``` text
Internet
   │
   ▼
Nginx / Reverse Proxy
   │
   ▼
SALEP Docker API
   │
   ├── OpenAI API
   │
   └── Google Sheets
```

Use HTTPS in production.

The OpenAI API key remains on the VPS and is never sent to the frontend.

------------------------------------------------------------------------

# 33. Development Milestones

## M1 --- Agent

``` text
Text
 ↓
SALEP Agent
 ↓
Structured JSON
```

Done when:

-   Agent runs.
-   Pydantic output validates.
-   20+ sample leads can be tested.

## M2 --- Product Matching

``` text
Lead
 ↓
Agent
 ↓
Product Catalog
 ↓
Recommendation
```

Done when:

-   Agent can select relevant service.
-   Recommendation has reason.
-   Unknown needs do not force fake recommendations.

## M3 --- Source Adapter

``` text
Keyword
 ↓
Source
 ↓
Raw Results
```

Done when:

-   Keyword works.
-   Date range works.
-   Results are normalized.
-   Source URL is retained.
-   Duplicates are removed.

## M4 --- Google Sheets

``` text
Analyzed Leads
 ↓
Google Sheets
```

Done when:

-   Rows append correctly.
-   Duplicate URL is rejected.
-   Columns stay consistent.

## M5 --- FastAPI

``` text
POST /api/v1/search
```

Done when:

-   Request validation works.
-   Search works.
-   Agent works.
-   Sheets persistence works.
-   JSON response works.

## M6 --- Docker

``` text
docker compose up
```

Done when:

-   Container starts.
-   `/health` works.
-   Environment variables load.
-   LLM API works.
-   Google Sheets works.

------------------------------------------------------------------------

# 34. Definition of Done

A user can:

1.  Enter one or more keywords.
2.  Set a time range.
3.  Select an available source.
4.  Trigger a real-time search.
5.  Receive raw results.
6.  Normalize and deduplicate them.
7.  Analyze each result with SALEP Agent.
8.  Detect intent.
9.  Extract needs/pain points.
10. Match company services.
11. Calculate lead score.
12. Store results in Google Sheets.
13. Receive a structured API response.
14. Run the whole application using Docker.

Example:

``` text
POST /api/v1/search

{
  "keywords": ["butuh aplikasi ERP"],
  "start_date": "2026-10-05",
  "end_date": "2026-10-05",
  "sources": ["source_a"],
  "limit": 20
}

        ↓

20 raw results
        ↓
18 unique results
        ↓
18 analyzed
        ↓
7 qualified leads
        ↓
Google Sheets
```

------------------------------------------------------------------------

# 35. Development Order

Follow this order:

``` text
01. Create Python project
        ↓
02. Install OpenAI Agents SDK
        ↓
03. Configure API key
        ↓
04. Build SALEP Agent
        ↓
05. Define Pydantic schemas
        ↓
06. Test with static leads
        ↓
07. Add product catalog
        ↓
08. Add search_products tool
        ↓
09. Build source adapter
        ↓
10. Implement real-time search
        ↓
11. Add deduplication
        ↓
12. Add Google Sheets
        ↓
13. Connect Search → Agent → Sheets
        ↓
14. Add FastAPI
        ↓
15. Add tests
        ↓
16. Dockerize
        ↓
17. Deploy to VPS
```

------------------------------------------------------------------------

# 36. Documentation

Start with:

1.  OpenAI Agents SDK\
    https://openai.github.io/openai-agents-python/

2.  Quickstart\
    https://openai.github.io/openai-agents-python/quickstart/

3.  Agents\
    https://openai.github.io/openai-agents-python/agents/

4.  Tools\
    https://openai.github.io/openai-agents-python/tools/

5.  Function Calling\
    https://developers.openai.com/api/docs/guides/function-calling

6.  Structured Outputs\
    https://developers.openai.com/api/docs/guides/structured-outputs

Learn in this order:

``` text
Agent
 ↓
Instructions
 ↓
Runner
 ↓
Tool
 ↓
Function Calling
 ↓
Structured Output
 ↓
Pydantic
 ↓
FastAPI
 ↓
Docker
```

------------------------------------------------------------------------

# 37. Future Roadmap

## V1

``` text
MVP
+
PostgreSQL
+
Web Dashboard
+
Pagination
+
Authentication
```

## V1.5

``` text
+
Background Workers
+
Redis
+
Scheduled Search
+
Multiple Source Adapters
```

## V2

``` text
+
Semantic Search
+
Embeddings
+
Knowledge Base
+
Advanced Lead Scoring
+
CRM Integration
```

## V3

``` text
+
n8n
+
Autonomous Workflows
+
Sales Notifications
+
Advanced Agent Orchestration
```

------------------------------------------------------------------------

# 38. Final Target Architecture

``` text
                         SALEP
                           │
                    ┌──────▼──────┐
                    │ Web / API   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Search      │
                    │ Service     │
                    └──────┬──────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Source A      Source B      Source C
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                       Raw Leads
                           │
                           ▼
                 ┌─────────────────┐
                 │   SALEP AGENT   │
                 │                 │
                 │ Intent          │
                 │ Need            │
                 │ Pain Point      │
                 │ Product Match   │
                 │ Lead Score      │
                 │ Evidence        │
                 └────────┬────────┘
                          │
                   Structured JSON
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
        Google Sheets             PostgreSQL
            MVP                     Later
              │                       │
              └───────────┬───────────┘
                          ▼
                    Sales Dashboard
```

## Core Philosophy

> **Search finds the signal.**\
> **The Agent understands the signal.**\
> **Product matching turns the signal into an opportunity.**\
> **Storage makes it useful to Sales.**
