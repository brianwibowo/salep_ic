-- SALEP PostgreSQL migration: raw leads, promotion, assignment, and audit trail
--
-- Intended to run after the existing source-of-truth/auth migrations.
-- This script is idempotent for the objects it owns. Review in staging first.

BEGIN;

CREATE TABLE IF NOT EXISTS raw_leads (
    raw_lead_id              VARCHAR(80) PRIMARY KEY,
    source                   VARCHAR(40) NOT NULL,
    source_url               TEXT NOT NULL,
    external_id              VARCHAR(255),
    canonical_post_id        VARCHAR(255),
    author_name              VARCHAR(255),
    author_profile_url       TEXT,
    published_at             TIMESTAMPTZ,
    matched_keyword          VARCHAR(255),
    content                  TEXT NOT NULL,
    raw_payload              JSONB NOT NULL DEFAULT '{}'::jsonb,
    dedup_key                VARCHAR(512) NOT NULL,
    first_seen_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    observation_count        INTEGER NOT NULL DEFAULT 1,
    processing_status        VARCHAR(32) NOT NULL DEFAULT 'captured',
    quality_status           VARCHAR(32) NOT NULL DEFAULT 'pending',
    quality_score            INTEGER NOT NULL DEFAULT 0,
    quality_reason           TEXT,
    quality_flags            JSONB NOT NULL DEFAULT '[]'::jsonb,
    spam_label               VARCHAR(32) NOT NULL DEFAULT 'unknown',
    spam_score               INTEGER NOT NULL DEFAULT 0,
    is_spam                  BOOLEAN NOT NULL DEFAULT false,
    llm_status               VARCHAR(32) NOT NULL DEFAULT 'pending',
    llm_decision             VARCHAR(32),
    llm_score                INTEGER,
    llm_confidence           NUMERIC(5,4),
    llm_model                VARCHAR(120),
    llm_prompt_version       VARCHAR(80),
    llm_analysis             JSONB,
    llm_error                TEXT,
    promotion_status         VARCHAR(32) NOT NULL DEFAULT 'not_promoted',
    promotion_source         VARCHAR(20),
    promoted_lead_id         VARCHAR(80),
    promoted_by_user_id      VARCHAR(40),
    promoted_at              TIMESTAMPTZ,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_raw_leads_dedup_key UNIQUE (dedup_key),
    CONSTRAINT ck_raw_leads_quality_score CHECK (quality_score BETWEEN 0 AND 100),
    CONSTRAINT ck_raw_leads_spam_score CHECK (spam_score BETWEEN 0 AND 100),
    CONSTRAINT ck_raw_leads_llm_score CHECK (llm_score IS NULL OR llm_score BETWEEN 0 AND 100),
    CONSTRAINT ck_raw_leads_llm_confidence CHECK (llm_confidence IS NULL OR (llm_confidence >= 0 AND llm_confidence <= 1)),
    CONSTRAINT ck_raw_leads_processing_status CHECK (processing_status IN ('captured', 'quality_checked', 'quality_rejected', 'queued_for_llm', 'processing', 'analyzed', 'analysis_failed')),
    CONSTRAINT ck_raw_leads_quality_status CHECK (quality_status IN ('pending', 'accepted', 'rejected', 'duplicate')),
    CONSTRAINT ck_raw_leads_llm_status CHECK (llm_status IN ('pending', 'processing', 'completed', 'failed', 'skipped')),
    CONSTRAINT ck_raw_leads_llm_decision CHECK (llm_decision IS NULL OR llm_decision IN ('relevant', 'not_relevant', 'uncertain')),
    CONSTRAINT ck_raw_leads_promotion_status CHECK (promotion_status IN ('not_promoted', 'promoted', 'manually_promoted', 'excluded')),
    CONSTRAINT ck_raw_leads_promotion_source CHECK (promotion_source IS NULL OR promotion_source IN ('llm', 'manual', 'legacy'))
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_raw_leads_promoted_lead'
    ) THEN
        ALTER TABLE raw_leads ADD CONSTRAINT fk_raw_leads_promoted_lead
            FOREIGN KEY (promoted_lead_id) REFERENCES leads (lead_id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_raw_leads_promoted_by'
    ) THEN
        ALTER TABLE raw_leads ADD CONSTRAINT fk_raw_leads_promoted_by
            FOREIGN KEY (promoted_by_user_id) REFERENCES auth_users (id) ON DELETE SET NULL;
    END IF;
