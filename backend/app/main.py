"""SALEP — AI Sales Intelligence Platform.

FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, search, leads, scheduler, web, spse
from app.core.auth import router as auth_router, enforce_access
from app.core.config import settings
from app.core.logging import logger
from app.services.scheduler import lead_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "SALEP starting — env=%s domain=%s url=%s provider=%s model=%s",
        settings.app_env,
        settings.app_domain,
        settings.app_base_url,
        settings.active_llm_provider,
        settings.active_llm_model,
    )
    if not settings.active_llm_key:
        logger.warning(
            "No LLM API key configured (GEMINI_API_KEY, GROQ_API_KEY, OPENAI_API_KEY) — agent qualification will fail"
        )
    else:
        logger.info("LLM configured successfully with provider '%s'", settings.active_llm_provider)

    if not settings.google_sheets_id:
        logger.warning("GOOGLE_SHEETS_ID not set — sheets storage disabled (dry-run mode)")
    else:
        logger.info("Google Sheets configured with ID '%s'", settings.google_sheets_id[:10] + "...")

    # Start automated background lead discovery
    lead_scheduler.start()
    yield
    lead_scheduler.stop()
    logger.info("SALEP shutting down")


app = FastAPI(
    title="SALEP",
    description="AI Sales Intelligence Platform — real-time lead discovery and qualification",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(web.router)
app.include_router(health.router)
app.include_router(search.router)
app.include_router(leads.router)
app.include_router(scheduler.router)
app.include_router(spse.router)
app.include_router(auth_router)
app.middleware('http')(enforce_access)
