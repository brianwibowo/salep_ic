"""Leads endpoint — single lead analysis, direct URL inspection, feed, and RBAC status management."""

from typing import Any
from fastapi import APIRouter, HTTPException, Query, Request

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
from app.core.responses import ApiResponse, success_response

router = APIRouter(prefix="/api/v1", tags=["leads"])


@router.get("/leads")
async def get_leads_endpoint(
    request: Request,
    page: int = Query(default=1, ge=1),
    sales_status: str = Query(default="all"),
    source: str = Query(default="all", description="Filter by source, e.g. spse or threads"),
    status: str = Query(default="all", description="Marketing status: 'all', 'valid', 'invalid', 'pending'"),
    search: str = Query(default="", description="Search query filter"),
    limit: int = Query(default=50, ge=1, le=100),
) -> ApiResponse[dict[str, Any]]:
    """Retrieve leads based on role access permissions.

    - Tim Sales: strictly filtered to 'valid' leads only.
    - Tim Marketing: view all leads or filter by status.
    """
    try:
        offset = (page - 1) * limit
        leads = lead_repository.get_leads(
            role=request.state.role,
            offset=offset,
            sales_status=sales_status,
            source=source,
            status=status,
            search=search,
            limit=limit,
        )
        total = lead_repository.count_leads(
            role=request.state.role,
            sales_status=sales_status,
            source=source,
            status=status,
            search=search,
        )
        return success_response(
            {
                "items": leads,
                "pagination": {"page": page, "limit": limit, "total": total},
            },
            "Daftar leads berhasil diambil",
        )
    except Exception as e:
        logger.error("Failed to query leads: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to query leads: {str(e)}")


@router.get("/leads/stats")
async def get_leads_stats(request: Request) -> ApiResponse[dict[str, int]]:
    """Retrieve aggregated lead counts for Marketing and Sales KPI counters."""
    try:
        stats = lead_repository.get_stats()
        if request.state.role == "sales":
            return success_response(
                {k: v for k, v in stats.items() if k.startswith("sales_") or k == "valid"},
                "Statistik leads berhasil diambil",
            )
        return success_response(stats, "Statistik leads berhasil diambil")
    except Exception as e:
        logger.error("Failed to fetch lead stats: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


@router.get("/leads/recent")
async def get_recent_leads(
    limit: int = Query(default=20, ge=1, le=50),
) -> ApiResponse[list[dict[str, Any]]]:
    """Fetch the latest leads directly from the Google Sheet."""
    try:
        leads = await sheets_service.get_recent_leads(limit=limit)
        return success_response(leads, "Lead terbaru berhasil diambil")
    except Exception as e:
        logger.error("Failed to fetch recent leads: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve leads: {str(e)}")


@router.get("/leads/{lead_id}")
async def get_lead_detail(
    lead_id: str,
    request: Request,
) -> ApiResponse[dict[str, Any]]:
    """Retrieve full details of a specific lead including transparent score breakdown."""
    lead = lead_repository.get_lead(lead_id)
    if not lead or (request.state.role == "sales" and lead["marketing_status"] != "valid"):
        raise HTTPException(status_code=404, detail="Lead not found")
    return success_response(lead, "Detail lead berhasil diambil")


@router.patch("/leads/{lead_id}/status")
async def update_lead_status(
    lead_id: str,
    payload: UpdateStatusRequest,
) -> ApiResponse[dict[str, Any]]:
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

        return success_response(updated, "Status marketing lead berhasil diperbarui")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update lead status: %s", e)
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.patch("/leads/{lead_id}/sales-status")
async def update_sales_status(
    lead_id: str,
    payload: UpdateSalesStatusRequest,
) -> ApiResponse[dict[str, Any]]:
    """Update sales outreach follow-up status (e.g. Belum Dihubungi, Sedang Dihubungi, Closing, Batal)."""
    lead = lead_repository.get_lead(lead_id)
    if not lead or lead["marketing_status"] != "valid":
        raise HTTPException(status_code=404, detail="Lead not found")
    try:
        updated = lead_repository.update_sales_status(lead_id, payload.sales_status)
        if not updated:
            raise HTTPException(status_code=404, detail="Lead not found")
        return success_response(updated, "Status sales lead berhasil diperbarui")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update sales status: %s", e)
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.post("/leads/analyze", response_model=ApiResponse[LeadAnalysis])
async def analyze_lead(request: AnalyzeRequest):
    """Analyze a single piece of content with the SALEP Agent."""
    try:
        result = await analyze_single_lead(request.content)
        return success_response(result, "Lead berhasil dianalisis")
    except Exception as e:
        logger.error("Lead analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/leads/analyze-url", response_model=ApiResponse[LeadRecord])
async def analyze_url_endpoint(request: AnalyzeUrlRequest):
    """Extract, analyze with Gemini AI, and optionally save a direct Threads or LinkedIn post URL."""
    try:
        record = await analyze_and_save_url(request.url, save_to_sheet=request.save_to_sheet)
        return success_response(record, "URL lead berhasil dianalisis")
    except Exception as e:
        logger.error("URL analysis failed for '%s': %s", request.url, e)
        raise HTTPException(status_code=500, detail=f"Failed to analyze URL: {str(e)}")
