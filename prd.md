# SALEP — Raw Lead, Promotion, and Sales Assignment

Status: Draft for discussion  
Date: 2026-10-15  
Storage: PostgreSQL as the single source of truth

## 1. Product goal

SALEP must preserve every usable scraping result, keep the original LLM decision explainable, allow Marketing to correct false negatives, and only expose validated opportunities to Sales.

The existing discovery, LLM analysis, Marketing validation, Sales follow-up, and Inaproc analytics capabilities remain in scope. This change adds explicit raw-data, promotion, assignment, and audit layers around them.

## 2. Problem

The current social-lead flow writes the analyzed result directly to `leads`. That makes these concepts difficult to distinguish:

- source evidence captured by the scraper;
- quality and deduplication decisions;
- the original LLM analysis;
- Marketing's human decision;
- Sales ownership and follow-up history.

The system must not lose a potentially valuable post because the scraper quality gate or LLM classified it incorrectly.

## 3. Target flow

```text
Scraping → raw_leads (PostgreSQL)
         → quality check + deduplication
         → LLM analysis
         → raw_leads updated with analysis
         → automatic or manual promotion
         → leads.marketing_status = pending
         → Marketing validates
         → Sales assignment
         → Sales follow-up and status history
```

Procurement data remains a separate source path:

```text
SiRUP/SPSE/Inaproc → procurement_packages
                  → procurement_events
                  → Final analytics
                  → sales opportunity / assignment when approved
```

## 4. Actors and permissions

### Marketing

- View and filter all raw records and leads.
- Review quality, deduplication, and LLM decisions.
- Promote a raw record manually.
- Set lead status to `pending`, `valid`, or `invalid`.
- Assign and unassign a valid lead to a Sales user.
- Run manual discovery and control the scheduler.

### Sales

- View valid leads allowed by the assignment policy.
- View lead evidence and the original LLM decision.
- Update Sales follow-up status and add notes.

### Super Admin

- Manage user accounts.
- Read audit data when the administration policy permits it.

## 5. Functional requirements

### FR-RAW — Raw capture

1. Every normalized scraper result is persisted in `raw_leads` before quality filtering and LLM processing.
2. The original content, source URL, author, timestamps, matched keyword, and optional raw payload are retained.
3. A repeat observation updates `last_seen_at` and `observation_count` instead of creating a second logical record.

### FR-QUALITY — Quality and deduplication

1. Quality checking labels records; it must not silently delete evidence.
2. Quality results include a status, score, reason, spam flag, and quality flags.
3. Deduplication uses a stable source key such as `source:canonical_post_id` or `source:source_url`.
4. A duplicate observation is auditable through counters and run logs.

### FR-LLM — Analysis

1. Eligible raw records are analyzed automatically by the SALEP Agent.
2. The raw record stores the latest LLM decision, score, confidence, model, prompt version, structured analysis, and failure reason.
3. LLM failure is retryable and does not remove the raw record.
4. The original LLM result remains unchanged when Marketing overrides it.

### FR-PROMOTION — Promotion to lead

1. LLM-positive records may be automatically promoted to `leads` with `promotion_source = 'llm'` and `marketing_status = 'pending'`.
2. LLM-negative or uncertain records remain available in `raw_leads`.
3. Marketing may promote any eligible raw record with `promotion_source = 'manual'`.
4. A raw record may point to at most one current lead.

### FR-MARKETING — Human validation

1. Marketing can set `marketing_status` to `pending`, `valid`, or `invalid`.
2. When Marketing changes a lead status, the backend takes the reviewer identity from the authenticated session. The client must not submit `reviewed_by_user_id`.
3. The lead stores the latest Marketing reviewer, review timestamp, and optional review note so the identity is visible on the lead detail.
4. Changing Marketing status must create an audit event containing the previous status, new status, reviewer, API, and request ID.
5. A valid lead may be synchronized to configured downstream destinations such as Google Sheets.

Implementation contract:

- Authentication middleware exposes the authenticated `user_id` on request state alongside the role and username.
- `PATCH /api/v1/leads/{lead_id}/status` accepts the new status and an optional review note; it does not accept a reviewer ID.
- The repository updates the lead reviewer fields and the activity log in one PostgreSQL transaction.
- The lead detail API resolves the reviewer username from `auth_users` for display.

### FR-ASSIGNMENT — Sales ownership

1. Marketing can assign a valid lead to a Sales user.
2. A lead has at most one active assignment, but keeps historical assignments.
3. Assign, unassign, and reassign actions are auditable.
4. The final visibility rule for valid-but-unassigned leads must be agreed before implementation.

### FR-SALES — Follow-up

1. Sales may update `sales_status` only for valid leads.
2. Existing statuses remain: `Belum Dihubungi`, `Sedang Dihubungi`, `Closing`, and `Batal`.
3. Every transition stores the actor, note, previous status, new status, and timestamp.

### FR-AUDIT — Observability

1. `scrape_runs` remains the summary of a run.
2. `scrape_run_logs` records important scraper, quality, LLM, and promotion events.
3. `activity_logs` records user CRUD, API access, validation, promotion, assignment, and Sales actions.
4. Passwords, session tokens, and full sensitive payloads must never be logged.

## 6. Data model additions

- `raw_leads`: source evidence, processing state, LLM result, and promotion state.
- `lead_assignments`: active and historical Sales ownership.
- `activity_logs`: user and API audit trail.
- `scrape_run_logs`: detailed events belonging to `scrape_runs`.
- `leads.raw_lead_id`: link from a promoted lead to its source raw record.
- `leads.promotion_source`: `llm`, `manual`, or `legacy`.
- `leads.marketing_reviewed_by_user_id`: the authenticated Marketing account that last reviewed the lead.
- `leads.marketing_reviewed_at`: timestamp of that review.
- `leads.marketing_review_note`: optional note explaining the review decision.

## 7. Non-goals for this change

- Replacing the LLM provider.
- Redesigning the Inaproc scraper.
- Automatically changing a Marketing decision from an LLM score.
- Deleting existing leads during migration.
- Implementing a full CRM or contact database.

## 8. Acceptance criteria

- A scraper result remains queryable even when quality or LLM processing fails.
- The same source post does not create duplicate logical raw records.
- Marketing can find an LLM-negative raw record and promote it manually.
- A promoted lead retains a link to its raw evidence and original LLM decision.
- A lead marked `valid` shows the Marketing username and timestamp that performed the review.
- A review identity cannot be spoofed through request JSON or query parameters.
- Sales cannot update or see a lead that is not valid.
- A lead cannot have two active Sales assignments.
- Every validation, promotion, assignment, and Sales status change is auditable.
- Existing social, SPSE, Inaproc, authentication, and scheduler behavior continues to work during rollout.

## 9. Rollout principle

Implement this incrementally behind PostgreSQL migrations. Backfill existing `leads` as legacy-promoted raw records first, then switch new discovery writes to the raw-first flow. Do not delete or rewrite existing business history.
