"""Dependency-free Prometheus exposition for SALEP operational signals."""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from collections.abc import Mapping


def _label_key(labels: Mapping[str, object] | None) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(k), str(v)) for k, v in (labels or {}).items()))


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
        self._gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self._histograms: dict[tuple[str, tuple[tuple[str, str], ...]], list[float]] = defaultdict(list)

    def inc(self, name: str, value: float = 1, labels: Mapping[str, object] | None = None) -> None:
        with self._lock:
            self._counters[(name, _label_key(labels))] += value

    def set_gauge(self, name: str, value: float, labels: Mapping[str, object] | None = None) -> None:
        with self._lock:
            self._gauges[(name, _label_key(labels))] = value

    def observe(self, name: str, value: float, labels: Mapping[str, object] | None = None) -> None:
        with self._lock:
            samples = self._histograms[(name, _label_key(labels))]
            samples.append(float(value))
            # Keep memory bounded while retaining useful recent latency data.
            if len(samples) > 1000:
                del samples[: len(samples) - 1000]

    def timer(self, name: str, labels: Mapping[str, object] | None = None):
        registry = self
        started = time.monotonic()

        class _Timer:
            def __enter__(self):
                return self

            def __exit__(self, *_exc):
                registry.observe(name, time.monotonic() - started, labels)

        return _Timer()

    def render(self) -> str:
        lines: list[str] = []
        with self._lock:
            counters = list(self._counters.items())
            gauges = list(self._gauges.items())
            histograms = list(self._histograms.items())
        for (name, labels), value in sorted(counters):
            metric_name = name if name.endswith("_total") else f"{name}_total"
            lines.append(f"{metric_name}{self._format_labels(labels)} {value:g}")
        for (name, labels), value in sorted(gauges):
            lines.append(f"{name}{self._format_labels(labels)} {value:g}")
        for (name, labels), samples in sorted(histograms):
            if not samples:
                continue
            base = self._format_labels(labels)
            lines.append(f"{name}_count{base} {len(samples)}")
            lines.append(f"{name}_sum{base} {sum(samples):g}")
            lines.append(f"{name}_max{base} {max(samples):g}")
        return "\n".join(lines) + ("\n" if lines else "")

    @staticmethod
    def _format_labels(labels: tuple[tuple[str, str], ...]) -> str:
        if not labels:
            return ""
        body = ",".join(f'{key}="{_escape(value)}"' for key, value in labels)
        return "{" + body + "}"


metrics = MetricsRegistry()

