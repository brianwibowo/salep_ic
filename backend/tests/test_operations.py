from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

import pytest

from app.core.metrics import MetricsRegistry
from app.core.resilience import CircuitBreaker, CircuitOpenError, call_with_resilience
from app.services.distributed_lock import DistributedLock
from app.api.routes import metrics as metrics_route


def test_file_distributed_lock_is_non_reentrant_across_instances(tmp_path: Path):
    first = DistributedLock(name="test", path=str(tmp_path / "scheduler.lock"))
    second = DistributedLock(name="test", path=str(tmp_path / "scheduler.lock"))
    assert first.try_acquire() is True
    try:
        assert second.try_acquire() is False
    finally:
        first.release()
    assert second.try_acquire() is True
    second.release()


@pytest.mark.asyncio
async def test_retry_and_circuit_breaker_retries_transient_failure():
    calls = 0
    breaker = CircuitBreaker(name="test", failure_threshold=3, recovery_seconds=1)

    async def operation():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("temporary timeout")
        return "ok"

    assert await call_with_resilience(operation, circuit=breaker, operation_name="test", base_delay_seconds=0.001) == "ok"
    assert calls == 2
    assert breaker.state == "closed"


@pytest.mark.asyncio
async def test_open_circuit_rejects_new_call():
    breaker = CircuitBreaker(name="test-open", failure_threshold=1, recovery_seconds=60)

    async def failing():
        raise TimeoutError("down")

    with pytest.raises(TimeoutError):
        await call_with_resilience(failing, circuit=breaker, operation_name="test-open", max_attempts=1)
    with pytest.raises(CircuitOpenError):
        await call_with_resilience(failing, circuit=breaker, operation_name="test-open", max_attempts=1)


def test_metrics_render_prometheus_text():
    registry = MetricsRegistry()
    registry.inc("test_requests", labels={"outcome": "ok"})
    registry.set_gauge("test_ready", 1)
    rendered = registry.render()
    assert 'test_requests_total{outcome="ok"} 1' in rendered
    assert "test_ready 1" in rendered


@pytest.mark.asyncio
async def test_metrics_endpoint_renders_worker_heartbeat(monkeypatch):
    monkeypatch.setattr(
        metrics_route,
        "read_worker_heartbeat",
        lambda: {"status": "idle", "updated_at": datetime.now(timezone.utc).isoformat()},
    )
    response = await metrics_route.metrics_endpoint()
    assert response.status_code == 200
    assert 'salep_worker_heartbeat{status="idle"} 1' in response.body.decode()

