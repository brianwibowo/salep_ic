"""Search endpoint — triggers the full SALEP pipeline."""

from fastapi import APIRouter, HTTPException

from app.agent.schemas import SearchRequest, SearchResponse
from app.services.lead_service import run_search
from app.core.logging import logger
from app.core.responses import ApiResponse, success_response

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.post("/search", response_model=ApiResponse[SearchResponse])
async def search_leads(request: SearchRequest):
    """Execute a real-time search: keywords → source search → AI analysis → results.

    Returns analyzed leads with intent, needs, product matching, and scoring.
    """
    try:
        result = await run_search(request)
        return success_response(result, "Pencarian leads berhasil")

    except Exception as e:
        logger.error("Search failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
