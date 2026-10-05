"""Leads endpoint — for dev/testing single lead analysis."""

from fastapi import APIRouter, HTTPException

from app.agent.schemas import AnalyzeRequest, LeadAnalysis
from app.services.lead_service import analyze_single_lead
from app.core.logging import logger

router = APIRouter(prefix="/api/v1", tags=["leads"])


@router.post("/leads/analyze", response_model=LeadAnalysis)
async def analyze_lead(request: AnalyzeRequest):
    """Analyze a single piece of content with the SALEP Agent.

    Useful for development and testing — bypasses source search.
    """
    try:
        result = await analyze_single_lead(request.content)
        return result

    except Exception as e:
        logger.error("Lead analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
