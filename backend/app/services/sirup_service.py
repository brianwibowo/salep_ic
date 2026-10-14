"""Read-side queries for the normalized Si-RUP package catalogue."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any, Literal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.engine import build_engine
from app.db.models import ProcurementPackageModel


SirupSort = Literal["newest", "oldest", "budget_desc", "budget_asc"]


def _start_of_day(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _end_of_day(value: date) -> datetime:
    return datetime.combine(value, time.max, tzinfo=timezone.utc)


def _serialize(row: ProcurementPackageModel) -> dict[str, Any]:
    return {
        "package_id": row.id,
        "external_id": row.external_id,
        "rup_id": row.rup_id,
        "package_name": row.package_name,
        "description": row.description,
        "organization": row.organization,
        "satker": row.satker,
        "location": row.location,
        "procurement_type": row.procurement_type,
        "procurement_method": row.procurement_method,
        "fiscal_year": row.fiscal_year,
        "budget_amount": row.budget_amount,
        "local_content_flag": row.local_content_flag,
        "small_business_flag": row.small_business_flag,
        "source_url": row.source_url,
        "first_seen_at": row.first_seen_at.isoformat() if row.first_seen_at else None,
        "last_seen_at": row.last_seen_at.isoformat() if row.last_seen_at else None,
    }


class SirupService:
    def __init__(self, database_url: str | None = None) -> None:
        self.engine = build_engine(database_url or settings.database_url)

    @staticmethod
    def _where(
        *,
        fiscal_year: int | None,
        search: str,
        procurement_type: str,
        procurement_method: str,
        date_from: date | None,
        date_to: date | None,
    ) -> list[Any]:
        conditions: list[Any] = [ProcurementPackageModel.source == "sirup"]
        if fiscal_year is not None:
            conditions.append(ProcurementPackageModel.fiscal_year == fiscal_year)
        if procurement_type:
            conditions.append(ProcurementPackageModel.procurement_type == procurement_type)
        if procurement_method:
            conditions.append(ProcurementPackageModel.procurement_method == procurement_method)
        if date_from:
            conditions.append(ProcurementPackageModel.last_seen_at >= _start_of_day(date_from))
        if date_to:
            conditions.append(ProcurementPackageModel.last_seen_at <= _end_of_day(date_to))
        normalized = search.strip()
        if normalized:
            pattern = f"%{normalized}%"
            conditions.append(or_(
                ProcurementPackageModel.package_name.ilike(pattern),
                ProcurementPackageModel.external_id.ilike(pattern),
                ProcurementPackageModel.organization.ilike(pattern),
                ProcurementPackageModel.satker.ilike(pattern),
                ProcurementPackageModel.location.ilike(pattern),
                ProcurementPackageModel.procurement_type.ilike(pattern),
                ProcurementPackageModel.procurement_method.ilike(pattern),
            ))
        return conditions

    def list(
        self,
        *,
        fiscal_year: int | None = None,
        search: str = "",
        procurement_type: str = "",
        procurement_method: str = "",
        date_from: date | None = None,
        date_to: date | None = None,
        sort: SirupSort = "newest",
        page: int = 1,
        limit: int = 25,
    ) -> dict[str, Any]:
        conditions = self._where(
            fiscal_year=fiscal_year,
            search=search,
            procurement_type=procurement_type,
            procurement_method=procurement_method,
            date_from=date_from,
            date_to=date_to,
        )
        sort_column = {
            "newest": ProcurementPackageModel.last_seen_at.desc(),
            "oldest": ProcurementPackageModel.last_seen_at.asc(),
            "budget_desc": ProcurementPackageModel.budget_amount.desc().nullslast(),
            "budget_asc": ProcurementPackageModel.budget_amount.asc().nullsfirst(),
        }[sort]
        with Session(self.engine) as session:
            base = select(ProcurementPackageModel).where(*conditions)
            total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
            total_budget = session.scalar(select(func.coalesce(func.sum(ProcurementPackageModel.budget_amount), 0)).where(*conditions)) or 0
            rows = session.scalars(
                base.order_by(sort_column, ProcurementPackageModel.id.asc())
                .offset((page - 1) * limit)
                .limit(limit)
            ).all()

            # Keep filter controls useful even when the current page is small.
            facet_conditions = self._where(
                fiscal_year=fiscal_year,
                search=search,
                procurement_type="",
                procurement_method="",
                date_from=date_from,
                date_to=date_to,
            )
            types = session.scalars(
                select(ProcurementPackageModel.procurement_type).where(*facet_conditions)
                .where(ProcurementPackageModel.procurement_type.is_not(None))
                .distinct().order_by(ProcurementPackageModel.procurement_type)
            ).all()
            methods = session.scalars(
                select(ProcurementPackageModel.procurement_method).where(*facet_conditions)
                .where(ProcurementPackageModel.procurement_method.is_not(None))
                .distinct().order_by(ProcurementPackageModel.procurement_method)
            ).all()
            years = session.scalars(
                select(ProcurementPackageModel.fiscal_year)
                .where(ProcurementPackageModel.source == "sirup")
                .distinct().order_by(ProcurementPackageModel.fiscal_year.desc())
            ).all()

        return {
            "items": [_serialize(row) for row in rows],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
            },
            "summary": {
                "total": total,
                "total_budget_amount": float(total_budget),
            },
            "facets": {
                "fiscal_years": [int(value) for value in years],
                "procurement_types": [value for value in types if value],
                "procurement_methods": [value for value in methods if value],
            },
            "filters": {
                "fiscal_year": fiscal_year,
                "search": search,
                "procurement_type": procurement_type,
                "procurement_method": procurement_method,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
                "sort": sort,
            },
        }
