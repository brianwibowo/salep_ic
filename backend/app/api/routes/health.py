from fastapi import APIRouter
from app.core.config import settings
from app.core.responses import success_response
from app.services.scheduler import lead_scheduler
from app.services.worker_heartbeat import read_worker_heartbeat
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health")
async def health_check():
    return success_response({
        "status": "ok",
        "app_env": settings.app_env,
        "llm_provider": settings.active_llm_provider,
        "llm_model": settings.active_llm_model,
        "llm_configured": bool(settings.active_llm_key),
        "sheets_configured": bool(settings.google_sheets_id),
        "process_role": settings.process_role,
        "scheduler_enabled": settings.auto_search_enabled,
        "scheduler_running": lead_scheduler.is_running,
        "worker_heartbeat": read_worker_heartbeat(),
    }, "Health check berhasil")


@router.get("/ready")
async def readiness_check():
    """Lightweight readiness probe for the reverse proxy/container runtime."""
    database_ready = True
    if settings.database_url:
        try:
            from sqlalchemy import text
            from app.db.engine import build_engine

            engine = build_engine(settings.database_url)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            engine.dispose()
        except Exception:
            database_ready = False
    heartbeat = read_worker_heartbeat()
    worker_ready = True
    if settings.process_role == "api" and heartbeat:
        try:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(str(heartbeat["updated_at"]))).total_seconds()
            worker_ready = age <= max(600, settings.auto_search_interval_minutes * 120)
        except (KeyError, TypeError, ValueError):
            worker_ready = False
    status = "ready" if database_ready and worker_ready else "degraded"
    return success_response({"status": status, "database_ready": database_ready, "worker_ready": worker_ready}, "Readiness check")
