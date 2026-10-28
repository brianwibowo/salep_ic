"""Pydantic schemas for SALEP Agent structured output and API models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# --- Intent Taxonomy ---

class IntentType(str, Enum):
    LOOKING_FOR_VENDOR = "looking_for_vendor"
    REQUESTING_RECOMMENDATION = "requesting_recommendation"
    EVALUATING_SOLUTION = "evaluating_solution"
    PROBLEM_IDENTIFICATION = "problem_identification"
    GENERAL_DISCUSSION = "general_discussion"
    LEARNING = "learning"
    JOB_SEEKING = "job_seeking"
    IRRELEVANT = "irrelevant"
    UNKNOWN = "unknown"


HIGH_VALUE_INTENTS = {
    IntentType.LOOKING_FOR_VENDOR,
    IntentType.REQUESTING_RECOMMENDATION,
    IntentType.EVALUATING_SOLUTION,
}


# --- Agent Output Schemas ---

class ProductMatch(BaseModel):
    product_id: str
    product_name: str
    match_score: int = Field(ge=0, le=100)
    reason: str


class ScoreBreakdown(BaseModel):
    intent_score: int = Field(ge=0, le=40, description="Poin kekuatan intent (0-40)")
    intent_max: int = 40
    intent_name: str
    intent_explanation: str

    problem_clarity_score: int = Field(ge=0, le=20, description="Poin kejelasan masalah & kebutuhan (0-20)")
    problem_clarity_max: int = 20
    problem_clarity_explanation: str

    it_relevance_score: int = Field(ge=0, le=20, description="Poin relevansi kebutuhan IT (0-20)")
    it_relevance_max: int = 20
    it_relevance_explanation: str

    product_fit_score: int = Field(ge=0, le=20, description="Poin kesesuaian produk/layanan (0-20)")
    product_fit_max: int = 20
    product_fit_explanation: str

    total_score: int = Field(ge=0, le=100)
    ai_confidence: float = Field(ge=0.0, le=1.0)
    ai_confidence_pct: int
    ai_confidence_explanation: str
    formula_summary: str


class LeadAnalysis(BaseModel):
    is_potential_lead: bool
    intent: IntentType
    industry: str | None = None
    needs: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    recommended_services: list[ProductMatch] = Field(default_factory=list)
    lead_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


# --- Normalized Raw Lead ---

class RawLead(BaseModel):
    source: str
    source_url: str
    author_name: str | None = None
    author_profile_url: str | None = None
    published_at: datetime | None = None
    content: str
    matched_keyword: str
    # Deterministic provenance and quality fields populated by source adapters/gates.
    canonical_post_id: str | None = None
    deterministic_relevance_score: int = Field(default=0, ge=0, le=100)
    deterministic_relevance_label: str = "unreviewed"
    deterministic_relevance_reason: str | None = None
    spam_label: str = "unknown"
    spam_score: int = Field(default=0, ge=0, le=100)
    is_spam: bool = False
    quality_flags: list[str] = Field(default_factory=list)


# --- Full Lead Record (Raw + Analysis) ---

class LeadStatus(str, Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    REJECTED = "rejected"
    CONTACTED = "contacted"


class SalesStatusLog(BaseModel):
    id: str
    from_status: str
    to_status: str
    note: str
    changed_by: str | None = None
    changed_at: datetime


class LeadRecord(BaseModel):
    lead_id: str
    source: str
    source_url: str
    author_name: str | None = None
    author_profile_url: str | None = None
    published_at: datetime | None = None
    matched_keyword: str
    content: str
    is_potential_lead: bool
    intent: IntentType
    industry: str | None = None
    needs: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    recommended_services: list[ProductMatch] = Field(default_factory=list)
    lead_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: LeadStatus = LeadStatus.NEW
    marketing_status: str = Field(default="pending", description="Status kualifikasi marketing: 'pending', 'valid', 'invalid'")
    sales_status: str = Field(default="Belum Dihubungi", description="Status follow-up sales: 'Belum Dihubungi', 'Sedang Dihubungi', 'Closing', 'Batal'")
    sales_status_logs: list["SalesStatusLog"] = Field(default_factory=list)
    score_breakdown: ScoreBreakdown | None = None
    canonical_post_id: str | None = None
    deterministic_relevance_score: int = Field(default=0, ge=0, le=100)
    deterministic_relevance_label: str = "unreviewed"
    deterministic_relevance_reason: str | None = None
    spam_label: str = "unknown"
    spam_score: int = Field(default=0, ge=0, le=100)
    is_spam: bool = False
    quality_flags: list[str] = Field(default_factory=list)
    marketing_reviewed_by_user_id: str | None = None
    marketing_reviewed_by_username: str | None = None
    marketing_reviewed_at: datetime | None = None
    marketing_review_note: str | None = None


class UpdateStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    marketing_status: Literal["pending", "valid", "invalid"]
    expected_version: int = Field(ge=0, description="Versi review terakhir yang ditampilkan kepada Marketing")
    sales_user_id: str | None = Field(default=None, min_length=1, max_length=40)
    review_note: str | None = Field(default=None, max_length=2000, description="Catatan review Marketing (opsional)")

    @field_validator("review_note")
    @classmethod
    def clean_review_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def validate_assignment(self):
        if self.marketing_status == "valid" and not self.sales_user_id:
            raise ValueError("Pilih Sales penanggung jawab untuk lead valid")
        if self.marketing_status != "valid" and self.sales_user_id is not None:
            raise ValueError("Assignment hanya tersedia untuk lead valid")
        return self


class UpdateSalesStatusRequest(BaseModel):
    sales_status: Literal["Belum Dihubungi", "Sedang Dihubungi", "Closing", "Batal"]
    note: str = Field(min_length=1, max_length=2000)

    @field_validator("note")
    @classmethod
    def clean_note(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Catatan tindak lanjut wajib diisi")
        return cleaned


# --- API Request / Response ---

class SearchRequest(BaseModel):
    keywords: list[str] = Field(min_length=1, max_length=10)
    start_date: str
    end_date: str
    sources: list[Literal["threads", "linkedin", "mock"]] = Field(
        min_length=1,
        default_factory=lambda: ["threads", "linkedin"],
        description="Sources to query: 'threads', 'linkedin', or 'mock'",
    )
    limit: int = Field(default=20, ge=1, le=100)


    @field_validator('keywords')
    @classmethod
    def clean_keywords(cls, values):
        cleaned = list(dict.fromkeys(v.strip() for v in values if v.strip()))
        if not cleaned or any(len(v) > 150 for v in cleaned):
            raise ValueError('Masukkan keyword yang valid')
        return cleaned

    @model_validator(mode='after')
    def check_dates(self):
        from datetime import date
        if date.fromisoformat(self.start_date) > date.fromisoformat(self.end_date):
            raise ValueError('Tanggal akhir harus setelah tanggal awal')
        return self


class AnalyzeRequest(BaseModel):
    content: str = Field(min_length=1)


class AnalyzeUrlRequest(BaseModel):
    url: str = Field(min_length=5, description="Full URL to a Threads or LinkedIn post")
    save_to_sheet: bool = Field(default=True, description="Whether to append the qualified lead to Google Sheets")


class SearchResponse(BaseModel):
    query_id: str
    total_found: int
    total_analyzed: int
    qualified: int
    leads: list[LeadRecord]


# --- Product Catalog ---

class Product(BaseModel):
    id: str
    name: str
    description: str
    keywords: list[str]
