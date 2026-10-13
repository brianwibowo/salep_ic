"""SQLAlchemy engine/session factory used by the incremental migration."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def normalize_database_url(url: str) -> str:
    """Normalize common platform-provided PostgreSQL URLs."""

    clean = url.strip()
    if clean.startswith("postgres://"):
        return "postgresql+psycopg://" + clean.removeprefix("postgres://")
    if clean.startswith("postgresql://"):
        return "postgresql+psycopg://" + clean.removeprefix("postgresql://")
    return clean


def build_engine(database_url: str | None = None) -> Engine:
    url = normalize_database_url(database_url or settings.database_url)
    if not url:
        raise ValueError("DATABASE_URL belum dikonfigurasi")
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

