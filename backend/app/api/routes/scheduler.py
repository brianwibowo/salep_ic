"""Scheduler control endpoints — inspect and trigger automated lead discovery."""

from fastapi import APIRouter, BackgroundTasks
from app.services.scheduler import lead_scheduler
from app.core.responses import success_response

router = APIRouter(prefix="/api/v1/scheduler", tags=["scheduler"])


@router.get("/status")
async def get_scheduler_status():
    """Get current status of autonomous background lead discovery."""
    return success_response(lead_scheduler.get_status(), "Status scheduler berhasil diambil")


@router.post("/trigger")
async def trigger_cycle(background_tasks: BackgroundTasks):
    """Trigger an autonomous search cycle immediately in the background."""
    background_tasks.add_task(lead_scheduler.run_cycle, trigger_type="api_trigger")
    return success_response({
        "status": "triggered",
        "message": "Autonomous lead discovery cycle dispatched in background.",
    }, "Discovery berhasil dijadwalkan")


@router.post("/start")
async def start_scheduler():
    """Start the periodic autonomous scheduler."""
    lead_scheduler.start()
    return success_response(
        {"status": "started", "scheduler": lead_scheduler.get_status()},
        "Scheduler berhasil dijalankan",
    )


@router.post("/stop")
async def stop_scheduler():
    """Stop the periodic autonomous scheduler."""
    lead_scheduler.stop()
    return success_response(
        {"status": "stopped", "scheduler": lead_scheduler.get_status()},
        "Scheduler berhasil dihentikan",
    )


from typing import Literal
from pydantic import BaseModel, Field, field_validator
from app.core.config import settings
from pathlib import Path
import json

CONFIG_PATH = Path(__file__).resolve().parents[3] / 'data' / 'discovery.json'


class DiscoveryConfig(BaseModel):
    keywords: list[str] = Field(min_length=1, max_length=40)
    sources: list[Literal['threads', 'linkedin']] = Field(min_length=1)
    limit_per_run: int = Field(ge=1, le=50)

    @field_validator('keywords')
    @classmethod
    def clean_keywords(cls, values):
        values = list(dict.fromkeys(v.strip() for v in values if v.strip()))
        if not values or any(len(v) > 150 for v in values):
            raise ValueError('Isi keyword yang valid (maksimal 150 karakter)')
        return values


def apply_config(config):
    settings.auto_search_keywords = ','.join(config.keywords)
    settings.auto_search_sources = ','.join(config.sources)
    settings.auto_search_limit_per_run = config.limit_per_run
    settings.auto_search_interval_minutes = 30


if CONFIG_PATH.exists():
    apply_config(DiscoveryConfig(**json.loads(CONFIG_PATH.read_text())))


@router.put('/config')
async def save_config(config: DiscoveryConfig):
    temp = CONFIG_PATH.with_suffix('.tmp')
    temp.write_text(config.model_dump_json(indent=2))
    temp.replace(CONFIG_PATH)
    apply_config(config)
    return success_response(lead_scheduler.get_status(), "Konfigurasi discovery berhasil disimpan")