END $$;

ALTER TABLE raw_leads
    ADD CONSTRAINT fk_raw_leads_promoted_by
    FOREIGN KEY (promoted_by_user_id) REFERENCES auth_users (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_raw_leads_processing_status ON raw_leads (processing_status);
CREATE INDEX IF NOT EXISTS ix_raw_leads_quality_status ON raw_leads (quality_status);
CREATE INDEX IF NOT EXISTS ix_raw_leads_llm_decision ON raw_leads (llm_decision);
CREATE INDEX IF NOT EXISTS ix_raw_leads_promotion_status ON raw_leads (promotion_status);
CREATE INDEX IF NOT EXISTS ix_raw_leads_source_published ON raw_leads (source, published_at DESC);
CREATE INDEX IF NOT EXISTS ix_raw_leads_canonical_post_id ON raw_leads (canonical_post_id);

ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS raw_lead_id VARCHAR(80),
    ADD COLUMN IF NOT EXISTS promotion_source VARCHAR(20) NOT NULL DEFAULT 'legacy',
    ADD COLUMN IF NOT EXISTS marketing_reviewed_by_user_id VARCHAR(40),
    ADD COLUMN IF NOT EXISTS marketing_reviewed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS marketing_review_note TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_leads_raw_lead_id'
    ) THEN
        ALTER TABLE leads ADD CONSTRAINT uq_leads_raw_lead_id UNIQUE (raw_lead_id);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_leads_raw_lead'
    ) THEN
        ALTER TABLE leads ADD CONSTRAINT fk_leads_raw_lead
            FOREIGN KEY (raw_lead_id) REFERENCES raw_leads (raw_lead_id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_leads_promotion_source'
    ) THEN
        ALTER TABLE leads ADD CONSTRAINT ck_leads_promotion_source
            CHECK (promotion_source IN ('llm', 'manual', 'legacy'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_leads_marketing_reviewer'
    ) THEN
        ALTER TABLE leads ADD CONSTRAINT fk_leads_marketing_reviewer
            FOREIGN KEY (marketing_reviewed_by_user_id) REFERENCES auth_users (id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_leads_marketing_reviewer
    ON leads (marketing_reviewed_by_user_id, marketing_reviewed_at DESC);

CREATE INDEX IF NOT EXISTS ix_leads_promotion_source ON leads (promotion_source);

CREATE TABLE IF NOT EXISTS lead_assignments (
    assignment_id          VARCHAR(80) PRIMARY KEY,
    lead_id                VARCHAR(80) NOT NULL REFERENCES leads (lead_id) ON DELETE CASCADE,
    sales_user_id          VARCHAR(40) NOT NULL REFERENCES auth_users (id) ON DELETE RESTRICT,
    assigned_by_user_id    VARCHAR(40) NOT NULL REFERENCES auth_users (id) ON DELETE RESTRICT,
    assigned_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    unassigned_at          TIMESTAMPTZ,
    unassigned_by_user_id  VARCHAR(40) REFERENCES auth_users (id) ON DELETE SET NULL,
    unassign_reason        TEXT,
    CONSTRAINT ck_assignment_dates CHECK (unassigned_at IS NULL OR unassigned_at >= assigned_at)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_lead_active_assignment
    ON lead_assignments (lead_id)
    WHERE unassigned_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_lead_assignments_sales_user
    ON lead_assignments (sales_user_id, unassigned_at);
CREATE INDEX IF NOT EXISTS ix_lead_assignments_lead_history
    ON lead_assignments (lead_id, assigned_at DESC);

CREATE TABLE IF NOT EXISTS activity_logs (
    activity_id       VARCHAR(80) PRIMARY KEY,
    user_id           VARCHAR(40) REFERENCES auth_users (id) ON DELETE SET NULL,
    action            VARCHAR(40) NOT NULL,
    entity_type       VARCHAR(80),
    entity_id         VARCHAR(120),
    api               TEXT,
    http_method       VARCHAR(10),
    http_status       INTEGER,
    request_id        VARCHAR(100),
    duration_ms       INTEGER,
    ip_address        INET,
    user_agent        TEXT,
    old_value         JSONB,
    new_value         JSONB,
    metadata          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_activity_logs_user_created
    ON activity_logs (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_activity_logs_entity
    ON activity_logs (entity_type, entity_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_activity_logs_api_created
    ON activity_logs (api, created_at DESC);

CREATE TABLE IF NOT EXISTS scrape_run_logs (
    scrape_run_log_id VARCHAR(80) PRIMARY KEY,
    run_id            VARCHAR(80) NOT NULL REFERENCES scrape_runs (run_id) ON DELETE CASCADE,
    level             VARCHAR(12) NOT NULL DEFAULT 'INFO',
    event             VARCHAR(60) NOT NULL,
    message           TEXT,
    metadata          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_scrape_run_logs_level CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR'))
);

CREATE INDEX IF NOT EXISTS ix_scrape_run_logs_run_created
    ON scrape_run_logs (run_id, created_at);
CREATE INDEX IF NOT EXISTS ix_scrape_run_logs_event_created
    ON scrape_run_logs (event, created_at DESC);

-- Backfill current leads as legacy-promoted raw records. No existing lead is deleted.
INSERT INTO raw_leads (
    raw_lead_id, source, source_url, canonical_post_id, author_name,
    author_profile_url, published_at, matched_keyword, content, raw_payload,
    dedup_key, first_seen_at, last_seen_at, processing_status, quality_status,
    quality_flags, spam_label, spam_score, is_spam, llm_status, llm_decision,
    llm_score, llm_confidence, llm_analysis, promotion_status, promotion_source,
    promoted_lead_id, promoted_at, created_at, updated_at
)
SELECT
    'raw_legacy_' || l.lead_id,
    l.source,
    l.source_url,
    l.canonical_post_id,
    l.author_name,
    l.author_profile_url,
    l.published_at,
    l.matched_keyword,
    l.content,
    jsonb_build_object(
        'legacy_lead_id', l.lead_id,
        'source', l.source,
        'source_url', l.source_url,
        'content', l.content
    ),
    'legacy:' || l.lead_id,
    COALESCE(l.created_at, now()),
    COALESCE(l.updated_at, l.created_at, now()),
    CASE WHEN COALESCE(l.quality_flags::text, '') LIKE '%llm_analysis_failed%' THEN 'analysis_failed' ELSE 'analyzed' END,
    'accepted',
    COALESCE(l.quality_flags, '[]'::json),
    COALESCE(l.spam_label, 'unknown'),
    COALESCE(l.spam_score, 0),
    COALESCE(l.is_spam, false),
    CASE WHEN COALESCE(l.quality_flags::text, '') LIKE '%llm_analysis_failed%' THEN 'failed' ELSE 'completed' END,
    CASE WHEN l.is_potential_lead THEN 'relevant' ELSE 'not_relevant' END,
    l.lead_score,
    l.confidence,
    jsonb_build_object(
        'intent', l.intent,
        'industry', l.industry,
        'needs', l.needs,
        'pain_points', l.pain_points,
        'recommended_services', l.recommended_services,
        'evidence', l.evidence,
        'score_breakdown', l.score_breakdown
    ),
    'promoted',
    'legacy',
    l.lead_id,
    COALESCE(l.created_at, now()),
    COALESCE(l.created_at, now()),
    COALESCE(l.updated_at, l.created_at, now())
FROM leads l
ON CONFLICT (dedup_key) DO NOTHING;

UPDATE leads l
SET raw_lead_id = r.raw_lead_id,
    promotion_source = COALESCE(l.promotion_source, 'legacy')
FROM raw_leads r
WHERE r.promoted_lead_id = l.lead_id
  AND l.raw_lead_id IS NULL;

-- Existing records have no trustworthy reviewer identity in the legacy schema;
-- their reviewer fields intentionally remain NULL. New reviews must populate
-- them from the authenticated session.

COMMIT;
