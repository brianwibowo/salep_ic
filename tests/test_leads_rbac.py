"""Tests for LeadRepository, ScoreBreakdown transparency, and RBAC endpoints."""

import pytest
from app.services.lead_repository import LeadRepository
from app.services.scoring_service import calculate_score_breakdown
from app.agent.schemas import LeadAnalysis, IntentType, ProductMatch


@pytest.fixture
def lead_repository(tmp_path):
    return LeadRepository(tmp_path / "leads.db")


def test_score_breakdown_transparency():
    """Verify that score breakdown provides exact numbers, reasons, and sums up correctly."""
    analysis = LeadAnalysis(
        is_potential_lead=True,
        intent=IntentType.LOOKING_FOR_VENDOR,
        industry="retail",
        needs=["website", "pos"],
        pain_points=["manual_stock"],
        recommended_services=[
            ProductMatch(
                product_id="svc-1",
                product_name="Web App",
                match_score=90,
                reason="Match web requirement",
            )
        ],
        lead_score=0,
        confidence=0.92,
        evidence=["butuh vendor website"],
    )

    breakdown = calculate_score_breakdown(analysis)
    assert breakdown.intent_score == 40
    assert breakdown.problem_clarity_score == 15  # 2 needs (10) + 1 pain (5) = 15
    assert breakdown.it_relevance_score == 20
    assert breakdown.product_fit_score == 18  # 90 * 0.2 = 18
    assert breakdown.total_score == 93
    assert "93/100" in breakdown.formula_summary
    assert breakdown.ai_confidence_pct == 92
    assert "Gemini" in breakdown.ai_confidence_explanation


def test_lead_repository_rbac_isolation(lead_repository):
    """Ensure Sales role only receives 'valid' leads, while Marketing can view all."""
    # Ensure seeded data is present
    stats = lead_repository.get_stats()
    assert stats["total"] >= 5
    assert stats["valid"] >= 2

    # Query as Marketing
    marketing_leads = lead_repository.get_leads(role="marketing", status="all")
    assert len(marketing_leads) >= 5

    # Query as Sales
    sales_leads = lead_repository.get_leads(role="sales")
    assert len(sales_leads) >= 2
    # Check that ALL leads returned to Sales are strictly 'valid'
    for lead in sales_leads:
        assert lead["marketing_status"] == "valid"


def test_lead_repository_status_toggle(lead_repository):
    """Marketing toggling status from pending to valid immediately makes it visible to Sales."""
    import uuid
    from datetime import datetime, timezone
    from app.agent.schemas import LeadRecord

    test_id = f"test_{uuid.uuid4().hex[:8]}"
    test_lead = LeadRecord(
        lead_id=test_id,
        source="threads",
        source_url=f"https://www.threads.net/@user/post/{test_id}",
        author_name="Test User",
        content="Butuh jasa pembuatan website custom",
        is_potential_lead=True,
        intent=IntentType.LOOKING_FOR_VENDOR,
        matched_keyword="jasa website",
        lead_score=80,
        confidence=0.9,
        marketing_status="pending",
        sales_status="Belum Dihubungi",
        analyzed_at=datetime.now(timezone.utc),
    )
    lead_repository.save_lead(test_lead, default_status="pending")

    # Verify initially pending and NOT in Sales
    sales_init = lead_repository.get_leads(role="sales")
    assert not any(l["lead_id"] == test_id for l in sales_init)

    # Mark as valid
    updated = lead_repository.update_marketing_status(test_id, "valid")
    assert updated["marketing_status"] == "valid"

    # Now verify Sales can see it
    sales_leads = lead_repository.get_leads(role="sales")
    assert any(l["lead_id"] == test_id for l in sales_leads)

    # Mark as invalid
    updated = lead_repository.update_marketing_status(test_id, "invalid")
    assert updated["marketing_status"] == "invalid"

    # Now verify Sales NO LONGER sees it
    sales_leads_after = lead_repository.get_leads(role="sales")
    assert not any(l["lead_id"] == test_id for l in sales_leads_after)
