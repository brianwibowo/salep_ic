"""Automated Background Scheduler — runs continuous lead discovery cycles."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.agent.schemas import SearchRequest
from app.core.config import settings
from app.core.logging import logger
from app.core.metrics import metrics
from app.services.alerting import alert_manager
from app.services.distributed_lock import DistributedLock
from app.services.lead_service import run_search
from app.services.worker_heartbeat import read_worker_heartbeat, write_worker_heartbeat


class LeadScheduler:
    """Manages periodic autonomous searches across social sources."""

    def __init__(self) -> None:
        self._cycle_lock = asyncio.Lock()
        self.is_running: bool = False
        self._task: asyncio.Task | None = None
        self.last_run_at: datetime | None = None
        self.next_run_at: datetime | None = None
        self.total_runs: int = 0
        self.total_leads_found: int = 0
        self.total_leads_qualified: int = 0
        self.last_error: str | None = None
        self._keyword_cursor: int = 0

    def start(self) -> None:
        """Start the background scheduler task."""
        if not settings.auto_search_enabled:
            logger.info("AutoScheduler is disabled in configuration (AUTO_SEARCH_ENABLED=false)")
            return

        if self.is_running:
            logger.warning("AutoScheduler is already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info(
            "AutoScheduler started — interval=%d minutes, sources=%s",
            settings.auto_search_interval_minutes,
            settings.auto_search_sources,
        )

    def stop(self) -> None:
        """Stop the background scheduler task."""
        self.is_running = False
        self.next_run_at = None
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("AutoScheduler stopped")

    async def _scheduler_loop(self) -> None:
        """Internal infinite loop with interval sleep."""
        # Wait one interval before the first scheduled run.
        logger.info("AutoScheduler waiting configured interval before initial cycle...")
        self.next_run_at = datetime.now(timezone.utc) + timedelta(minutes=settings.auto_search_interval_minutes)
        await asyncio.sleep(settings.auto_search_interval_minutes * 60)

        while self.is_running:
            cycle_started = datetime.now(timezone.utc)
            try:
                await self.run_cycle(trigger_type="scheduled")
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.last_error = str(e)
                logger.error("AutoScheduler cycle failed: %s", e)

            interval_seconds = max(300, settings.auto_search_interval_minutes * 60)
            self.next_run_at = cycle_started + timedelta(seconds=interval_seconds)
            logger.info("AutoScheduler next run scheduled at: %s UTC", self.next_run_at.isoformat())

            try:
                await asyncio.sleep(max(0, (self.next_run_at - datetime.now(timezone.utc)).total_seconds()))
            except asyncio.CancelledError:
                break

    async def run_cycle(self, trigger_type: str = "manual") -> dict[str, Any]:
        if self._cycle_lock.locked():
            metrics.inc("salep_scheduler_cycles_total", labels={"outcome": "busy"})
            return {"status": "busy"}
        async with self._cycle_lock:
            distributed_lock = DistributedLock()
            if not distributed_lock.try_acquire():
                metrics.inc("salep_scheduler_cycles_total", labels={"outcome": "locked"})
                write_worker_heartbeat("locked", last_error="another_worker_holds_lock")
                return {"status": "locked", "message": "Scheduler cycle is owned by another worker."}
            try:
                started = datetime.now(timezone.utc)
                write_worker_heartbeat("running", trigger=trigger_type)
                result = await self._run_cycle(trigger_type)
                metrics.inc("salep_scheduler_cycles_total", labels={"outcome": "success", "trigger": trigger_type})
                metrics.observe("salep_scheduler_cycle_duration_seconds", (datetime.now(timezone.utc) - started).total_seconds())
                write_worker_heartbeat("idle", last_run_at=self.last_run_at.isoformat() if self.last_run_at else None, last_error=None)
                return result
            except Exception as exc:
                self.last_error = str(exc)
                metrics.inc("salep_scheduler_cycles_total", labels={"outcome": "error", "trigger": trigger_type})
                write_worker_heartbeat("error", last_error=self.last_error)
                await alert_manager.notify("scheduler_cycle_failed", f"trigger={trigger_type}: {exc}")
                raise
            finally:
                distributed_lock.release()

    async def _run_cycle(self, trigger_type: str = "manual") -> dict[str, Any]:
        """Execute a single autonomous discovery cycle with rotated keywords."""
        self._reload_shared_discovery_config()
        logger.info("[AutoScheduler] Starting discovery cycle (trigger=%s)...", trigger_type)
        self.last_run_at = datetime.now(timezone.utc)
        self.total_runs += 1
        metrics.set_gauge("salep_scheduler_last_run_timestamp", self.last_run_at.timestamp())

        all_keywords = [k.strip() for k in settings.auto_search_keywords.split(",") if k.strip()]
        sources = [s.strip() for s in settings.auto_search_sources.split(",") if s.strip()]

        if not all_keywords:
            all_keywords = ["rekomendasi hosting", "cari managed service", "butuh software", "rekomendasi vendor IT"]
        if not sources:
            sources = ["threads", "linkedin"]

        # Rotate keywords so different prospect intents are covered each cycle
        num_kw = len(all_keywords)
        idx = self._keyword_cursor % num_kw
        cycle_keywords = list(dict.fromkeys([all_keywords[idx], all_keywords[(idx + 1) % num_kw]]))
        self._keyword_cursor = (idx + 2) % num_kw

        logger.info(
            "[AutoScheduler] Cycle keywords chosen: %s (from pool of %d)",
            cycle_keywords,
            num_kw,
        )

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d")

        request = SearchRequest(
            keywords=cycle_keywords,
            start_date=three_days_ago,
            end_date=today,
            sources=sources,
            limit=settings.auto_search_limit_per_run,
        )

        response = await run_search(request)

        self.total_leads_found += response.total_found
        self.total_leads_qualified += response.qualified
        self.last_error = None

        # Procurement ingestion shares this 30-minute heartbeat but is only
        # activated when PostgreSQL is configured. A portal outage must not
        # make the social discovery cycle fail.
        inaproc_result: list[dict[str, Any]] = []
        if settings.inaproc_auto_sync_enabled and settings.database_url:
            try:
                from app.services.inaproc_ingestion import InaprocIngestionService

                current_year = datetime.now(timezone.utc).year
                inaproc_result = await InaprocIngestionService().sync_all(
                    fiscal_years=[current_year, current_year - 1],
                    limit=settings.inaproc_sync_limit,
                    fetch_details=True,
                )
            except Exception as exc:
                logger.warning("[AutoScheduler] Inaproc sync failed; social cycle retained: %s", exc)
                await alert_manager.notify("inaproc_sync_failed", str(exc), severity="warning")

        logger.info(
            "[AutoScheduler] Cycle complete: found=%d analyzed=%d qualified=%d (saved to Sheets)",
            response.total_found,
            response.total_analyzed,
            response.qualified,
        )

        return {
            "trigger": trigger_type,
            "query_id": response.query_id,
            "total_found": response.total_found,
            "total_analyzed": response.total_analyzed,
            "qualified": response.qualified,
            "inaproc": inaproc_result,
            "leads": response.leads,
        }

    @staticmethod
    def _reload_shared_discovery_config() -> None:
        """Reload the API-edited discovery config in the dedicated worker."""
        path = Path(__file__).resolve().parents[3] / "data" / "discovery.json"
        try:
            if not path.exists():
                return
            payload = json.loads(path.read_text(encoding="utf-8"))
            keywords = [str(value).strip() for value in payload.get("keywords", []) if str(value).strip()]
            sources = [str(value).strip() for value in payload.get("sources", []) if str(value).strip()]
            if keywords:
                settings.auto_search_keywords = ",".join(keywords)
            if sources:
                settings.auto_search_sources = ",".join(sources)
            if payload.get("limit_per_run"):
                settings.auto_search_limit_per_run = int(payload["limit_per_run"])
        except Exception as exc:
            logger.warning("Could not reload shared discovery config %s: %s", path, exc)

    def get_status(self) -> dict[str, Any]:
        """Return current status of the autonomous background scheduler."""
        return {
            "cycle_running": self._cycle_lock.locked(),
            "enabled": settings.auto_search_enabled,
            "is_running": self.is_running,
            "interval_minutes": settings.auto_search_interval_minutes,
            "sources": settings.auto_search_sources.split(","),
            "keywords": [k.strip() for k in settings.auto_search_keywords.split(",") if k.strip()],
            "limit_per_run": settings.auto_search_limit_per_run,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "total_cycles_executed": self.total_runs,
            "total_leads_found": self.total_leads_found,
            "total_leads_qualified": self.total_leads_qualified,
            "last_error": self.last_error,
            "worker_heartbeat": read_worker_heartbeat(),
        }


# Global singleton scheduler
lead_scheduler = LeadScheduler()
