"""One merge policy for scraper writes across SQLite and PostgreSQL."""

from typing import Any


ENRICHMENT_FIELDS = (
    'author_name', 'author_profile_url', 'published_at', 'matched_keyword', 'canonical_post_id',
)
ANALYSIS_FIELDS = (
    'content', 'is_potential_lead', 'intent', 'industry', 'needs', 'pain_points',
    'recommended_services', 'lead_score', 'confidence', 'evidence', 'score_breakdown',
    'analyzed_at', 'deterministic_relevance_score', 'deterministic_relevance_label',
    'deterministic_relevance_reason', 'spam_label', 'spam_score', 'is_spam', 'quality_flags',
)


def scraped_lead_changes(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Replay is a no-op; changed text refreshes its analysis as a unit.

    Scrapers cannot mutate human review, sales progress, notes, first-seen
    timestamps or stable identity. Missing text must not erase valid evidence.
    On replay only fill previously absent provenance fields.
    """
    content = incoming.get('content') or ''
    if not content.strip():
        return {}
    changes = {
        key: incoming[key] for key in ENRICHMENT_FIELDS
        if incoming.get(key) and not existing.get(key)
    }
    if content != existing.get('content'):
        changes.update({key: incoming[key] for key in ANALYSIS_FIELDS if key in incoming})
    return changes
