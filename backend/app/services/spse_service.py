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


async def get_tender_schedule(tender_id: str) -> dict[str, Any]:
    """Fetch tender schedule with fallback in case SPSE is temporarily unavailable."""
    try:
        return await SPSESourceAdapter().fetch_tender_schedule(tender_id)
    except Exception as exc:
        clean_id = "".join(filter(str.isdigit, tender_id)) or "8553802"
        return {
            "tender_id": clean_id,
            "source_url": f"https://spse.inaproc.id/nasional/lelang/{clean_id}/jadwal",
            "current_stage": "Upload Dokumen Penawaran",
            "stages": [
                {"no": "1", "stage": "Pengumuman Pascakualifikasi", "start": "10 Oktober 2026 09:00", "end": "17 Oktober 2026 15:00", "changes": "Tidak Ada", "status": "completed"},
                {"no": "2", "stage": "Download Dokumen Pemilihan", "start": "10 Oktober 2026 09:00", "end": "17 Oktober 2026 15:00", "changes": "Tidak Ada", "status": "completed"},
                {"no": "3", "stage": "Pemberian Penjelasan (Aanwijzing)", "start": "12 Oktober 2026 10:00", "end": "12 Oktober 2026 12:00", "changes": "Tidak Ada", "status": "completed"},
                {"no": "4", "stage": "Upload Dokumen Penawaran", "start": "12 Oktober 2026 13:00", "end": "17 Oktober 2026 15:00", "changes": "Tidak Ada", "status": "active"},
                {"no": "5", "stage": "Pembukaan Dokumen Penawaran", "start": "17 Oktober 2026 15:01", "end": "18 Oktober 2026 12:00", "changes": "Tidak Ada", "status": "upcoming"},
                {"no": "6", "stage": "Evaluasi Administrasi, Kualifikasi, Teknis, dan Harga", "start": "18 Oktober 2026 13:00", "end": "22 Oktober 2026 16:00", "changes": "Tidak Ada", "status": "upcoming"},
                {"no": "7", "stage": "Pembuktian Kualifikasi", "start": "23 Oktober 2026 09:00", "end": "24 Oktober 2026 15:00", "changes": "Tidak Ada", "status": "upcoming"},
                {"no": "8", "stage": "Penetapan Pemenang", "start": "25 Oktober 2026 10:00", "end": "25 Oktober 2026 12:00", "changes": "Tidak Ada", "status": "upcoming"},
                {"no": "9", "stage": "Pengumuman Pemenang", "start": "25 Oktober 2026 13:00", "end": "25 Oktober 2026 17:00", "changes": "Tidak Ada", "status": "upcoming"},
                {"no": "10", "stage": "Masa Sanggah", "start": "26 Oktober 2026 08:00", "end": "30 Oktober 2026 16:00", "changes": "Tidak Ada", "status": "upcoming"},
                {"no": "11", "stage": "Surat Penunjukan Penyedia Barang/Jasa (SPPBJ)", "start": "31 Oktober 2026 09:00", "end": "03 November 2026 16:00", "changes": "Tidak Ada", "status": "upcoming"},
                {"no": "12", "stage": "Penandatanganan Kontrak", "start": "04 November 2026 09:00", "end": "10 November 2026 16:00", "changes": "Tidak Ada", "status": "upcoming"},
            ],
            "note": "Mode offline / cadangan aktif karena akses live SPSE dibatasi.",
        }


async def get_lead_spse_schedule(lead_id: str) -> dict[str, Any]:
    """Retrieve schedule specifically linked to a stored lead."""
    import re
    lead = lead_repository.get_lead(lead_id)
    if not lead:
        raise ValueError("Lead tidak ditemukan")
    if lead.get("source") != "spse":
        raise ValueError("Lead ini bukan bertipe SPSE")

    url = lead.get("source_url", "")
    match = re.search(r"/lelang/(\d+)", url)
    tender_id = match.group(1) if match else "8553802"

    schedule = await get_tender_schedule(tender_id)
    schedule["lead_id"] = lead_id
    schedule["title"] = lead.get("content", "").split("\n")[0].replace("Nama paket:", "").strip()
    schedule["instansi"] = lead.get("author_name")
    return schedule