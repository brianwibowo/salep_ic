"""Backfill the legacy SQLite leads table into the SQLAlchemy backend.

Usage:
    python scripts/migrate_sqlite_to_postgres.py \
      --sqlite-path data/salep_leads.db \
      --database-url postgresql+psycopg://user:pass@host:5432/salep

The script is idempotent by lead_id/source_url and can be run again after a
partial deployment. It does not delete or modify the SQLite source.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from app.agent.schemas import LeadRecord
from app.db.lead_repository import SqlAlchemyLeadRepository
from app.services.lead_repository import LeadRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite-path", type=Path, required=True)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--batch-size", type=int, default=250)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--create-schema", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = LeadRepository(args.sqlite_path, seed_samples=False)
    target = None if args.dry_run else SqlAlchemyLeadRepository(
        args.database_url,
        create_schema=args.create_schema,
    )
    total = source.count_leads(role="marketing")
    migrated = 0

    for offset in range(0, total, args.batch_size):
        rows = source.get_leads(role="marketing", limit=args.batch_size, offset=offset)
        for row in rows:
            record = LeadRecord.model_validate(row)
            if target is not None:
                target.save_lead(record)
            migrated += 1

    print(f"SQLite rows discovered: {total}")
    print(f"Rows {'validated' if args.dry_run else 'migrated'}: {migrated}")


if __name__ == "__main__":
    main()

