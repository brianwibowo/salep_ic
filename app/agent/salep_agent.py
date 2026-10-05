"""SALEP Agent — core AI agent for lead analysis with multi-model fallback."""

from __future__ import annotations

import asyncio
from agents import (
    Agent,
    Runner,
    set_default_openai_client,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)

from app.agent.instructions import SALEP_AGENT_INSTRUCTIONS
from app.agent.schemas import LeadAnalysis
from app.agent.tools import search_products, get_product
from app.core.config import settings
from app.core.logging import logger

_agent_cache: dict[str, Agent] = {}


def _create_agent_for_model(model_name: str) -> Agent:
    set_tracing_disabled(True)
    api_key = settings.active_llm_key or "no-key-set"
    base_url = settings.active_llm_base_url

    client = AsyncOpenAI(api_key=api_key, base_url=base_url, max_retries=3)
    set_default_openai_client(client)

    if base_url:
        agent_model = OpenAIChatCompletionsModel(model=model_name, openai_client=client)
    else:
        agent_model = model_name

    logger.info(
        "SALEP Agent initialized with model: %s (provider=%s)",
        model_name,
        settings.active_llm_provider,
    )

    return Agent(
        name="SALEP Agent",
        instructions=SALEP_AGENT_INSTRUCTIONS,
        tools=[search_products, get_product],
        output_type=LeadAnalysis,
        model=agent_model,
    )


def _get_agent(model_name: str) -> Agent:
    if model_name not in _agent_cache:
        _agent_cache[model_name] = _create_agent_for_model(model_name)
    return _agent_cache[model_name]


async def analyze_lead(content: str) -> LeadAnalysis:
    """Analyze a single piece of prospect content using the SALEP Agent.
    
    Supports automatic fallback across active models (e.g. Gemini 3.6 Flash,
    3.5 Flash Lite, 3.7 Flash) if rate limits or quota boundaries are encountered.
    """
    primary_model = settings.active_llm_model or "gemini-3.6-flash"
    fallback_pool = [
        primary_model,
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.7-flash",
    ]
    models_to_try = list(dict.fromkeys(fallback_pool))

    last_error: Exception | None = None
    for model_name in models_to_try:
        try:
            agent = _get_agent(model_name)
            logger.info("Analyzing lead (%d chars) using %s", len(content), model_name)

            result = await Runner.run(agent, content)
            analysis: LeadAnalysis = result.final_output

            logger.info(
                "Analysis complete [%s] — is_lead=%s intent=%s score=%d confidence=%.2f",
                model_name,
                analysis.is_potential_lead,
                analysis.intent.value,
                analysis.lead_score,
                analysis.confidence,
            )
            return analysis

        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "Quota exceeded" in err_msg:
                logger.warning(
                    "Model %s hit rate/quota limit. Falling back to next available model...",
                    model_name,
                )
                last_error = e
                await asyncio.sleep(2)
                continue
            logger.error("Non-quota error analyzing lead with %s: %s", model_name, e)
            raise e

    if last_error:
        raise last_error
    raise RuntimeError("No LLM models available to analyze lead")
