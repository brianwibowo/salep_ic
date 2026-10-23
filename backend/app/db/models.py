"""SQLAlchemy models for the PostgreSQL source-of-truth migration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON, TypeDecorator


class Base(DeclarativeBase):
    pass


class IPAddressType(TypeDecorator[str]):
    """Use PostgreSQL INET in production and a portable string for SQLite tests."""

    impl = String(64)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(INET())
        return dialect.type_descriptor(String(64))


class LeadModel(Base):
    __tablename__ = "leads"

    lead_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    author_name: Mapped[str | None] = mapped_column(String(255))
    author_profile_url: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    matched_keyword: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_potential_lead: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    intent: Mapped[str] = mapped_column(String(80), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(120))
    needs: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    pain_points: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    recommended_services: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    lead_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evidence: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    score_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    canonical_post_id: Mapped[str | None] = mapped_column(String(255), index=True)
    deterministic_relevance_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deterministic_relevance_label: Mapped[str] = mapped_column(String(40), nullable=False, default="unreviewed")
    deterministic_relevance_reason: Mapped[str | None] = mapped_column(Text)
    spam_label: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown")
    spam_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_spam: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    quality_flags: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    marketing_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    sales_status: Mapped[str] = mapped_column(String(40), nullable=False, default="Belum Dihubungi")
    sales_status_logs: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    notes: Mapped[str | None] = mapped_column(Text)
    marketing_reviewed_by_user_id: Mapped[str | None] = mapped_column(String(40))
    marketing_reviewed_by_username: Mapped[str | None] = mapped_column(String(120))
    marketing_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    marketing_review_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_leads_source_status", "source", "marketing_status"),
        Index("ix_leads_score_time", "lead_score", "analyzed_at"),
    )


class ActivityLogModel(Base):
    """Audit trail for authenticated user and API actions."""

    __tablename__ = "activity_logs"

    activity_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(40), index=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(80))
    entity_id: Mapped[str | None] = mapped_column(String(120))
    api: Mapped[str | None] = mapped_column(Text)
    http_method: Mapped[str | None] = mapped_column(String(10))
    http_status: Mapped[int | None] = mapped_column(Integer)
    request_id: Mapped[str | None] = mapped_column(String(100))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    ip_address: Mapped[str | None] = mapped_column(IPAddressType())
    user_agent: Mapped[str | None] = mapped_column(Text)
    old_value: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_activity_logs_entity", "entity_type", "entity_id", "created_at"),
        Index("ix_activity_logs_api_created", "api", "created_at"),
    )


class SourceDocumentModel(Base):
    __tablename__ = "source_documents"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer)
    access_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    payload_uri: Mapped[str | None] = mapped_column(Text)
    payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(80), nullable=False)
    run_id: Mapped[str | None] = mapped_column(String(80), index=True)

    __table_args__ = (
        UniqueConstraint("source", "action", "source_url", "payload_hash", name="uq_source_snapshot"),
        Index("ix_source_documents_external", "source", "external_id"),
    )


class ProcurementPackageModel(Base):
    __tablename__ = "procurement_packages"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    track: Mapped[str] = mapped_column(String(30), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    rup_id: Mapped[str | None] = mapped_column(String(255))
    tender_id: Mapped[str | None] = mapped_column(String(255))
    package_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    organization: Mapped[str | None] = mapped_column(String(500))
    satker: Mapped[str | None] = mapped_column(String(500))
    location: Mapped[str | None] = mapped_column(String(500))
    procurement_type: Mapped[str | None] = mapped_column(String(120))
    procurement_method: Mapped[str | None] = mapped_column(String(255))
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    budget_amount: Mapped[float | None] = mapped_column(Float)
    hps_amount: Mapped[float | None] = mapped_column(Float)
    contract_type: Mapped[str | None] = mapped_column(String(120))
    local_content_flag: Mapped[bool | None] = mapped_column(Boolean)
    small_business_flag: Mapped[bool | None] = mapped_column(Boolean)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_stage_code: Mapped[str | None] = mapped_column(String(80))
    current_stage_label: Mapped[str | None] = mapped_column(String(255))
    current_contract_status: Mapped[str | None] = mapped_column(String(80))
    raw_snapshot_id: Mapped[str | None] = mapped_column(String(80))

    __table_args__ = (
        UniqueConstraint("source", "track", "external_id", "fiscal_year", name="uq_procurement_package"),
        Index("ix_procurement_final_filter", "fiscal_year", "current_stage_code", "current_contract_status"),
    )


class ProcurementEventModel(Base):
    __tablename__ = "procurement_events"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    package_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    event_code: Mapped[str | None] = mapped_column(String(80))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_snapshot_id: Mapped[str | None] = mapped_column(String(80))


class ScrapeRunModel(Base):
    __tablename__ = "scrape_runs"

    run_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    track: Mapped[str | None] = mapped_column(String(40))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    records_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)


class OpportunityModel(Base):
    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    source_document_id: Mapped[str | None] = mapped_column(String(80))
    package_id: Mapped[str | None] = mapped_column(String(100), index=True)
    social_post_id: Mapped[str | None] = mapped_column(String(255))
    opportunity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    service_category: Mapped[str | None] = mapped_column(String(80))
    is_it_relevant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    relevance_score: Mapped[int | None] = mapped_column(Integer)
    managed_service_fit: Mapped[int | None] = mapped_column(Integer)
    commercial_signal: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[float | None] = mapped_column(Float)
    marketing_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    sales_status: Mapped[str | None] = mapped_column(String(40))
    review_reason: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    last_classified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    classifier_version: Mapped[str | None] = mapped_column(String(80))


class LLMAnalysisCacheModel(Base):
    """Persistent cache for deterministic replay of successful LLM analyses."""

    __tablename__ = "llm_analysis_cache"

    cache_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False)
    response: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("content_hash", "model_name", "prompt_version", name="uq_llm_cache_content_model_prompt"),
    )

