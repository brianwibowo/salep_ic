"""SPSE discovery service: raw public tender listings enter Marketing review."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from app.agent.schemas import IntentType, LeadAnalysis, LeadRecord
from app.services.lead_repository import lead_repository
from app.sources.spse_source import SPSESourceAdapter


DEFAULT_SPSE_KEYWORDS = [
    "software", "aplikasi", "sistem informasi", "teknologi informasi", "jaringan",
    "server", "cloud", "data center", "keamanan siber", "cyber security",
    "komputer", "laptop", "internet", "hosting", "database", "digital",
]


async def discover_spse_tenders(keywords: list[str], limit: int = 50) -> dict[str, Any]:
    """Fetch keyword-matched homepage tenders and persist them as pending raw leads."""
    matches = await SPSESourceAdapter().search(keywords, limit=limit)
    saved = 0
    for raw in matches:
        lead_id = "spse_" + hashlib.sha256(raw.source_url.encode()).hexdigest()[:16]
        analysis = LeadAnalysis(
            is_potential_lead=True,
            intent=IntentType.LOOKING_FOR_VENDOR,
            needs=[raw.matched_keyword],
            lead_score=0,
            confidence=0.0,
            evidence=["Paket ditemukan berdasarkan pencocokan keyword; belum dianalisis AI."],
        )
        record = {
            "lead_id": lead_id,
            "source": raw.source,
            "source_url": raw.source_url,
            "author_name": raw.author_name,
            "author_profile_url": None,
            "published_at": None,
            "matched_keyword": raw.matched_keyword,
            "content": raw.content,
            "is_potential_lead": analysis.is_potential_lead,
            "intent": analysis.intent,
            "industry": None,
            "needs": analysis.needs,
            "pain_points": [],
            "recommended_services": [],
            "lead_score": 0,
            "confidence": 0.0,
            "evidence": analysis.evidence,
            "analyzed_at": datetime.now(timezone.utc),
            "marketing_status": "pending",
            "sales_status": "Belum Dihubungi",
            "score_breakdown": None,
        }
        lead_repository.save_lead(LeadRecord.model_validate(record))
        saved += 1
    return {"matched": len(matches), "saved": saved, "leads": [m.model_dump() for m in matches]}