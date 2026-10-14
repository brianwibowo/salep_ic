"""Manual Inaproc synchronization endpoints (Si-RUP + five SPSE tracks)."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.responses import success_response
from app.domain.procurement import ProcurementTrack
from app.services.inaproc_ingestion import InaprocIngestionService
from app.services.sirup_service import SirupService


router = APIRouter(prefix="/api/v1/inaproc", tags=["inaproc"])


def _read_guard(request: Request) -> None:
    if request.state.role not in {"marketing", "sales"}:
        raise HTTPException(status_code=403, detail="Data SiRUP hanya tersedia untuk Marketing dan Sales")


class InaprocSyncRequest(BaseModel):
    fiscal_years: list[int] = Field(min_length=1, max_length=5)
    keyword: str = Field(default="", max_length=200)
    limit: int = Field(default=500, ge=1, le=5000)
    fetch_details: bool = True
    tracks: list[ProcurementTrack] | None = None


@router.get("/sirup")
async def sirup_records(
    request: Request,
    fiscal_year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    search: str = Query(default="", max_length=200),
    procurement_type: str = Query(default="", max_length=120),
    procurement_method: str = Query(default="", max_length=255),
    date_from: date | None = None,
    date_to: date | None = None,
    sort: Literal["newest", "oldest", "budget_desc", "budget_asc"] = "newest",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict[str, Any]:
    _read_guard(request)
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="Tanggal mulai tidak boleh setelah tanggal akhir")
    try:
        data = SirupService().list(
            fiscal_year=fiscal_year,
            search=search,
            procurement_type=procurement_type,
            procurement_method=procurement_method,
            date_from=date_from,
            date_to=date_to,
            sort=sort,
            page=page,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Source of truth PostgreSQL belum siap: {exc}") from exc
    return success_response(data, "Data SiRUP berhasil diambil")


@router.get("/tracks")
async def tracks(request: Request) -> dict[str, Any]:
    if request.state.role not in {"marketing", "sales"}:
        raise HTTPException(status_code=403, detail="Akses khusus user terautentikasi")
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
