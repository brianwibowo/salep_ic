from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from datetime import datetime, timezone

from app.core.config import settings
from app.core.metrics import metrics
from app.services.worker_heartbeat import read_worker_heartbeat

router = APIRouter(tags=["operations"])


@router.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
async def metrics_endpoint() -> PlainTextResponse:
    body = metrics.render()
    heartbeat = read_worker_heartbeat()
    if heartbeat:
        status = str(heartbeat.get("status", "unknown"))
        try:
            heartbeat_at = datetime.fromisoformat(str(heartbeat["updated_at"]))
            age = max(0.0, (datetime.now(timezone.utc) - heartbeat_at).total_seconds())
            body += f"salep_worker_heartbeat_age_seconds {age:g}\n"
            if age > max(600, settings.auto_search_interval_minutes * 120):
                status = "stale"
        except (KeyError, TypeError, ValueError):
            pass
        body += f'salep_worker_heartbeat{{status="{status}"}} 1\n'
        try:
            timestamp = datetime.fromisoformat(str(heartbeat["updated_at"])).timestamp()
            body += f"salep_worker_last_heartbeat_timestamp {timestamp}\n"
        except (KeyError, TypeError, ValueError):
            pass
    else:
        body += 'salep_worker_heartbeat{status="missing"} 0\n'
    return PlainTextResponse(body, media_type="text/plain; version=0.0.4")

