"""Scoring service — deterministic lead scoring based on agent analysis."""

from app.agent.schemas import LeadAnalysis, IntentType, HIGH_VALUE_INTENTS


# Intent strength scores (0-40)
INTENT_SCORES: dict[IntentType, int] = {
    IntentType.LOOKING_FOR_VENDOR: 40,
    IntentType.REQUESTING_RECOMMENDATION: 35,
    IntentType.EVALUATING_SOLUTION: 30,
    IntentType.PROBLEM_IDENTIFICATION: 20,
    IntentType.GENERAL_DISCUSSION: 10,
    IntentType.LEARNING: 5,
    IntentType.JOB_SEEKING: 0,
    IntentType.IRRELEVANT: 0,
    IntentType.UNKNOWN: 5,
}


def calculate_lead_score(analysis: LeadAnalysis) -> int:
    """Calculate deterministic lead score from AI analysis.

    Scoring dimensions:
      - Intent strength:  0–40
      - Problem clarity:  0–20
      - IT relevance:     0–20
      - Product fit:      0–20
      Total:              0–100

    Returns:
        Score between 0 and 100.
    """
    # Intent strength (0-40)
    intent_score = INTENT_SCORES.get(analysis.intent, 5)

    # Problem clarity (0-20): based on extracted pain points and needs
    needs_count = len(analysis.needs)
    pain_count = len(analysis.pain_points)
    problem_clarity = min(20, (needs_count * 5) + (pain_count * 5))

    # IT relevance (0-20): high-value intents + having needs = IT relevant
    it_relevance = 0
    if analysis.intent in HIGH_VALUE_INTENTS:
        it_relevance = 15
    elif analysis.intent == IntentType.PROBLEM_IDENTIFICATION:
        it_relevance = 10
    elif analysis.intent == IntentType.GENERAL_DISCUSSION:
        it_relevance = 5

    if needs_count > 0:
        it_relevance = min(20, it_relevance + 5)

    # Product fit (0-20): based on recommended services and their match scores
    product_fit = 0
    if analysis.recommended_services:
        avg_match = sum(s.match_score for s in analysis.recommended_services) / len(
            analysis.recommended_services
        )
        product_fit = min(20, int(avg_match * 0.2))

    total = intent_score + problem_clarity + it_relevance + product_fit
    return min(100, max(0, total))
