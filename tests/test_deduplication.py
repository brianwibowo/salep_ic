"""Tests for deduplication logic."""

import pytest
from datetime import datetime

from app.agent.schemas import RawLead
from app.services.search_service import deduplicate, expand_keywords


def test_deduplicate_same_url():
    """Same source + source_url should be deduplicated."""
    leads = [
        RawLead(
            source="mock",
            source_url="https://example.com/post/123",
            content="Need an inventory app",
            matched_keyword="inventory",
        ),
        RawLead(
            source="mock",
            source_url="https://example.com/post/123",
            content="Need an inventory app",
            matched_keyword="stock management",
        ),
    ]

    result = deduplicate(leads)
    assert len(result) == 1


def test_deduplicate_different_urls():
    """Different URLs should NOT be deduplicated."""
    leads = [
        RawLead(
            source="mock",
            source_url="https://example.com/post/123",
            content="Need an inventory app",
            matched_keyword="inventory",
        ),
        RawLead(
            source="mock",
            source_url="https://example.com/post/456",
            content="Need an ERP system",
            matched_keyword="ERP",
        ),
    ]

    result = deduplicate(leads)
    assert len(result) == 2


def test_deduplicate_different_sources_same_path():
    """Different sources with same URL path are NOT duplicates."""
    leads = [
        RawLead(
            source="source_a",
            source_url="https://example.com/post/123",
            content="Content A",
            matched_keyword="inventory",
        ),
        RawLead(
            source="source_b",
            source_url="https://example.com/post/123",
            content="Content B",
            matched_keyword="inventory",
        ),
    ]

    result = deduplicate(leads)
    assert len(result) == 2


def test_expand_keywords_inventory():
    """Inventory keyword should expand to include synonyms."""
    result = expand_keywords(["butuh aplikasi inventory"])
    assert len(result) > 1
    lower_results = [r.lower() for r in result]
    assert any("stock management" in r for r in lower_results)


def test_expand_keywords_no_match():
    """Keywords without synonym groups should stay as-is."""
    result = expand_keywords(["xyz random keyword"])
    assert result == ["xyz random keyword"]


def test_expand_keywords_managed_service_and_website():
    """Managed service and website keywords should expand properly."""
    result_ms = expand_keywords(["jasa managed service"])
    assert any("IT outsourcing" in r or "NOC" in r for r in result_ms)

    result_web = expand_keywords(["jasa website"])
    assert any("landing page" in r or "company profile web" in r for r in result_web)

    result_cloud = expand_keywords(["butuh cloud server"])
    assert any("AWS" in r or "VPS" in r for r in result_cloud)

