"""Leads endpoint — single lead analysis, direct URL inspection, and recent leads feed."""

from typing import Any
from fastapi import APIRouter, HTTPException, Query

from app.agent.schemas import AnalyzeRequest, AnalyzeUrlRequest, LeadAnalysis, LeadRecord
from app.services.lead_service import analyze_single_lead, analyze_and_save_url
from app.services.google_sheets import sheets_service
from app.core.logging import logger

router = APIRouter(prefix="/api/v1", tags=["leads"])


@router.post("/leads/analyze", response_model=LeadAnalysis)
async def analyze_lead(request: AnalyzeRequest):
    """Analyze a single piece of content with the SALEP Agent."""
    try:
        result = await analyze_single_lead(request.content)
        return result
    except Exception as e:
        logger.error("Lead analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/leads/analyze-url", response_model=LeadRecord)
async def analyze_url_endpoint(request: AnalyzeUrlRequest):
    """Extract, analyze with Gemini AI, and optionally save a direct Threads or LinkedIn post URL."""
    try:
        record = await analyze_and_save_url(request.url, save_to_sheet=request.save_to_sheet)
        return record
    except Exception as e:
        logger.error("URL analysis failed for '%s': %s", request.url, e)
        raise HTTPException(status_code=500, detail=f"Failed to analyze URL: {str(e)}")


@router.get("/leads/recent")
async def get_recent_leads(limit: int = Query(default=20, ge=1, le=50)) -> list[dict[str, Any]]:
    """Fetch the latest leads directly from the Google Sheet."""
    try:
        leads = await sheets_service.get_recent_leads(limit=limit)
        return leads
    except Exception as e:
        logger.error("Failed to fetch recent leads: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve leads: {str(e)}")
