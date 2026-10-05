"""Lead service — orchestrates the full Search → Agent → Sheets pipeline."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

from app.agent.salep_agent import analyze_lead
from app.agent.schemas import (
    LeadRecord,
    RawLead,
    SearchRequest,
    SearchResponse,
    LeadAnalysis,
    LeadStatus,
)
from app.core.logging import logger
from app.services.scoring_service import calculate_lead_score
from app.services.search_service import expand_keywords, search_sources, deduplicate
from app.services.google_sheets import sheets_service


def build_lead_record(raw: RawLead, analysis: LeadAnalysis) -> LeadRecord:
    """Combine raw lead data with AI analysis into a full LeadRecord."""
    app_score = calculate_lead_score(analysis)

    return LeadRecord(
        lead_id=f"lead_{uuid.uuid4().hex[:12]}",
        source=raw.source,
        source_url=raw.source_url,
        author_name=raw.author_name,
        author_profile_url=raw.author_profile_url,
        published_at=raw.published_at,
        matched_keyword=raw.matched_keyword,
        content=raw.content,
        is_potential_lead=analysis.is_potential_lead,
        intent=analysis.intent,
        industry=analysis.industry,
        needs=analysis.needs,
        pain_points=analysis.pain_points,
        recommended_services=analysis.recommended_services,
        lead_score=app_score,
        confidence=analysis.confidence,
        evidence=analysis.evidence,
        analyzed_at=datetime.utcnow(),
        status=LeadStatus.NEW,
    )


async def run_search(request: SearchRequest) -> SearchResponse:
    """Execute the full SALEP pipeline:
    Keywords → Expand → Search Sources → Deduplicate → AI Analysis → Score → Save → Response.
    """
    query_id = f"qry_{uuid.uuid4().hex[:8]}"
    logger.info("Starting search %s — keywords=%s sources=%s", query_id, request.keywords, request.sources)

    # Step 1: Expand keywords
    expanded = expand_keywords(request.keywords)

    # Step 2: Search sources
    raw_results = await search_sources(
        keywords=expanded,
        start_date=request.start_date,
        end_date=request.end_date,
        sources=request.sources,
        limit=request.limit,
    )
    total_found = len(raw_results)
    logger.info("Search %s found %d raw results", query_id, total_found)

    # Step 3: Deduplicate
    unique_results = deduplicate(raw_results)
    logger.info("Search %s — %d unique results after dedup", query_id, len(unique_results))

    # Step 4: Analyze each lead with SALEP Agent
    leads: list[LeadRecord] = []
    errors = 0

    for i, raw_lead in enumerate(unique_results):
        try:
            if i > 0:
                await asyncio.sleep(2)
            logger.info("Analyzing lead %d/%d", i + 1, len(unique_results))
            analysis = await analyze_lead(raw_lead.content)
            lead_record = build_lead_record(raw_lead, analysis)
            leads.append(lead_record)

        except Exception as e:
            errors += 1
            logger.error("Failed to analyze lead %d: %s", i + 1, e)

    # Step 5: Save to Google Sheets
    qualified = [l for l in leads if l.is_potential_lead]
    saved = await sheets_service.append_leads(qualified)
    logger.info(
        "Search %s complete — analyzed=%d qualified=%d saved=%d errors=%d",
        query_id, len(leads), len(qualified), saved, errors,
    )

    return SearchResponse(
        query_id=query_id,
        total_found=total_found,
        total_analyzed=len(leads),
        qualified=len(qualified),
        leads=leads,
    )


async def analyze_single_lead(content: str) -> LeadAnalysis:
    """Analyze a single piece of content — for development/testing endpoint."""
    return await analyze_lead(content)
