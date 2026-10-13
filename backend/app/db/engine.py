"""SQLAlchemy engine/session factory used by the incremental migration."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


from pathlib import Path


def default_procurement_db_url() -> str:
    path = Path(__file__).resolve().parents[2] / "data" / "salep-procurement.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


def normalize_database_url(url: str) -> str:
    """Normalize common platform-provided PostgreSQL URLs."""

    clean = url.strip()
    if clean.startswith("postgres://"):
        return "postgresql+psycopg://" + clean.removeprefix("postgres://")
    if clean.startswith("postgresql://"):
        return "postgresql+psycopg://" + clean.removeprefix("postgresql://")
    return clean


def build_engine(database_url: str | None = None) -> Engine:
    raw_url = database_url or settings.database_url
    if not raw_url and not settings.is_production:
        raw_url = default_procurement_db_url()
    if not raw_url:
        raise ValueError("DATABASE_URL belum dikonfigurasi")
    url = normalize_database_url(raw_url)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    if url.startswith("sqlite") and not settings.is_production:
        from app.db.models import Base
        Base.metadata.create_all(engine)
    return engine


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

