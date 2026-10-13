"""Manual Inaproc synchronization endpoints (Si-RUP + five SPSE tracks)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.responses import success_response
from app.domain.procurement import ProcurementTrack
from app.services.inaproc_ingestion import InaprocIngestionService


router = APIRouter(prefix="/api/v1/inaproc", tags=["inaproc"])


class InaprocSyncRequest(BaseModel):
    fiscal_years: list[int] = Field(min_length=1, max_length=5)
    keyword: str = Field(default="", max_length=200)
    limit: int = Field(default=500, ge=1, le=5000)
    fetch_details: bool = True
    tracks: list[ProcurementTrack] | None = None


@router.get("/tracks")
async def tracks(request: Request) -> dict[str, Any]:
    if request.state.role != "marketing":
        raise HTTPException(status_code=403, detail="Modul Inaproc hanya untuk Marketing")
    return success_response({
        "sirup": "https://sirup.inaproc.id/sirup/caripaketctr/index",
        "spse": {
            track.value: f"https://spse.inaproc.id{path}"
            for track, path in {
                ProcurementTrack.TENDER: "/nasional/lelang",
                ProcurementTrack.NON_TENDER: "/nasional/nontender",
                ProcurementTrack.PENCATATAN_NON_TENDER: "/nasional/pencatatan",
                ProcurementTrack.SWAKELOLA: "/nasional/swakelola",
                ProcurementTrack.DARURAT: "/nasional/darurat",
            }.items()
        },
    }, "Track Inaproc berhasil diambil")


@router.post("/sync")
async def sync(request: InaprocSyncRequest, raw_request: Request) -> dict[str, Any]:
    if raw_request.state.role != "marketing":
        raise HTTPException(status_code=403, detail="Sinkronisasi Inaproc hanya untuk Marketing")
    service = InaprocIngestionService()
    try:
        if request.tracks is None:
            result = await service.sync_all(
                fiscal_years=request.fiscal_years, keyword=request.keyword,
                limit=request.limit, fetch_details=request.fetch_details,
            )
        else:
            result = []
            for year in request.fiscal_years:
                for track in request.tracks:
                    if track is ProcurementTrack.SIRUP:
                        result.append(await service.sync_sirup(fiscal_year=year, keyword=request.keyword, limit=request.limit, fetch_details=request.fetch_details))
                    else:
                        result.append(await service.sync_spse_track(track=track, fiscal_year=year, keyword=request.keyword, limit=request.limit, fetch_details=request.fetch_details))
        return success_response({"results": result}, "Sinkronisasi Inaproc selesai")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Sinkronisasi Inaproc gagal: {exc}") from exc
