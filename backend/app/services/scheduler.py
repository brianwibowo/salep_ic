"""Automated Background Scheduler — runs continuous lead discovery cycles."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from app.agent.schemas import SearchRequest
from app.core.config import settings
from app.core.logging import logger
from app.services.lead_service import run_search


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
            return {"status": "busy"}
        async with self._cycle_lock:
            try:
                return await self._run_cycle(trigger_type)
            except Exception as exc:
                self.last_error = str(exc)
                raise

    async def _run_cycle(self, trigger_type: str = "manual") -> dict[str, Any]:
        """Execute a single autonomous discovery cycle with rotated keywords."""
        logger.info("[AutoScheduler] Starting discovery cycle (trigger=%s)...", trigger_type)
        self.last_run_at = datetime.now(timezone.utc)
        self.total_runs += 1

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
            "leads": response.leads,
        }

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
        }


# Global singleton scheduler
lead_scheduler = LeadScheduler()
