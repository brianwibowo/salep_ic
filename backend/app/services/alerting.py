"""Best-effort operational alert delivery with cooldown protection."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.core.metrics import metrics


class AlertManager:
    def __init__(self) -> None:
        self._last_sent: dict[str, float] = {}

    async def notify(self, event: str, message: str, *, severity: str = "error", force: bool = False) -> bool:
        now = time.monotonic()
        last = self._last_sent.get(event, 0.0)
        if not force and now - last < settings.alert_cooldown_seconds:
            metrics.inc("salep_alerts_suppressed_total", labels={"event": event})
            return False
        self._last_sent[event] = now
        payload: dict[str, Any] = {
            "event": event,
            "severity": severity,
            "message": message,
            "service": "salep",
            "environment": settings.app_env,
        }
        metrics.inc("salep_alerts_total", labels={"event": event, "severity": severity})
        if not settings.alert_webhook_url:
            logger.error("ALERT [%s] %s: %s", severity.upper(), event, message)
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(settings.alert_webhook_url, json=payload)
                response.raise_for_status()
            metrics.inc("salep_alert_deliveries_total", labels={"outcome": "success"})
            return True
        except Exception as exc:
            metrics.inc("salep_alert_deliveries_total", labels={"outcome": "error"})
            logger.error("Could not deliver alert %s: %s", event, exc)
            return False


alert_manager = AlertManager()

