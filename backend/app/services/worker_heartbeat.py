"""File-backed worker heartbeat shared by the API and dedicated worker."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings


def heartbeat_path() -> Path:
    lock_path = Path(settings.scheduler_lock_path)
    return lock_path.parent / "worker-heartbeat.json"


def write_worker_heartbeat(status: str, **details: Any) -> None:
    path = heartbeat_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        **details,
    }
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def read_worker_heartbeat() -> dict[str, Any] | None:
    try:
        return json.loads(heartbeat_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None

