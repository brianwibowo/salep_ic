"""Prune operational PostgreSQL records while keeping lead/package history."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", ""), required=False)
    parser.add_argument("--snapshot-days", type=int, default=int(os.getenv("SNAPSHOT_RETENTION_DAYS", "90")))
    parser.add_argument("--cache-days", type=int, default=90)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.database_url:
        raise SystemExit("DATABASE_URL wajib diisi untuk retention PostgreSQL")
    url = args.database_url
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgres://")
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    engine = create_engine(url, pool_pre_ping=True)
    snapshot_cutoff = datetime.now(timezone.utc) - timedelta(days=args.snapshot_days)
    cache_cutoff = datetime.now(timezone.utc) - timedelta(days=args.cache_days)
    with engine.begin() as connection:
        snapshot_count = connection.execute(text("SELECT COUNT(*) FROM source_documents WHERE fetched_at < :cutoff"), {"cutoff": snapshot_cutoff}).scalar() or 0
        cache_count = connection.execute(text("SELECT COUNT(*) FROM llm_analysis_cache WHERE last_used_at < :cutoff"), {"cutoff": cache_cutoff}).scalar() or 0
        print(f"source_documents eligible={snapshot_count}; llm_analysis_cache eligible={cache_count}")
        if not args.dry_run:
            connection.execute(text("DELETE FROM source_documents WHERE fetched_at < :cutoff"), {"cutoff": snapshot_cutoff})
            connection.execute(text("DELETE FROM llm_analysis_cache WHERE last_used_at < :cutoff"), {"cutoff": cache_cutoff})
    engine.dispose()


if __name__ == "__main__":
    main()

