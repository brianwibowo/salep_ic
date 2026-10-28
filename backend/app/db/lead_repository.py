"""SQLAlchemy lead repository used when DATABASE_URL is configured."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo
from typing import Any
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, sessionmaker

from app.agent.schemas import LeadRecord, SalesStatusLog
from app.db.auth_models import AuthUser
from app.db.models import ActivityLogModel, Base, LeadAssignmentModel, LeadModel
from app.db.engine import build_engine, session_factory
from app.services.lead_merge import scraped_lead_changes


class ReviewConflict(Exception):
    """The form was opened before another Marketing review was saved."""


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
        assignment = row.current_assignment
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
            "sales_status_logs": row.sales_status_logs or [],
            "notes": row.notes,
            "marketing_reviewed_by_user_id": row.marketing_reviewed_by_user_id,
            "marketing_reviewed_by_username": row.marketing_reviewed_by_username,
            "marketing_reviewed_at": row.marketing_reviewed_at.isoformat() if row.marketing_reviewed_at else None,
            "marketing_review_note": row.marketing_review_note,
            "review_version": row.review_version,
            "deleted_at": row.deleted_at.isoformat() if row.deleted_at else None,
            "deleted_by_user_id": row.deleted_by_user_id,
            "deleted_by_username": row.deleted_by_username,
            "assignment": {
                "assignment_id": assignment.assignment_id,
                "sales_user_id": assignment.sales_user_id,
                "sales_username": assignment.sales_username,
                "assigned_by_user_id": assignment.assigned_by_user_id,
                "assigned_at": assignment.assigned_at.isoformat(),
            } if assignment else None,
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
            "sales_status_logs": [log.model_dump(mode="json") for log in lead.sales_status_logs],
            "marketing_reviewed_by_user_id": lead.marketing_reviewed_by_user_id,
            "marketing_reviewed_by_username": lead.marketing_reviewed_by_username,
            "marketing_reviewed_at": lead.marketing_reviewed_at,
            "marketing_review_note": lead.marketing_review_note,
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
                ).with_for_update()
            )
            if existing:
                # Keep the tombstone and evidence unchanged on scraper replay.
                # Never create a replacement row or implicitly restore this lead.
                if existing.deleted_at is not None:
                    lead.lead_id = existing.lead_id
                    return self._to_dict(existing)
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
        user_id: str | None = None,
        sales_user_id: str | None = None,
        assignment_status: str = "all",
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Any]:
        if role not in {"marketing", "sales"}:
            raise ValueError("Unknown role")
        conditions: list[Any] = [LeadModel.deleted_at.is_(None)]
        if role == "sales":
            conditions.append(LeadModel.marketing_status == "valid")
            conditions.append(select(LeadAssignmentModel.assignment_id).where(
                LeadAssignmentModel.lead_id == LeadModel.lead_id,
                LeadAssignmentModel.sales_user_id == user_id,
                LeadAssignmentModel.unassigned_at.is_(None),
            ).exists())
        elif status and status.casefold() != "all":
            conditions.append(LeadModel.marketing_status == status.casefold())
        active_assignment = select(LeadAssignmentModel.assignment_id).where(
            LeadAssignmentModel.lead_id == LeadModel.lead_id,
            LeadAssignmentModel.unassigned_at.is_(None),
        )
        if assignment_status == "unassigned":
            conditions.extend([LeadModel.marketing_status == "valid", ~active_assignment.exists()])
        elif assignment_status == "assigned":
            conditions.append(active_assignment.exists())
        if sales_user_id:
            conditions.append(active_assignment.where(LeadAssignmentModel.sales_user_id == sales_user_id).exists())
        # Filter by lead arrival time, not publication/review time. Calendar dates
        # are interpreted in WIB so end-of-day records are included consistently.
        wib = ZoneInfo("Asia/Jakarta")
        if date_from:
            conditions.append(LeadModel.created_at >= datetime.combine(date_from, time.min, wib).astimezone(timezone.utc))
        if date_to:
            conditions.append(LeadModel.created_at <= datetime.combine(date_to, time.max, wib).astimezone(timezone.utc))
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
        user_id: str | None = None,
        sales_user_id: str | None = None,
        assignment_status: str = "all",
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict[str, Any]]:
        session = self._session()
        try:
            statement = (
                select(LeadModel)
                .where(*self._conditions(role=role, status=status, search=search, sales_status=sales_status, source=source,
                                        user_id=user_id, sales_user_id=sales_user_id, assignment_status=assignment_status,
                                        date_from=date_from, date_to=date_to))
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
        user_id: str | None = None,
        sales_user_id: str | None = None,
        assignment_status: str = "all",
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> int:
        session = self._session()
        try:
            statement = select(func.count()).select_from(LeadModel).where(
                *self._conditions(role=role, status=status, search=search, sales_status=sales_status, source=source,
                                  user_id=user_id, sales_user_id=sales_user_id, assignment_status=assignment_status,
                                  date_from=date_from, date_to=date_to)
            )
            return int(session.scalar(statement) or 0)
        finally:
            session.close()

    def get_lead(self, lead_id: str) -> dict[str, Any] | None:
        session = self._session()
        try:
            row = session.get(LeadModel, lead_id)
            return self._to_dict(row) if row and row.deleted_at is None else None
        finally:
            session.close()

    def get_deleted_source_urls(self, source_urls: list[str]) -> set[str]:
        """Suppress deleted leads in historical external exports without editing them."""
        if not source_urls:
            return set()
        with self._session() as session:
            return set(session.scalars(select(LeadModel.source_url).where(
                LeadModel.source_url.in_(source_urls), LeadModel.deleted_at.is_not(None),
            )))

    def delete_lead(self, lead_id: str, *, deleted_by_user_id: str,
                    api: str = "/api/v1/leads/{lead_id}", request_id: str | None = None) -> bool:
        session = self._session()
        try:
            row = session.scalar(select(LeadModel).where(LeadModel.lead_id == lead_id).with_for_update())
            if not row or row.deleted_at is not None:
                return False
            actor = session.scalar(select(AuthUser).where(
                AuthUser.id == deleted_by_user_id, AuthUser.role == "marketing", AuthUser.active.is_(True),
            ).with_for_update(read=True))
            if actor is None:
                raise ValueError("Akun Marketing tidak aktif atau tidak valid")
            now = self._now()
            row.deleted_at = now
            row.deleted_by_user_id = actor.id
            row.deleted_by_username = actor.username
            row.updated_at = now
            session.add(ActivityLogModel(
                activity_id=uuid.uuid4().hex, user_id=actor.id, action="SOFT_DELETE_LEAD",
                entity_type="lead", entity_id=lead_id, api=api, http_method="DELETE", http_status=200,
                request_id=request_id, old_value={"deleted_at": None},
                new_value={"deleted_at": now.isoformat(), "deleted_by_user_id": actor.id},
                metadata_json={"deleted_by_username": actor.username}, created_at=now,
            ))
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_marketing_status(
        self,
        lead_id: str,
        new_status: str,
        *,
        reviewed_by_user_id: str,
        expected_version: int,
        sales_user_id: str | None = None,
        review_note: str | None = None,
        api: str = "/api/v1/leads/{lead_id}/status",
        request_id: str | None = None,
    ) -> dict[str, Any] | None:
        clean_status = new_status.strip().lower()
        if clean_status not in {"valid", "invalid", "pending"}:
            raise ValueError(f"Invalid marketing status: {clean_status}")
        session = self._session()
        try:
            # Serializes reviewers AND Sales updates on this same parent row.
            row = session.scalar(select(LeadModel).where(LeadModel.lead_id == lead_id).with_for_update())
            if not row or row.deleted_at is not None:
                return None
            if row.review_version != expected_version:
                raise ReviewConflict("Lead sudah direview Marketing lain. Muat data terbaru sebelum menyimpan kembali.")
            reviewer = session.scalar(select(AuthUser).where(
                AuthUser.id == reviewed_by_user_id, AuthUser.role == "marketing", AuthUser.active.is_(True),
            ).with_for_update(read=True))
            if reviewer is None:
                raise ValueError("Akun Marketing tidak aktif atau tidak valid")
            if clean_status != "valid" and sales_user_id is not None:
                raise ValueError("Assignment hanya tersedia untuk lead valid")
            recipient = None
            if clean_status == "valid":
                recipient = session.scalar(select(AuthUser).where(
                    AuthUser.id == sales_user_id, AuthUser.role == "sales", AuthUser.active.is_(True),
                ).with_for_update(read=True))
                if recipient is None:
                    raise ValueError("Pilih akun Sales yang aktif")
            active = session.scalar(select(LeadAssignmentModel).where(
                LeadAssignmentModel.lead_id == lead_id, LeadAssignmentModel.unassigned_at.is_(None),
            ))
            before = {"marketing_status": row.marketing_status, "review_version": row.review_version,
                      "review_note": row.marketing_review_note,
                      "sales_user_id": active.sales_user_id if active else None}
            now = self._now()
            if active and (recipient is None or active.sales_user_id != recipient.id):
                active.unassigned_at = now
                active.unassigned_by_user_id = reviewer.id
                active.unassign_reason = "Dialihkan ke Sales lain" if recipient else f"Status review menjadi {clean_status}"
                session.flush()  # Close the old assignment before inserting the new one.
                active = None
            if recipient and active is None:
                session.add(LeadAssignmentModel(
                    assignment_id=uuid.uuid4().hex, lead_id=lead_id,
                    sales_user_id=recipient.id, sales_username=recipient.username,
                    assigned_by_user_id=reviewer.id, assigned_at=now,
                ))
            row.marketing_reviewed_by_user_id = reviewer.id
            row.marketing_reviewed_by_username = reviewer.username
            row.marketing_reviewed_at = now
            row.marketing_review_note = (review_note.strip() or None) if review_note else None
            row.marketing_status = clean_status
            row.review_version += 1
            row.updated_at = now
            session.add(ActivityLogModel(
                activity_id=uuid.uuid4().hex,
                user_id=reviewed_by_user_id,
                action="REVIEW_AND_ASSIGN_LEAD",
                entity_type="lead",
                entity_id=lead_id,
                api=api,
                http_method="PATCH",
                http_status=200,
                request_id=request_id,
                old_value=before,
                new_value={"marketing_status": clean_status, "review_note": row.marketing_review_note,
                           "review_version": row.review_version, "sales_user_id": recipient.id if recipient else None},
                metadata_json={"reviewer_username": reviewer.username},
                created_at=now,
            ))
            session.commit()
            session.expire(row, ["current_assignment"])
            return self._to_dict(row)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_sales_status(
        self,
        lead_id: str,
        new_status: str,
        note: str,
        changed_by: str | None = None,
        *,
        user_id: str | None = None,
    ) -> dict[str, Any] | None:
        session = self._session()
        try:
            row = session.scalar(select(LeadModel).where(LeadModel.lead_id == lead_id).with_for_update())
            if not row or row.deleted_at is not None or row.marketing_status != "valid":
                return None
            assigned = session.scalar(select(LeadAssignmentModel.assignment_id).where(
                LeadAssignmentModel.lead_id == lead_id,
                LeadAssignmentModel.sales_user_id == user_id,
                LeadAssignmentModel.unassigned_at.is_(None),
            ))
            if assigned is None:
                return None
            now = self._now()
            next_status = new_status.strip()
            logs = list(row.sales_status_logs or [])
            logs.append(SalesStatusLog(
                id=uuid.uuid4().hex,
                from_status=row.sales_status,
                to_status=next_status,
                note=note.strip(),
                changed_by=changed_by,
                changed_at=now,
            ).model_dump(mode="json"))
            row.sales_status = next_status
            row.sales_status_logs = logs
            row.updated_at = now
            session.commit()
            return self._to_dict(row)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

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
            row = session.scalar(select(LeadModel).where(LeadModel.lead_id == lead_id).with_for_update())
            if not row or row.deleted_at is not None or (require_valid and row.marketing_status != "valid"):
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

    def list_sales_users(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        with self._session() as session:
            statement = select(AuthUser).where(AuthUser.role == "sales")
            if not include_inactive:
                statement = statement.where(AuthUser.active.is_(True))
            users = session.scalars(statement.order_by(AuthUser.username)).all()
            return [{"user_id": user.id, "username": user.username, "active": user.active} for user in users]

    def get_stats(self, role: str = "marketing", user_id: str | None = None) -> dict[str, int]:
        session = self._session()
        try:
            def count(*conditions: Any) -> int:
                scope = self._conditions(role=role, user_id=user_id)
                return int(session.scalar(select(func.count()).select_from(LeadModel).where(*scope, *conditions)) or 0)

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

