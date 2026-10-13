"""Evaluate the deterministic Threads gate against its checked-in golden set."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.threads_quality import evaluate_golden_set, load_golden_set


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "tests/fixtures/threads/golden_set.json"
    print(json.dumps(evaluate_golden_set(load_golden_set(path)), indent=2))


if __name__ == "__main__":
    main()
