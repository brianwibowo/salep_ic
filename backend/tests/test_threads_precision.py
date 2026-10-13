from __future__ import annotations

import json
from pathlib import Path

from app.agent.schemas import RawLead
from app.services.search_service import deduplicate
from app.services.threads_quality import (
    apply_threads_quality_gate,
    canonical_threads_post_id,
    evaluate_golden_set,
)


def test_canonical_id_prefers_provider_id_and_strips_url_variants():
    assert canonical_threads_post_id("https://www.threads.net/t/ABC?utm_source=x", post_code="ABC") == "threads:abc"
    assert canonical_threads_post_id("https://www.threads.net/@alice/post/ABC#comments") == "threads:abc"
    assert canonical_threads_post_id("", explicit_id="provider-123") == "threads:provider-123"


def test_threads_gate_accepts_buying_signal_and_rejects_learning():
    good = RawLead(source="threads", source_url="https://www.threads.net/t/good", content="Butuh hosting VPS, rekomendasi vendor?", matched_keyword="hosting", author_name="A")
    bad = RawLead(source="threads", source_url="https://www.threads.net/t/bad", content="Belajar membuat aplikasi web dari tutorial", matched_keyword="web", author_name="B")
    accepted = apply_threads_quality_gate(good)
    assert accepted is not None
    assert accepted.canonical_post_id == "threads:good"
    assert apply_threads_quality_gate(bad) is None


def test_deduplicate_uses_canonical_threads_id():
    rows = [
        RawLead(source="threads", source_url="https://www.threads.net/t/one", canonical_post_id="threads:one", content="butuh server", matched_keyword="server"),
        RawLead(source="threads", source_url="https://threads.net/@x/post/one?x=1", canonical_post_id="threads:one", content="butuh server", matched_keyword="server"),
    ]
    assert len(deduplicate(rows)) == 1


def test_golden_set_precision_is_measurable():
    path = Path(__file__).parent / "fixtures/threads/golden_set.json"
    metrics = evaluate_golden_set(json.loads(path.read_text()))
    assert metrics["relevance"]["precision"] >= 0.9
    assert metrics["spam"]["precision"] >= 0.9

