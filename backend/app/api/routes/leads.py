"""Leads endpoint — single lead analysis, direct URL inspection, feed, and RBAC status management."""

from datetime import date
from typing import Any, Literal
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
from app.db.lead_repository import ReviewConflict
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
    sales_user_id: str | None = Query(default=None, min_length=1, max_length=40),
    assignment_status: Literal["all", "assigned", "unassigned"] = Query(default="all"),
    date_from: date | None = Query(default=None, description="Lead created date, inclusive, Asia/Jakarta"),
    date_to: date | None = Query(default=None, description="Lead created date, inclusive, Asia/Jakarta"),
    limit: int = Query(default=50, ge=1, le=100),
) -> ApiResponse[dict[str, Any]]:
    """Retrieve leads based on role access permissions.

    - Tim Sales: strictly filtered to their own assigned, valid leads only.
    - Tim Marketing: view all leads or filter by status.
    """
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "Tanggal mulai tidak boleh melewati tanggal akhir")
    if (date_from and date_from.year < 1900) or (date_to and date_to.year < 1900):
        raise HTTPException(422, "Tahun filter minimal 1900")
    if assignment_status == "unassigned" and (sales_user_id or status not in {"all", "valid"}):
        raise HTTPException(422, "Unassigned hanya untuk lead valid tanpa Sales PIC")
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
            user_id=request.state.user_id,
            sales_user_id=sales_user_id,
            assignment_status=assignment_status,
            date_from=date_from,
            date_to=date_to,
        )
        total = lead_repository.count_leads(
            role=request.state.role,
            sales_status=sales_status,
            source=source,
            status=status,
            search=search,
            user_id=request.state.user_id,
            sales_user_id=sales_user_id,
            assignment_status=assignment_status,
            date_from=date_from,
            date_to=date_to,
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
        stats = lead_repository.get_stats(role=request.state.role, user_id=request.state.user_id)
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
        deleted_urls = lead_repository.get_deleted_source_urls([
            str(lead.get("Link Postingan") or lead.get("source_url") or "") for lead in leads
        ])
        leads = [lead for lead in leads if (lead.get("Link Postingan") or lead.get("source_url")) not in deleted_urls]
        return success_response(leads, "Lead terbaru berhasil diambil")
    except Exception as e:
        logger.error("Failed to fetch recent leads: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve leads: {str(e)}")


@router.get("/leads/sales-users")
def list_assignable_sales(request: Request, include_inactive: bool = False):
    if request.state.role != "marketing":
        raise HTTPException(403, "Akses khusus Marketing")
    return success_response(lead_repository.list_sales_users(include_inactive=include_inactive), "Daftar Sales berhasil diambil")


def require_lead_access(lead: dict | None, request: Request) -> None:
    if not lead:
        raise HTTPException(404, "Lead tidak ditemukan")
    if request.state.role == "sales" and (
        lead["marketing_status"] != "valid"
        or (lead.get("assignment") or {}).get("sales_user_id") != request.state.user_id
    ):
        raise HTTPException(404, "Lead tidak ditemukan")


@router.get("/leads/{lead_id}")
async def get_lead_detail(
    lead_id: str,
    request: Request,
) -> ApiResponse[dict[str, Any]]:
    """Retrieve full details of a specific lead including transparent score breakdown."""
    lead = lead_repository.get_lead(lead_id)
    require_lead_access(lead, request)
    return success_response(lead, "Detail lead berhasil diambil")


@router.delete("/leads/{lead_id}")
async def delete_lead_endpoint(lead_id: str, request: Request) -> ApiResponse[dict[str, bool]]:
    """Soft-delete a lead; retain all Sales progress, assignments, and audit history."""
    if request.state.role != "marketing":
        raise HTTPException(status_code=403, detail="Akses khusus marketing")
    try:
        deleted = lead_repository.delete_lead(
            lead_id, deleted_by_user_id=request.state.user_id,
            api=str(request.url.path), request_id=request.headers.get("x-request-id"),
        )
    except ValueError as exc:
        raise HTTPException(403, str(exc)) from exc
    except Exception as exc:
        logger.error("Failed to soft-delete lead %s: %s", lead_id, exc)
        raise HTTPException(500, "Lead gagal dihapus. Silakan coba lagi.") from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Lead tidak ditemukan")
    return success_response({"deleted": True}, "Lead dihapus dari daftar aktif; riwayat tetap tersimpan")


@router.patch("/leads/{lead_id}/status")
async def update_lead_status(
    lead_id: str,
    payload: UpdateStatusRequest,
    request: Request,
) -> ApiResponse[dict[str, Any]]:
    """Atomically review and assign a lead, rejecting stale form versions.

    When marked 'valid', automatically triggers sync to Google Sheets if configured.
    """
    if request.state.role != "marketing":
        raise HTTPException(403, "Akses khusus Marketing")
    try:
        updated = lead_repository.update_marketing_status(
            lead_id,
            payload.marketing_status,
            reviewed_by_user_id=request.state.user_id,
            expected_version=payload.expected_version,
            sales_user_id=payload.sales_user_id,
            review_note=payload.review_note,
            api=str(request.url.path),
            request_id=request.headers.get("x-request-id"),
        )
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
                        canonical_post_id=lead_data.get("canonical_post_id"),
                        deterministic_relevance_score=lead_data.get("deterministic_relevance_score") or 0,
                        deterministic_relevance_label=lead_data.get("deterministic_relevance_label") or "unreviewed",
                        deterministic_relevance_reason=lead_data.get("deterministic_relevance_reason"),
                        spam_label=lead_data.get("spam_label") or "unknown",
                        spam_score=lead_data.get("spam_score") or 0,
                        is_spam=bool(lead_data.get("is_spam")),
                        quality_flags=lead_data.get("quality_flags") or [],
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
    except ReviewConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update lead status: %s", e)
        raise HTTPException(status_code=500, detail="Review gagal disimpan. Silakan coba lagi.")


@router.patch("/leads/{lead_id}/sales-status")
async def update_sales_status(
    lead_id: str,
    payload: UpdateSalesStatusRequest,
    request: Request,
) -> ApiResponse[dict[str, Any]]:
    """Update sales outreach follow-up status (e.g. Belum Dihubungi, Sedang Dihubungi, Closing, Batal)."""
    lead = lead_repository.get_lead(lead_id)
    require_lead_access(lead, request)
    try:
        updated = lead_repository.update_sales_status(
            lead_id,
            payload.sales_status,
            payload.note,
            request.state.username,
            user_id=request.state.user_id,
        )
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
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("URL analysis failed for '%s': %s", request.url, e)
        raise HTTPException(status_code=500, detail=f"Failed to analyze URL: {str(e)}")
