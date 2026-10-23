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

Marketing selects a review result and, for valid leads, an active Sales recipient. One save sends `marketing_status`, `sales_user_id`, optional `review_note`, and `expected_version` to `PATCH /api/v1/leads/{lead_id}/status`. The backend derives the reviewer from the HttpOnly session and saves reviewer, timestamp, assignment history, and the audit transition in a single PostgreSQL transaction.

The backend locks the lead and verifies its `review_version` before updating. When two Marketing accounts submit the same version, only one succeeds. The other receives HTTP 409, sees an explicit conflict message, and must reload and review the latest state before submitting again. There is no automatic resubmission.

### Assignment and Sales

Valid leads require an active Sales recipient. The same form is used on social leads and SPSE. Only one assignment can be active; reassignment closes the previous record and creates another. Pending/invalid closes the active assignment. Sales can only list, view, count, and update valid leads assigned to that account. Sales follow-up requires a real note; Marketing review notes remain optional. Legacy valid leads without an owner remain in Marketing's queue until explicitly assigned.

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

## 7. Marketing progress monitoring and filters

1. Assigned Sales saves a status and follow-up message (for example Closing with a PO/onboarding note). The authenticated username and timestamp are saved with the transition.
2. Marketing sees the latest status/message in the social or SPSE table. Opening detail or refreshing progress loads the latest data; older notes remain expandable, including notes from previous Sales owners.
3. Marketing combines validation, source, progress, Sales owner/assigned/unassigned, and arrival-time filters, then applies them together. Applying or resetting filters returns pagination to page one.
4. Unassigned automatically selects valid leads without an active assignment. Selecting a named Sales user matches only current ownership; closed assignment history does not count.
5. Arrival time uses `created_at` with inclusive WIB boundaries. Month and year inputs expand into date ranges. The same conditions determine both table rows and pagination totals.

## 8. Soft-delete flow

1. Marketing confirms removal. The backend resolves the actor from the login session and locks the lead row.
2. The same transaction records deletion time/account and appends `SOFT_DELETE_LEAD`. Lead data, Sales messages, assignments, and previous audit history remain intact.
3. Active lists, totals, stats, detail, schedules and write endpoints no longer expose the deleted lead. A repeated delete returns 404; any audit failure rolls back the deletion.
4. Scraper rediscovery matches the retained identity and skips the tombstone. It cannot restore or overwrite deleted evidence. Historical external exports are not physically removed, but deleted references are filtered from the recent-leads API.
5. This release does not add a trash screen, restore button, or permanent purge. Apply `0008_lead_soft_delete` before using the updated API.
