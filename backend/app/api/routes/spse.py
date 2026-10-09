"""SPSE public tender discovery endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.spse_service import DEFAULT_SPSE_KEYWORDS, discover_spse_tenders
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
