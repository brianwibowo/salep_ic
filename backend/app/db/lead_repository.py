"""SQLAlchemy lead repository used when DATABASE_URL is configured."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, sessionmaker

from app.agent.schemas import LeadRecord
from app.db.models import Base, LeadModel
from app.db.engine import build_engine, session_factory
from app.services.lead_merge import scraped_lead_changes


class SqlAlchemyLeadRepository:
    """Repository-compatible persistence for PostgreSQL or SQLAlchemy SQLite.

    The existing SQLite repository remains available for tests and local
    development. This class deliberately exposes the same methods used by the
    API so the application can switch backends without changing route logic.
    """

    def __init__(
        self,
        database_url: str,
        *,
        create_schema: bool = False,
        session_factory_override: sessionmaker[Session] | None = None,
    ) -> None:
        self.engine = build_engine(database_url)
        self.session_factory = session_factory_override or session_factory(self.engine)
        if create_schema:
            Base.metadata.create_all(self.engine)

    def _session(self) -> Session:
        return self.session_factory()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _to_dict(row: LeadModel) -> dict[str, Any]:
        return {
            "lead_id": row.lead_id,
            "source": row.source,
            "source_url": row.source_url,
            "author_name": row.author_name,
            "author_profile_url": row.author_profile_url,
            "published_at": row.published_at.isoformat() if row.published_at else None,
            "matched_keyword": row.matched_keyword,
            "content": row.content,
            "is_potential_lead": bool(row.is_potential_lead),
            "intent": row.intent,
            "industry": row.industry,
            "needs": row.needs or [],
            "pain_points": row.pain_points or [],
            "recommended_services": row.recommended_services or [],
            "lead_score": row.lead_score,
            "confidence": row.confidence,
            "evidence": row.evidence or [],
            "score_breakdown": row.score_breakdown,
            "canonical_post_id": row.canonical_post_id,
            "deterministic_relevance_score": row.deterministic_relevance_score,
            "deterministic_relevance_label": row.deterministic_relevance_label,
            "deterministic_relevance_reason": row.deterministic_relevance_reason,
            "spam_label": row.spam_label,
            "spam_score": row.spam_score,
            "is_spam": bool(row.is_spam),
            "quality_flags": row.quality_flags or [],
            "analyzed_at": row.analyzed_at.isoformat() if row.analyzed_at else None,
            "marketing_status": row.marketing_status,
            "sales_status": row.sales_status,
            "notes": row.notes,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }

    @staticmethod
    def _model_values(lead: LeadRecord, *, marketing_status: str, sales_status: str, now: datetime) -> dict[str, Any]:
        analyzed_at = lead.analyzed_at or now
        return {
            "lead_id": lead.lead_id,
            "source": lead.source,
            "source_url": lead.source_url,
            "author_name": lead.author_name,
            "author_profile_url": lead.author_profile_url,
            "published_at": lead.published_at,
            "matched_keyword": lead.matched_keyword,
            "content": lead.content,
            "is_potential_lead": lead.is_potential_lead,
            "intent": lead.intent.value if hasattr(lead.intent, "value") else str(lead.intent),
            "industry": lead.industry,
            "needs": lead.needs,
            "pain_points": lead.pain_points,
            "recommended_services": [service.model_dump() for service in lead.recommended_services],
            "lead_score": lead.lead_score,
            "confidence": lead.confidence,
            "evidence": lead.evidence,
            "score_breakdown": lead.score_breakdown.model_dump() if lead.score_breakdown else None,
            "canonical_post_id": lead.canonical_post_id,
            "deterministic_relevance_score": lead.deterministic_relevance_score,
            "deterministic_relevance_label": lead.deterministic_relevance_label,
            "deterministic_relevance_reason": lead.deterministic_relevance_reason,
            "spam_label": lead.spam_label,
            "spam_score": lead.spam_score,
            "is_spam": lead.is_spam,
            "quality_flags": lead.quality_flags,
            "analyzed_at": analyzed_at,
            "marketing_status": marketing_status,
            "sales_status": sales_status,
            "created_at": now,
            "updated_at": now,
        }

    def save_lead(self, lead: LeadRecord, default_status: str | None = None) -> dict[str, Any]:
        session = self._session()
        now = self._now()
        try:
            existing = session.scalar(
                select(LeadModel).where(
                    or_(
                        LeadModel.lead_id == lead.lead_id,
                        (LeadModel.source_url != '') & (LeadModel.source_url == lead.source_url),
                        (
                            (LeadModel.source == "threads")
                            & (LeadModel.canonical_post_id.is_not(None))
                            & (LeadModel.canonical_post_id == lead.canonical_post_id)
                        ),
                    )
                )
            )
            if existing:
                values = self._model_values(
                    lead,
                    marketing_status=existing.marketing_status,
                    sales_status=existing.sales_status,
                    now=now,
                )
                changes = scraped_lead_changes(self._to_dict(existing), values)
                for key, value in changes.items():
                    setattr(existing, key, value)
                if changes:
                    existing.updated_at = now
                lead_id = existing.lead_id
                lead.lead_id = lead_id
            else:
                status = default_status or lead.marketing_status
                model = LeadModel(
                    **self._model_values(
                        lead,
                        marketing_status=status,
                        sales_status=lead.sales_status,
                        now=now,
                    )
                )
                session.add(model)
                lead_id = model.lead_id
            session.commit()
            row = session.get(LeadModel, lead_id)
            return self._to_dict(row) if row else {}
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _conditions(
        self,
        *,
        role: str,
        status: str = "all",
        search: str = "",
        sales_status: str = "all",
        source: str = "all",
    ) -> list[Any]:
        if role not in {"marketing", "sales"}:
            raise ValueError("Unknown role")
        conditions: list[Any] = []
        if role == "sales":
            conditions.append(LeadModel.marketing_status == "valid")
        elif status and status.casefold() != "all":
            conditions.append(LeadModel.marketing_status == status.casefold())
        if sales_status != "all":
            conditions.append(LeadModel.sales_status == sales_status)
        if source == "social_media":
            conditions.append(LeadModel.source.in_(["threads", "linkedin"]))
        elif source != "all":
            conditions.append(LeadModel.source == source)
        if search.strip():
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    LeadModel.content.ilike(pattern),
                    LeadModel.author_name.ilike(pattern),
                    LeadModel.matched_keyword.ilike(pattern),
                )
            )
        return conditions

    def get_leads(
        self,
        role: str = "marketing",
        status: str = "all",
        search: str = "",
        limit: int = 50,
        offset: int = 0,
        sales_status: str = "all",
        source: str = "all",
    ) -> list[dict[str, Any]]:
        session = self._session()
        try:
            statement = (
                select(LeadModel)
                .where(*self._conditions(role=role, status=status, search=search, sales_status=sales_status, source=source))
                .order_by(LeadModel.analyzed_at.desc(), LeadModel.lead_score.desc(), LeadModel.lead_id)
                .offset(offset)
                .limit(limit)
            )
            return [self._to_dict(row) for row in session.scalars(statement).all()]
        finally:
            session.close()

    def count_leads(
        self,
        role: str = "marketing",
        status: str = "all",
        search: str = "",
        sales_status: str = "all",
        source: str = "all",
    ) -> int:
        session = self._session()
        try:
            statement = select(func.count()).select_from(LeadModel).where(
                *self._conditions(role=role, status=status, search=search, sales_status=sales_status, source=source)
            )
            return int(session.scalar(statement) or 0)
        finally:
            session.close()

    def get_lead(self, lead_id: str) -> dict[str, Any] | None:
        session = self._session()
        try:
            row = session.get(LeadModel, lead_id)
            return self._to_dict(row) if row else None
        finally:
            session.close()

    def delete_lead(self, lead_id: str) -> bool:
        session = self._session()
        try:
            row = session.get(LeadModel, lead_id)
            if not row:
                return False
            session.delete(row)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_marketing_status(self, lead_id: str, new_status: str) -> dict[str, Any] | None:
        clean_status = new_status.strip().lower()
        if clean_status not in {"valid", "invalid", "pending"}:
            raise ValueError(f"Invalid marketing status: {clean_status}")
        return self._update_status(lead_id, marketing_status=clean_status)

    def update_sales_status(self, lead_id: str, new_status: str) -> dict[str, Any] | None:
        return self._update_status(lead_id, sales_status=new_status.strip(), require_valid=True)

    def _update_status(
        self,
        lead_id: str,
        *,
        marketing_status: str | None = None,
        sales_status: str | None = None,
        require_valid: bool = False,
    ) -> dict[str, Any] | None:
        session = self._session()
        try:
            row = session.get(LeadModel, lead_id)
            if not row or (require_valid and row.marketing_status != "valid"):
                return None
            if marketing_status is not None:
                row.marketing_status = marketing_status
            if sales_status is not None:
                row.sales_status = sales_status
            row.updated_at = self._now()
            session.commit()
            return self._to_dict(row)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_stats(self) -> dict[str, int]:
        session = self._session()
        try:
            def count(*conditions: Any) -> int:
                return int(session.scalar(select(func.count()).select_from(LeadModel).where(*conditions)) or 0)

            valid = count(LeadModel.marketing_status == "valid")
            return {
                "total": count(),
                "valid": valid,
                "pending": count(LeadModel.marketing_status == "pending"),
                "invalid": count(LeadModel.marketing_status == "invalid"),
                "sales_new": count(LeadModel.marketing_status == "valid", LeadModel.sales_status == "Belum Dihubungi"),
                "sales_in_progress": count(LeadModel.marketing_status == "valid", LeadModel.sales_status == "Sedang Dihubungi"),
                "sales_closed": count(LeadModel.marketing_status == "valid", LeadModel.sales_status == "Closing"),
            }
        finally:
            session.close()

