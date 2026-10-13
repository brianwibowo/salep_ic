"""Create verified PostgreSQL/SQLite backups and prune expired backup files.

Production PostgreSQL credentials should come from the environment or
``.pgpass``; the script never prints the database URL.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _prune(directory: Path, retention_days: int, *, dry_run: bool) -> list[str]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    removed: list[str] = []
    paths = list(directory.glob("salep-*.dump")) + list(directory.glob("salep-*.sqlite3"))
    for path in paths:
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if modified < cutoff:
            removed.append(str(path))
            if not dry_run:
                path.unlink(missing_ok=True)
                path.with_suffix(path.suffix + ".sha256").unlink(missing_ok=True)
    return removed


def _backup_postgres(database_url: str, directory: Path, stamp: str, *, dry_run: bool) -> Path | None:
    output = directory / f"salep-postgres-{stamp}.dump"
    if dry_run:
        print(f"DRY-RUN postgres backup: {output}")
        return None
    if shutil.which("pg_dump") is None:
        raise RuntimeError("pg_dump tidak ditemukan di PATH")
    subprocess.run(
        ["pg_dump", "--format=custom", "--no-owner", "--file", str(output), database_url],
        check=True,
    )
    return output


def _backup_sqlite(sqlite_path: Path, directory: Path, stamp: str, *, dry_run: bool) -> Path | None:
    output = directory / f"salep-sqlite-{stamp}.sqlite3"
    if dry_run:
        print(f"DRY-RUN SQLite backup: {output}")
        return None
    source = sqlite3.connect(str(sqlite_path))
    target = sqlite3.connect(str(output))
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", ""))
    parser.add_argument("--sqlite-path", type=Path, default=Path("data/salep_leads.db"))
    parser.add_argument("--output-dir", type=Path, default=Path(os.getenv("BACKUP_DIR", "data/backups")))
    parser.add_argument("--retention-days", type=int, default=int(os.getenv("BACKUP_RETENTION_DAYS", "14")))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifacts: list[Path] = []
    if args.database_url:
        artifact = _backup_postgres(args.database_url, args.output_dir, stamp, dry_run=args.dry_run)
    elif args.sqlite_path.exists():
        artifact = _backup_sqlite(args.sqlite_path, args.output_dir, stamp, dry_run=args.dry_run)
    else:
        raise RuntimeError("DATABASE_URL kosong dan SQLite database tidak ditemukan")
    if artifact:
        checksum = _digest(artifact)
        artifact.with_suffix(artifact.suffix + ".sha256").write_text(f"{checksum}  {artifact.name}\n", encoding="utf-8")
        manifest = args.output_dir / "manifest.jsonl"
        with manifest.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"created_at": stamp, "path": artifact.name, "sha256": checksum}) + "\n")
        print(f"Backup created: {artifact} sha256={checksum}")
    removed = _prune(args.output_dir, args.retention_days, dry_run=args.dry_run)
    if removed:
        print(f"Pruned {len(removed)} expired backup(s)")


if __name__ == "__main__":
    main()

