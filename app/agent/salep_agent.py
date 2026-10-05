"""SALEP Agent — core AI agent for lead analysis."""

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


def _create_agent() -> Agent:
    set_tracing_disabled(True)
    api_key = settings.active_llm_key or "no-key-set"
    base_url = settings.active_llm_base_url
    model_name = settings.active_llm_model

    # Configure client for Agents SDK (supports Gemini, Groq, OpenRouter, Ollama, OpenAI)
    client = AsyncOpenAI(api_key=api_key, base_url=base_url, max_retries=5)
    set_default_openai_client(client)

    if base_url:
        agent_model = OpenAIChatCompletionsModel(model=model_name, openai_client=client)
    else:
        agent_model = model_name

    logger.info(
        "SALEP Agent initialized with LLM: provider=%s model=%s base_url=%s",
        settings.active_llm_provider,
        model_name,
        base_url or "default(openai)",
    )

    return Agent(
        name="SALEP Agent",
        instructions=SALEP_AGENT_INSTRUCTIONS,
        tools=[search_products, get_product],
        output_type=LeadAnalysis,
        model=agent_model,
    )


salep_agent = _create_agent()


async def analyze_lead(content: str) -> LeadAnalysis:
    """Analyze a single piece of prospect content using the SALEP Agent.

    Args:
        content: Raw text content from a prospect (post, message, etc.)

    Returns:
        LeadAnalysis with intent, needs, product matches, and scoring.
    """
    logger.info("Analyzing lead content (%d chars)", len(content))

    result = await Runner.run(salep_agent, content)

    analysis: LeadAnalysis = result.final_output
    logger.info(
        "Analysis complete — is_lead=%s intent=%s score=%d confidence=%.2f",
        analysis.is_potential_lead,
        analysis.intent.value,
        analysis.lead_score,
        analysis.confidence,
    )
    return analysis
