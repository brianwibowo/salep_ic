"""SALEP — AI Sales Intelligence Platform.

FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, search, leads
from app.core.config import settings
from app.core.logging import logger

app = FastAPI(
    title="SALEP",
    description="AI Sales Intelligence Platform — real-time lead discovery and qualification",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(search.router)
app.include_router(leads.router)


@app.on_event("startup")
async def startup():
    logger.info("SALEP starting — env=%s model=%s", settings.app_env, settings.openai_model)
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not set — agent calls will fail")
    if not settings.google_sheets_id:
        logger.warning("GOOGLE_SHEETS_ID not set — sheets storage disabled")


@app.on_event("shutdown")
async def shutdown():
    logger.info("SALEP shutting down")
