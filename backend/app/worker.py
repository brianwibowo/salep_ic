"""Dedicated SALEP scheduler worker entry point.

Run this process separately from Uvicorn so horizontal API scaling cannot
duplicate discovery or Inaproc ingestion cycles.
"""

from __future__ import annotations

import asyncio
import signal

from app.core.config import settings
from app.core.logging import logger
from app.services.scheduler import lead_scheduler
from app.services.worker_heartbeat import write_worker_heartbeat


async def worker_main() -> None:
    if settings.process_role not in {"worker", "all"}:
        logger.warning("SALEP worker started with SALEP_PROCESS_ROLE=%s; forcing worker mode", settings.process_role)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(signum, stop_event.set)
        except (NotImplementedError, RuntimeError):
            pass
    lead_scheduler.start()
    write_worker_heartbeat("idle", last_error=None)
    logger.info("SALEP worker ready — scheduler ownership acquired through distributed lock")
    try:
        await stop_event.wait()
    finally:
        lead_scheduler.stop()
        write_worker_heartbeat("stopped")
        logger.info("SALEP worker stopped")


if __name__ == "__main__":
    asyncio.run(worker_main())

