"""Leads endpoint — single lead analysis, direct URL inspection, feed, and RBAC status management."""

from typing import Any
from fastapi import APIRouter, HTTPException, Query

from app.agent.schemas import (
    AnalyzeRequest,
    AnalyzeUrlRequest,
    LeadAnalysis,
    LeadRecord,
    UpdateStatusRequest,
    UpdateSalesStatusRequest,
)
from app.services.lead_service import analyze_single_lead, analyze_and_save_url
from app.services.lead_repository import lead_repository
from app.services.google_sheets import sheets_service
from app.core.logging import logger

router = APIRouter(prefix="/api/v1", tags=["leads"])


@router.get("/leads")
async def get_leads_endpoint(
    role: str = Query(default="marketing", description="Role requesting data: 'marketing' or 'sales'"),
    status: str = Query(default="all", description="Marketing status: 'all', 'valid', 'invalid', 'pending'"),
    search: str = Query(default="", description="Search query filter"),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[dict[str, Any]]:
    """Retrieve leads based on role access permissions.

    - Tim Sales: strictly filtered to 'valid' leads only.
    - Tim Marketing: view all leads or filter by status.
    """
    try:
        leads = lead_repository.get_leads(
            role=role,
            status=status,
            search=search,
            limit=limit,
        )
        return leads
    except Exception as e:
        logger.error("Failed to query leads: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to query leads: {str(e)}")


@router.get("/leads/stats")
async def get_leads_stats():
    """Retrieve aggregated lead counts for Marketing and Sales KPI counters."""
    try:
        return lead_repository.get_stats()
    except Exception as e:
        logger.error("Failed to fetch lead stats: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


@router.get("/leads/{lead_id}")
async def get_lead_detail(lead_id: str) -> dict[str, Any]:
    """Retrieve full details of a specific lead including transparent score breakdown."""
    lead = lead_repository.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/leads/{lead_id}/status")
async def update_lead_status(lead_id: str, payload: UpdateStatusRequest) -> dict[str, Any]:
    """Update qualification status (valid / invalid / pending).

    When marked 'valid', automatically triggers sync to Google Sheets if configured.
    """
    try:
        updated = lead_repository.update_marketing_status(lead_id, payload.marketing_status)
        if not updated:
            raise HTTPException(status_code=404, detail="Lead not found")

        # If marketing marked lead as valid, also sync to Google Sheets
        if payload.marketing_status == "valid":
            try:
                # Build minimal LeadRecord for sheet sync
                lead_data = lead_repository.get_lead(lead_id)
                if lead_data:
                    from app.agent.schemas import RawLead, IntentType
                    from app.services.lead_service import build_lead_record

                    raw = RawLead(
                        source=lead_data["source"],
                        source_url=lead_data["source_url"],
                        author_name=lead_data["author_name"],
                        author_profile_url=lead_data["author_profile_url"],
                        content=lead_data["content"],
                        matched_keyword=lead_data.get("matched_keyword") or "manual_qualification",
                    )
                    analysis = LeadAnalysis(
                        is_potential_lead=lead_data["is_potential_lead"],
                        intent=IntentType(lead_data["intent"]) if lead_data.get("intent") in IntentType._value2member_map_ else IntentType.LOOKING_FOR_VENDOR,
                        industry=lead_data.get("industry"),
                        needs=lead_data.get("needs") or [],
                        pain_points=lead_data.get("pain_points") or [],
                        lead_score=lead_data.get("lead_score") or 70,
                        confidence=lead_data.get("confidence") or 0.85,
                        evidence=lead_data.get("evidence") or [],
                    )
                    rec = build_lead_record(raw, analysis)
                    rec.marketing_status = "valid"
                    await sheets_service.append_lead(rec)
            except Exception as se:
                logger.warning("Could not sync validated lead %s to sheets: %s", lead_id, se)

        return updated
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update lead status: %s", e)
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.patch("/leads/{lead_id}/sales-status")
async def update_sales_status(lead_id: str, payload: UpdateSalesStatusRequest) -> dict[str, Any]:
    """Update sales outreach follow-up status (e.g. Belum Dihubungi, Sedang Dihubungi, Closing, Batal)."""
    try:
        updated = lead_repository.update_sales_status(lead_id, payload.sales_status)
        if not updated:
            raise HTTPException(status_code=404, detail="Lead not found")
        return updated
    except Exception as e:
        logger.error("Failed to update sales status: %s", e)
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


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
