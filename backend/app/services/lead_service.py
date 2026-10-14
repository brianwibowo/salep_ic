"""Lead service — orchestrates the full Search → Agent → Sheets pipeline."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

from app.agent.salep_agent import analyze_lead
from app.agent.schemas import (
    LeadRecord,
    RawLead,
    SearchRequest,
    SearchResponse,
    LeadAnalysis,
    LeadStatus,
    IntentType,
)
from app.core.logging import logger
from app.services.scoring_service import calculate_lead_score, calculate_score_breakdown
from app.services.search_service import expand_keywords, search_sources, deduplicate
from app.services.google_sheets import sheets_service
from app.services.lead_repository import lead_repository
from app.services.threads_quality import apply_threads_quality_gate, canonical_threads_post_id


def build_lead_record(raw: RawLead, analysis: LeadAnalysis) -> LeadRecord:
    """Combine raw lead data with AI analysis into a full LeadRecord with score breakdown."""
    score_breakdown = calculate_score_breakdown(analysis)
    app_score = score_breakdown.total_score

    # Human marketing review is required before exposing any lead to sales.
    initial_status = "pending" if analysis.is_potential_lead else "invalid"

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
        analyzed_at=datetime.now(timezone.utc),
        status=LeadStatus.NEW,
        marketing_status=initial_status,
        sales_status="Belum Dihubungi",
        score_breakdown=score_breakdown,
        canonical_post_id=raw.canonical_post_id,
        deterministic_relevance_score=raw.deterministic_relevance_score,
        deterministic_relevance_label=raw.deterministic_relevance_label,
        deterministic_relevance_reason=raw.deterministic_relevance_reason,
        spam_label=raw.spam_label,
        spam_score=raw.spam_score,
        is_spam=raw.is_spam,
        quality_flags=raw.quality_flags,
    )


def build_raw_only_lead_record(raw: RawLead) -> LeadRecord:
    """Build a reviewable lead when AI analysis is unavailable.

    Keep the scraped evidence and provenance, but do not invent an intent,
    score, or qualification decision. The quality flag lets the UI distinguish
    this record from one that received an AI analysis.
    """
    return LeadRecord(
        lead_id=f"lead_{uuid.uuid4().hex[:12]}",
        source=raw.source,
        source_url=raw.source_url,
        author_name=raw.author_name,
        author_profile_url=raw.author_profile_url,
        published_at=raw.published_at,
        matched_keyword=raw.matched_keyword,
        content=raw.content,
        is_potential_lead=False,
        intent=IntentType.UNKNOWN,
        needs=[],
        pain_points=[],
        recommended_services=[],
        lead_score=0,
        confidence=0.0,
        evidence=[],
        analyzed_at=datetime.now(timezone.utc),
        status=LeadStatus.NEW,
        marketing_status="pending",
        sales_status="Belum Dihubungi",
        score_breakdown=None,
        canonical_post_id=raw.canonical_post_id,
        deterministic_relevance_score=raw.deterministic_relevance_score,
        deterministic_relevance_label=raw.deterministic_relevance_label,
        deterministic_relevance_reason=raw.deterministic_relevance_reason,
        spam_label=raw.spam_label,
        spam_score=raw.spam_score,
        is_spam=raw.is_spam,
        quality_flags=list(dict.fromkeys([*raw.quality_flags, "llm_analysis_failed"])),
    )


async def run_search(request: SearchRequest) -> SearchResponse:
    """Execute the full SALEP pipeline:
    Keywords → Search Sources → Deduplicate → AI Analysis → Score → Save → Response.
    """
    query_id = f"qry_{uuid.uuid4().hex[:8]}"
    logger.info("Starting search %s — keywords=%s sources=%s", query_id, request.keywords, request.sources)

    # Step 1: Use only explicitly selected keywords to keep Apify usage predictable
    expanded = list(dict.fromkeys(k.strip() for k in request.keywords if k.strip()))

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
    analyzed = 0

    for i, raw_lead in enumerate(unique_results):
        try:
            if i > 0:
                await asyncio.sleep(2)
            logger.info("Analyzing lead %d/%d", i + 1, len(unique_results))
            analysis = await analyze_lead(raw_lead.content)
        except Exception as e:
            errors += 1
            logger.warning(
                "AI analysis unavailable for lead %d/%d; preserving raw lead for review: %s",
                i + 1,
                len(unique_results),
                e,
            )
            leads.append(build_raw_only_lead_record(raw_lead))
            continue
        analyzed += 1
        leads.append(build_lead_record(raw_lead, analysis))

    # Step 5: Save all leads to local SQLite repository and sync valid leads to Google Sheets
    for l in leads:
        try:
            lead_repository.save_lead(l)
        except Exception as e:
            logger.error("Failed to save lead %s to repository: %s", l.lead_id, e)

    qualified_leads_for_sales = [
        l for l in leads
        if l.marketing_status == "valid"
    ]
    saved = await sheets_service.append_leads(qualified_leads_for_sales)
    logger.info(
        "Search %s complete — analyzed=%d qualified=%d saved_for_sales=%d errors=%d",
        query_id, analyzed, len(qualified_leads_for_sales), saved, errors,
    )

    return SearchResponse(
        query_id=query_id,
        total_found=total_found,
        total_analyzed=analyzed,
        qualified=sum(l.is_potential_lead for l in leads),
        leads=leads,
    )


async def extract_post_from_url(url: str) -> RawLead:
    """Fetch and extract post content & author from a direct post URL."""
    import re
    import html
    import httpx

    clean_url = url.strip()
    allowed_hosts = {"threads.net", "threads.com", "linkedin.com"}
    def validate_social_url(candidate: str) -> str:
        parsed = urlparse(candidate)
        host = (parsed.hostname or "").casefold().rstrip(".")
        if parsed.scheme != "https" or not any(host == domain or host.endswith(f".{domain}") for domain in allowed_hosts):
            raise ValueError("URL harus merupakan tautan HTTPS Threads atau LinkedIn")
        return host

    host = validate_social_url(clean_url)
    source = "threads" if host.endswith(("threads.net", "threads.com")) else "linkedin"
    headers = {"User-Agent": "facebookexternalhit/1.1"}

    # Follow only a short chain of redirects that remains on the two allowed
    # social domains.  This prevents the URL-analysis endpoint becoming an
    # SSRF proxy while keeping normal www/canonical redirects working.
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
        current_url = clean_url
        for _ in range(3):
            resp = await client.get(current_url, headers=headers)
            if not 300 <= resp.status_code < 400:
                break
            location = resp.headers.get("location")
            if not location:
                break
            current_url = urljoin(current_url, location)
            validate_social_url(current_url)
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
    if raw_lead.source == "threads":
        raw_lead = apply_threads_quality_gate(raw_lead) or raw_lead.model_copy(update={
            "canonical_post_id": canonical_threads_post_id(raw_lead.source_url, content=raw_lead.content, author_name=raw_lead.author_name),
            "deterministic_relevance_label": "manual_review",
            "deterministic_relevance_reason": "direct_url_not_accepted_by_gate",
        })
    try:
        analysis = await analyze_lead(raw_lead.content)
    except Exception as e:
        logger.warning("AI analysis unavailable for direct URL; preserving raw lead for review: %s", e)
        lead_record = build_raw_only_lead_record(raw_lead)
    else:
        lead_record = build_lead_record(raw_lead, analysis)

    try:
        lead_repository.save_lead(lead_record)
    except Exception as e:
        logger.error("Failed to save lead from URL to repository: %s", e)

    if save_to_sheet and lead_record.marketing_status == "valid":
        await sheets_service.append_lead(lead_record)

    return lead_record


async def analyze_single_lead(content: str) -> LeadAnalysis:
    """Analyze a single piece of content — for development/testing endpoint."""
    return await analyze_lead(content)
