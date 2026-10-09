"""Tests for the scoring service."""

from app.agent.schemas import LeadAnalysis, ProductMatch, IntentType
from app.services.scoring_service import calculate_lead_score


def test_high_intent_high_match():
    """A lead with clear vendor search intent and matching products should score high."""
    analysis = LeadAnalysis(
        is_potential_lead=True,
        intent=IntentType.LOOKING_FOR_VENDOR,
        industry="distribution",
        needs=["inventory_system", "multi_warehouse"],
        pain_points=["excel_limitation", "manual_tracking"],
        recommended_services=[
            ProductMatch(
                product_id="svc-001",
                product_name="Custom Software Development",
                match_score=94,
                reason="Prospect needs an inventory system.",
            )
        ],
        lead_score=0,
        confidence=0.94,
        evidence=["mencari vendor", "aplikasi inventory"],
    )

    score = calculate_lead_score(analysis)
    assert score >= 75, f"Expected high score, got {score}"


def test_low_intent_learning():
    """A learning-oriented post should score low."""
    analysis = LeadAnalysis(
        is_potential_lead=False,
        intent=IntentType.LEARNING,
        industry=None,
        needs=[],
        pain_points=[],
        recommended_services=[],
        lead_score=0,
        confidence=0.8,
        evidence=[],
    )

    score = calculate_lead_score(analysis)
    assert score <= 15, f"Expected low score, got {score}"


def test_irrelevant_scores_zero():
    """Completely irrelevant content should score near zero."""
    analysis = LeadAnalysis(
        is_potential_lead=False,
        intent=IntentType.IRRELEVANT,
        industry=None,
        needs=[],
        pain_points=[],
        recommended_services=[],
        lead_score=0,
        confidence=0.95,
        evidence=[],
    )

    score = calculate_lead_score(analysis)
    assert score == 0, f"Expected zero score, got {score}"


def test_medium_intent_with_needs():
    """Problem identification with clear needs should score medium."""
    analysis = LeadAnalysis(
        is_potential_lead=True,
        intent=IntentType.PROBLEM_IDENTIFICATION,
        industry="food_beverage",
        needs=["pos_system"],
        pain_points=["manual_process"],
        recommended_services=[
            ProductMatch(
                product_id="svc-001",
                product_name="Custom Software Development",
                match_score=70,
                reason="POS system could be custom built.",
            )
        ],
        lead_score=0,
        confidence=0.7,
        evidence=["ingin go digital"],
    )

    score = calculate_lead_score(analysis)
    assert 30 <= score <= 70, f"Expected medium score, got {score}"


def test_job_seeking_scores_zero():
    """Job seeking posts should score zero."""
    analysis = LeadAnalysis(
        is_potential_lead=False,
        intent=IntentType.JOB_SEEKING,
        industry=None,
        needs=[],
        pain_points=[],
        recommended_services=[],
        lead_score=0,
        confidence=0.9,
        evidence=[],
    )

    score = calculate_lead_score(analysis)
    assert score == 0, f"Expected zero, got {score}"
