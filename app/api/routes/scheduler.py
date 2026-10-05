"""Scheduler control endpoints — inspect and trigger automated lead discovery."""

from fastapi import APIRouter, BackgroundTasks
from app.services.scheduler import lead_scheduler

router = APIRouter(prefix="/api/v1/scheduler", tags=["scheduler"])


@router.get("/status")
async def get_scheduler_status():
    """Get current status of autonomous background lead discovery."""
    return lead_scheduler.get_status()


@router.post("/trigger")
async def trigger_cycle(background_tasks: BackgroundTasks):
    """Trigger an autonomous search cycle immediately in the background."""
    background_tasks.add_task(lead_scheduler.run_cycle, trigger_type="api_trigger")
    return {
        "status": "triggered",
        "message": "Autonomous lead discovery cycle dispatched in background.",
    }


@router.post("/start")
async def start_scheduler():
    """Start the periodic autonomous scheduler."""
    lead_scheduler.start()
    return {"status": "started", "scheduler": lead_scheduler.get_status()}


@router.post("/stop")
async def stop_scheduler():
    """Stop the periodic autonomous scheduler."""
    lead_scheduler.stop()
    return {"status": "stopped", "scheduler": lead_scheduler.get_status()}
