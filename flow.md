# SALEP — Flow Specification

## 1. Social lead flow

```text
Marketing manual search / Scheduler
                ↓
        Threads / LinkedIn scraper
                ↓
          raw_leads in PostgreSQL
                ↓
       quality check + deduplication
                ↓
             LLM analysis
                ↓
 raw_leads.llm_* and processing status updated
                ↓
       ┌───────────────────────┐
       │ LLM relevant           │
       │ auto-promote to leads  │
       └───────────┬───────────┘
                   │
       ┌───────────▼───────────┐
       │ LLM negative/uncertain │
       │ remain raw and reviewable│
       └───────────┬───────────┘
                   │ optional manual promotion
                   ▼
       leads.marketing_status = pending
                   ↓
           Marketing validation
          ┌────────┼────────┐
          ▼        ▼        ▼
       pending   valid    invalid
                    ↓
             Assign to Sales
                    ↓
              Sales follow-up
                    ↓
       sales_status + notes + audit log
```

## 2. Meaning of each stage

### Raw capture

The scraper response is normalized and stored first. The record includes the original content and provenance so later decisions can be explained.

### Quality check

Checks technical/data quality such as empty content, malformed URL, spam signals, and parser issues. It labels the record; it does not erase it.

### Deduplication

Uses a stable source identity, preferably `source + canonical_post_id`, otherwise `source + source_url`. Repeated observations update the existing raw record's last-seen data and counters.

### LLM analysis

The Agent extracts intent, needs, pain points, service matches, evidence, confidence, and a lead decision. The result is stored with model and prompt metadata.

### Promotion

Promotion creates or links a record in `leads`. The raw record remains the evidence source. LLM promotion and Marketing manual promotion are different sources and must remain distinguishable.

### Marketing validation

Marketing makes the final qualification decision. This decision is separate from the LLM decision.

When Marketing changes the status, the backend resolves the logged-in account from the HttpOnly session and stores `marketing_reviewed_by_user_id`, `marketing_reviewed_at`, and the optional review note on the lead. The same transition is written to `activity_logs` with the old status, new status, endpoint, and request ID. The frontend only sends the new status and note; it never sends the reviewer identity.

### Assignment and Sales

Only valid leads can be assigned. Assignment history is append-only; only one assignment can be active at a time. Sales updates follow-up status and notes without changing the original raw or LLM data.

## 3. State model

```text
raw_leads.processing_status:
captured → quality_checked → queued_for_llm → processing → analyzed
                                      └──────→ quality_rejected
processing → analysis_failed → queued_for_llm (retry)

raw_leads.promotion_status:
not_promoted → promoted
not_promoted → manually_promoted
not_promoted → excluded

leads.marketing_status:
pending ↔ valid
pending ↔ invalid

lead_assignments:
unassigned → assigned → unassigned → assigned
```

## 4. Procurement flow

```text
SiRUP / SPSE / Inaproc adapters
                ↓
       source_documents snapshots
                ↓
       procurement_packages upsert
                ↓
       procurement_events on change
                ↓
           Final analytics
                ↓
       validated opportunity / assignment
```

Procurement packages are not forced into the social `raw_leads` table. They retain their existing package, snapshot, event, and Final analytics model. A future opportunity layer may connect both sources to the same Sales assignment workflow.

## 5. Failure behavior

- Scraper failure: finish the `scrape_runs` record as failed and write a `scrape_run_logs` error event.
- Quality rejection: keep the raw record and its reason.
- Duplicate observation: update `last_seen_at` and `observation_count`; do not create a second logical post.
- LLM failure: keep raw content, mark `analysis_failed`, and allow retry.
- Manual promotion: preserve the original LLM decision and record the actor in `activity_logs`.
- Marketing validation: persist the authenticated reviewer and timestamp on the lead, then append the full transition to `activity_logs`.
- Assignment failure: do not change the lead's current assignment unless the transaction succeeds.

## 6. Audit boundaries

`activity_logs` records user/API actions. `scrape_run_logs` records worker and pipeline events. Neither table should contain passwords, session cookies, or complete sensitive API responses.
