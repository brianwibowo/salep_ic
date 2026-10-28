"""SPSE public tender discovery endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.spse_service import (
    DEFAULT_SPSE_KEYWORDS,
    discover_spse_tenders,
    get_tender_schedule,
    get_lead_spse_schedule,
)
from app.core.responses import success_response


router = APIRouter(prefix="/api/v1/spse", tags=["spse"])


class SPSESearchRequest(BaseModel):
    keywords: list[str] = Field(default_factory=lambda: DEFAULT_SPSE_KEYWORDS.copy(), min_length=1, max_length=30)
    limit: int = Field(default=30, ge=1, le=100)


@router.get("/defaults")
async def get_defaults(request: Request) -> dict[str, Any]:
    if request.state.role != "marketing":
        raise HTTPException(status_code=403, detail="Modul SPSE hanya untuk Marketing")
    return success_response(
        {"keywords": DEFAULT_SPSE_KEYWORDS, "source": "https://spse.inaproc.id/nasional"},
        "Default pencarian SPSE berhasil diambil",
    )


@router.get("/tender/{tender_id}/jadwal")
async def get_tender_jadwal_endpoint(tender_id: str) -> dict[str, Any]:
    """Retrieve full SPSE tender schedule and active stage progress."""
    try:
        schedule = await get_tender_schedule(tender_id)
        return success_response(schedule, "Jadwal lelang SPSE berhasil diambil")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gagal mengambil jadwal tender dari SPSE: {exc}") from exc


@router.get("/leads/{lead_id}/jadwal")
async def get_lead_jadwal_endpoint(lead_id: str, request: Request) -> dict[str, Any]:
    """Retrieve SPSE tender schedule for a specific lead."""
    from app.api.routes.leads import lead_repository, require_lead_access
    require_lead_access(lead_repository.get_lead(lead_id), request)
    try:
        schedule = await get_lead_spse_schedule(lead_id)
        return success_response(schedule, "Jadwal lelang lead SPSE berhasil diambil")
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve)) from ve
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gagal mengambil jadwal lead dari SPSE: {exc}") from exc


@router.post("/search")
async def search_spse(payload: SPSESearchRequest, request: Request) -> dict[str, Any]:
    if request.state.role != "marketing":
        raise HTTPException(status_code=403, detail="Pencarian SPSE hanya untuk Marketing")
    keywords = list(dict.fromkeys(k.strip() for k in payload.keywords if k.strip()))
    if not keywords:
        raise HTTPException(status_code=422, detail="Masukkan minimal satu keyword")
    try:
        result = await discover_spse_tenders(keywords, payload.limit)
        return success_response(
            {
                "matched": result["matched"],
                "saved": result["saved"],
                "source": "https://spse.inaproc.id/nasional",
            },
            "Pencarian SPSE berhasil",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Pengambilan data SPSE gagal: {exc}") from exc
