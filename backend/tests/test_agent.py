"""Tests for the SALEP Agent — requires OPENAI_API_KEY to be set."""

import os
import pytest

from app.agent.schemas import LeadAnalysis, IntentType
from app.core.config import settings

pytestmark = pytest.mark.skipif(
    not settings.active_llm_key,
    reason="No LLM API key set (GEMINI_API_KEY, GROQ_API_KEY, OPENAI_API_KEY) — skipping agent tests",
)



@pytest.mark.asyncio
async def test_high_intent_vendor_search():
    """Agent should identify explicit vendor search as a high-intent lead."""
    from app.agent.salep_agent import analyze_lead

    content = "Ada rekomendasi vendor yang bisa bikin aplikasi inventory? Bisnis kami masih menggunakan Excel dan mulai kesulitan tracking stok beberapa gudang."

    result = await analyze_lead(content)

    assert isinstance(result, LeadAnalysis)
    assert result.is_potential_lead is True
    assert result.intent in {
        IntentType.LOOKING_FOR_VENDOR,
        IntentType.REQUESTING_RECOMMENDATION,
    }
    assert len(result.needs) > 0
    assert result.confidence > 0.5


@pytest.mark.asyncio
async def test_irrelevant_content():
    """Agent should identify irrelevant content correctly."""
    import asyncio
    await asyncio.sleep(6)
    from app.agent.salep_agent import analyze_lead

    content = "Jual laptop gaming murah! RTX 4060, RAM 16GB. Harga nego. COD Jakarta."

    result = await analyze_lead(content)

    assert isinstance(result, LeadAnalysis)
    assert result.is_potential_lead is False
    assert result.intent in {IntentType.IRRELEVANT, IntentType.UNKNOWN}


@pytest.mark.asyncio
async def test_learning_not_a_lead():
    """Agent should recognize students/learners are not potential leads."""
    import asyncio
    await asyncio.sleep(6)
    from app.agent.salep_agent import analyze_lead

    content = "Saya sedang belajar membuat aplikasi inventory menggunakan Python. Ada tutorial yang bagus?"

    result = await analyze_lead(content)

    assert isinstance(result, LeadAnalysis)
    assert result.is_potential_lead is False
    assert result.intent == IntentType.LEARNING
