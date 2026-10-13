"""Small persistent/in-memory cache for successful SALEP analyses."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from app.agent.schemas import LeadAnalysis
from app.core.config import settings
from app.core.logging import logger


PROMPT_VERSION = "threads-precision-v1"


def analysis_cache_key(content: str, model_name: str, prompt_version: str = PROMPT_VERSION) -> tuple[str, str]:
    content_hash = hashlib.sha256(" ".join(content.split()).casefold().encode("utf-8")).hexdigest()
    key = hashlib.sha256(f"{content_hash}:{model_name}:{prompt_version}".encode("utf-8")).hexdigest()
    return key, content_hash


class LLMAnalysisCache:
    """Use PostgreSQL when configured, with a safe process-local fallback."""

    def __init__(self) -> None:
        self._memory: dict[str, LeadAnalysis] = {}
        self._factory: Any = None
        self._model: Any = None
        if not settings.database_url.strip():
            return
        try:
            from app.db.engine import build_engine, session_factory
            from app.db.models import LLMAnalysisCacheModel

            engine = build_engine(settings.database_url)
            self._factory = session_factory(engine)
            self._model = LLMAnalysisCacheModel
        except Exception as exc:
            logger.warning("LLM cache database unavailable; using memory cache: %s", exc)

    def get(self, content: str, model_name: str, prompt_version: str = PROMPT_VERSION) -> LeadAnalysis | None:
        key, _ = analysis_cache_key(content, model_name, prompt_version)
        hit: LeadAnalysis | None = None
        if self._factory and self._model:
            session = self._factory()
            try:
                row = session.get(self._model, key)
                if row:
                    row.hit_count = int(row.hit_count or 0) + 1
                    row.last_used_at = datetime.now(timezone.utc)
                    session.commit()
                    hit = LeadAnalysis.model_validate(row.response)
            except Exception as exc:
                session.rollback()
                logger.warning("LLM cache read failed: %s", exc)
            finally:
                session.close()
        if hit is None:
            hit = self._memory.get(key)
        if hit is not None:
            logger.info("LLM cache hit model=%s key=%s", model_name, key[:12])
        return hit

    def put(self, content: str, model_name: str, analysis: LeadAnalysis, prompt_version: str = PROMPT_VERSION) -> None:
        key, content_hash = analysis_cache_key(content, model_name, prompt_version)
        self._memory[key] = analysis
        if not (self._factory and self._model):
            return
        session = self._factory()
        now = datetime.now(timezone.utc)
        try:
            row = session.get(self._model, key)
            if row:
                row.response = analysis.model_dump(mode="json")
                row.last_used_at = now
            else:
                session.add(self._model(
                    cache_key=key,
                    content_hash=content_hash,
                    model_name=model_name,
                    prompt_version=prompt_version,
                    response=analysis.model_dump(mode="json"),
                    created_at=now,
                    last_used_at=now,
                    hit_count=0,
                ))
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.warning("LLM cache write failed: %s", exc)
        finally:
            session.close()


llm_analysis_cache = LLMAnalysisCache()

