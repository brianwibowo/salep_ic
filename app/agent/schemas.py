"""Pydantic schemas for SALEP Agent structured output and API models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


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


# --- Full Lead Record (Raw + Analysis) ---

class LeadStatus(str, Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    REJECTED = "rejected"
    CONTACTED = "contacted"


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
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    status: LeadStatus = LeadStatus.NEW
    marketing_status: str = Field(default="pending", description="Status kualifikasi marketing: 'pending', 'valid', 'invalid'")
    sales_status: str = Field(default="Belum Dihubungi", description="Status follow-up sales: 'Belum Dihubungi', 'Sedang Dihubungi', 'Closing', 'Batal'")
    score_breakdown: ScoreBreakdown | None = None


class UpdateStatusRequest(BaseModel):
    marketing_status: str = Field(description="Status kualifikasi marketing: 'valid', 'invalid', 'pending'")


class UpdateSalesStatusRequest(BaseModel):
    sales_status: str = Field(description="Status follow up sales")


# --- API Request / Response ---

class SearchRequest(BaseModel):
    keywords: list[str] = Field(min_length=1)
    start_date: str
    end_date: str
    sources: list[str] = Field(
        default_factory=lambda: ["threads", "linkedin"],
        description="Sources to query: 'threads', 'linkedin', or 'mock'",
    )
    limit: int = Field(default=20, ge=1, le=100)


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
