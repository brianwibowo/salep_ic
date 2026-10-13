"""Final procurement analytics API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, Request

from app.core.responses import success_response
from app.domain.procurement import FinalReason, ProcurementTrack
from app.services.final_analytics import FinalAnalyticsService, selected_years


router = APIRouter(prefix="/api/v1/inaproc/final", tags=["inaproc-final"])


def _guard(request: Request) -> None:
    if request.state.role not in {"marketing", "sales"}:
        raise HTTPException(status_code=403, detail="Analytics Final hanya tersedia untuk Marketing dan Sales")


def _service() -> FinalAnalyticsService:
    try:
        return FinalAnalyticsService()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Source of truth PostgreSQL belum siap: {exc}") from exc


@router.get("/summary")
async def final_summary(
    request: Request,
    fiscal_years: list[Annotated[int, Query(ge=2000, le=2100)]] | None = Query(default=None),
    reasons: list[FinalReason] | None = Query(default=None),
    tracks: list[ProcurementTrack] | None = Query(default=None),
    categories: list[str] | None = Query(default=None),
    search: str = Query(default="", max_length=200),
) -> dict[str, Any]:
    _guard(request)
    service = _service()
    return success_response(service.summary(fiscal_years=fiscal_years, reasons=reasons, tracks=tracks, categories=categories, search=search), "Ringkasan Final berhasil diambil")


@router.get("")
async def final_records(
    request: Request,
    fiscal_years: list[Annotated[int, Query(ge=2000, le=2100)]] | None = Query(default=None),
    reasons: list[FinalReason] | None = Query(default=None),
    tracks: list[ProcurementTrack] | None = Query(default=None),
    categories: list[str] | None = Query(default=None),
    search: str = Query(default="", max_length=200),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict[str, Any]:
    _guard(request)
    service = _service()
    offset = (page - 1) * limit
    rows, total = service.records(
        fiscal_years=fiscal_years, reasons=reasons, tracks=tracks, categories=categories, search=search,
        limit=limit, offset=offset,
    )
    years = selected_years(fiscal_years)
    return success_response({
        "items": [row.__dict__ for row in rows],
        "filters": {"fiscal_years": years, "reasons": reasons or [], "tracks": tracks or [], "categories": categories or [], "search": search},
        "pagination": {"page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit},
    }, "Data Final berhasil diambil")
