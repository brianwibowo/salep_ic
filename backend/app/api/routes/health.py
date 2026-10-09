from fastapi import APIRouter
from app.core.config import settings
from app.core.responses import success_response

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
    }, "Health check berhasil")
