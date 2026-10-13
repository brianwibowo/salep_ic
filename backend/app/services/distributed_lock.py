"""Cross-process scheduler lock with PostgreSQL advisory-lock support."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logging import logger
from app.core.metrics import metrics


class DistributedLock:
    def __init__(self, name: str | None = None, path: str | None = None) -> None:
        self.name = name or settings.scheduler_lock_name
        self.path = Path(path or settings.scheduler_lock_path)
        self._connection: Any = None
        self._engine: Any = None
        self._file_handle: Any = None
        self._mode: str | None = None

    def try_acquire(self) -> bool:
        if settings.database_url.lower().startswith(("postgres://", "postgresql://", "postgresql+")):
            postgres_result = self._try_postgres()
            if postgres_result is not None:
                return postgres_result
        return self._try_file()

    def release(self) -> None:
        if self._mode == "postgres" and self._connection is not None:
            try:
                from sqlalchemy import text

                self._connection.execute(text("SELECT pg_advisory_unlock(hashtext(:lock_name))"), {"lock_name": self.name})
                self._connection.commit()
            except Exception as exc:
                logger.warning("Could not release PostgreSQL scheduler lock: %s", exc)
            finally:
                self._connection.close()
                self._connection = None
                if self._engine is not None:
                    self._engine.dispose()
                    self._engine = None
                metrics.set_gauge("salep_scheduler_lock_held", 0, {"backend": "postgres"})
        elif self._mode == "file" and self._file_handle is not None:
            try:
                import fcntl

                fcntl.flock(self._file_handle.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                self._file_handle.close()
            finally:
                self._file_handle = None
                metrics.set_gauge("salep_scheduler_lock_held", 0, {"backend": "file"})
        self._mode = None

    def _try_postgres(self) -> bool | None:
        try:
            from sqlalchemy import create_engine, text

            url = settings.database_url
            if url.startswith("postgres://"):
                url = "postgresql+psycopg://" + url.removeprefix("postgres://")
            elif url.startswith("postgresql://"):
                url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
            engine = create_engine(url, pool_pre_ping=True)
            connection = engine.connect()
            acquired = bool(connection.execute(
                text("SELECT pg_try_advisory_lock(hashtext(:lock_name))"),
                {"lock_name": self.name},
            ).scalar())
            if acquired:
                self._connection = connection
                self._engine = engine
                self._mode = "postgres"
                metrics.set_gauge("salep_scheduler_lock_held", 1, {"backend": "postgres"})
                return True
            connection.close()
            engine.dispose()
            metrics.inc("salep_scheduler_lock_contention", labels={"backend": "postgres"})
            return False
        except Exception as exc:
            logger.warning("PostgreSQL lock unavailable; using file lock fallback: %s", exc)
            metrics.inc("salep_scheduler_lock_fallback_total", labels={"backend": "postgres"})
            return None

    def _try_file(self) -> bool:
        try:
            import fcntl

            self.path.parent.mkdir(parents=True, exist_ok=True)
            handle = self.path.open("a+")
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                handle.close()
                metrics.inc("salep_scheduler_lock_contention", labels={"backend": "file"})
                return False
            handle.seek(0)
            handle.truncate()
            handle.write(str(os.getpid()))
            handle.flush()
            self._file_handle = handle
            self._mode = "file"
            metrics.set_gauge("salep_scheduler_lock_held", 1, {"backend": "file"})
            return True
        except Exception as exc:
            logger.error("Scheduler file lock failed: %s", exc)
            metrics.inc("salep_scheduler_lock_errors_total", labels={"backend": "file"})
            return False

    def __enter__(self) -> "DistributedLock":
        if not self.try_acquire():
            raise RuntimeError("scheduler_lock_unavailable")
        return self

    def __exit__(self, *_exc: object) -> None:
        self.release()

