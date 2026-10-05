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

    # Step 5: Save all analyzed leads to Google Sheets (strictly real sources, exclude mock)
    qualified = [l for l in leads if l.is_potential_lead]
    real_leads_to_save = [l for l in leads if l.source != "mock"]
    saved = await sheets_service.append_leads(real_leads_to_save)
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


async def extract_post_from_url(url: str) -> RawLead:
    """Fetch and extract post content & author from a direct post URL."""
    import re
    import html
    import httpx

    clean_url = url.strip()
    source = "threads" if "threads." in clean_url else ("linkedin" if "linkedin.com" in clean_url else "web")
    headers = {"User-Agent": "facebookexternalhit/1.1"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(clean_url, headers=headers, follow_redirects=True)
        resp_text = resp.text

    desc_match = re.search(r"<meta\s+property=[\"\x27]og:description[\"\x27]\s+content=[\"\x27](.*?)[\"\x27]", resp_text)
    if not desc_match:
        desc_match = re.search(r"<meta\s+name=[\"\x27]description[\"\x27]\s+content=[\"\x27](.*?)[\"\x27]", resp_text)

    title_match = re.search(r"<meta\s+property=[\"\x27]og:title[\"\x27]\s+content=[\"\x27](.*?)[\"\x27]", resp_text)

    desc = html.unescape(desc_match.group(1)) if desc_match else ""
    title = html.unescape(title_match.group(1)) if title_match else ""

    author_name = "User"
    author_username = ""
    author_profile_url = clean_url

    if "threads." in clean_url:
        author_match = re.search(r"^(.*?)\s*\(@([^)]+)\)\s*on\s*Threads", title)
        if author_match:
            author_name = author_match.group(1).strip()
            author_username = author_match.group(2).strip()
            author_profile_url = f"https://www.threads.net/@{author_username}"
        elif title:
            author_name = title
    else:
        if title:
            author_name = title.split("|")[0].split("-")[0].strip()

    content = desc or title or "No description could be extracted"

    return RawLead(
        source=source,
        source_url=clean_url,
        author_name=author_name,
        author_profile_url=author_profile_url,
        content=content,
        matched_keyword="direct_url_input",
    )


async def analyze_and_save_url(url: str, save_to_sheet: bool = True) -> LeadRecord:
    """Analyze a direct post URL using Gemini AI and optionally save to Google Sheets."""
    raw_lead = await extract_post_from_url(url)
    analysis = await analyze_lead(raw_lead.content)
    lead_record = build_lead_record(raw_lead, analysis)

    if save_to_sheet:
        await sheets_service.append_lead(lead_record)

    return lead_record


async def analyze_single_lead(content: str) -> LeadAnalysis:
    """Analyze a single piece of content — for development/testing endpoint."""
    return await analyze_lead(content)
