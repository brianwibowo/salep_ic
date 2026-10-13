"""Async retry and circuit-breaker primitives used by external source calls."""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

from app.core.config import settings
from app.core.logging import logger
from app.core.metrics import metrics

T = TypeVar("T")


class CircuitOpenError(RuntimeError):
    pass


@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = settings.circuit_failure_threshold
    recovery_seconds: int = settings.circuit_recovery_seconds
    failures: int = 0
    opened_at: float | None = None
    half_open_probe: bool = False

    @property
    def state(self) -> str:
        if self.opened_at is None:
            return "closed"
        if time.monotonic() - self.opened_at >= self.recovery_seconds:
            return "half_open"
        return "open"

    def allow(self) -> bool:
        state = self.state
        if state == "closed":
            return True
        if state == "half_open" and not self.half_open_probe:
            self.half_open_probe = True
            return True
        metrics.inc("salep_circuit_open_total", labels={"circuit": self.name})
        return False

    def success(self) -> None:
        was_open = self.opened_at is not None
        self.failures = 0
        self.opened_at = None
        self.half_open_probe = False
        if was_open:
            metrics.inc("salep_circuit_recovered_total", labels={"circuit": self.name})

    def failure(self) -> None:
        self.failures += 1
        self.half_open_probe = False
        if self.failures >= self.failure_threshold:
            self.opened_at = time.monotonic()
            metrics.inc("salep_circuit_tripped_total", labels={"circuit": self.name})


def is_retryable(exc: Exception) -> bool:
    text = str(exc).casefold()
    if any(token in text for token in ("403", "401", "invalid token", "hard limit exceeded", "quota exceeded")):
        return False
    if any(token in text for token in ("429", "timeout", "timed out", "connection", "temporarily", "502", "503", "504", "unavailable")):
        return True
    try:
        import httpx

        if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
            return True
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500:
            return True
    except ImportError:
        pass
    return False


async def call_with_resilience(
    operation: Callable[[], Awaitable[T]],
    *,
    circuit: CircuitBreaker,
    operation_name: str,
    max_attempts: int | None = None,
    base_delay_seconds: float | None = None,
) -> T:
    attempts = max_attempts or settings.retry_max_attempts
    base_delay = base_delay_seconds or settings.retry_base_delay_seconds
    if not circuit.allow():
        raise CircuitOpenError(f"circuit_open:{circuit.name}")
    for attempt in range(1, attempts + 1):
        started = time.monotonic()
        try:
            result = await operation()
            circuit.success()
            metrics.inc("salep_external_requests_total", labels={"operation": operation_name, "outcome": "success"})
            metrics.observe("salep_external_request_duration_seconds", time.monotonic() - started, {"operation": operation_name})
            return result
        except Exception as exc:
            metrics.inc("salep_external_requests_total", labels={"operation": operation_name, "outcome": "error"})
            circuit.failure()
            if circuit.state == "open":
                from app.services.alerting import alert_manager

                await alert_manager.notify(
                    "source_circuit_open",
                    f"{operation_name} circuit opened after {circuit.failures} failures",
                    severity="critical",
                )
            retry = attempt < attempts and is_retryable(exc) and circuit.state != "open"
            if not retry:
                raise
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, base_delay / 2)
            metrics.inc("salep_external_retries_total", labels={"operation": operation_name})
            logger.warning("%s failed (attempt %d/%d); retrying in %.2fs: %s", operation_name, attempt, attempts, delay, exc)
            await asyncio.sleep(delay)
    raise RuntimeError(f"{operation_name} exhausted retry policy")

