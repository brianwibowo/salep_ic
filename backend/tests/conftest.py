"""Shared test policy for deterministic local and CI runs."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def isolate_runtime(request, monkeypatch, tmp_path):
    import httpx
    from app.core.config import settings

    monkeypatch.setattr(settings, 'scheduler_lock_path', str(tmp_path / 'scheduler.lock'))
    monkeypatch.setattr(settings, 'alert_webhook_url', '')
    monkeypatch.setattr(settings, 'database_url', '')
    monkeypatch.setattr(settings, 'inaproc_auto_sync_enabled', False)
    if 'external' in request.keywords:
        return

    def reject_network(*args, **kwargs):
        pytest.fail('Unexpected external HTTP request; inject MockTransport or mark external')

    async def reject_async_network(*args, **kwargs):
        reject_network()

    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', reject_network)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, 'handle_async_request', reject_async_network)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-external",
        action="store_true",
        default=False,
        help="run tests that require live LLM or public portal providers",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "external: requires a live external provider")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    enabled = config.getoption("--run-external") or os.getenv("RUN_EXTERNAL_TESTS") == "1"
    if enabled:
        return
    skip = pytest.mark.skip(reason="external provider test disabled; use --run-external")
    for item in items:
        if "external" in item.keywords:
            item.add_marker(skip)
