"""PostgreSQL persistence for normalized Inaproc packages and transitions."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.engine import build_engine
from app.db.models import (
    Base,
    ProcurementEventModel,
    ProcurementPackageModel,
    ScrapeRunModel,
    SourceDocumentModel,
)
from app.domain.procurement import ProcurementPackage


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:40]


def _present(value: object) -> bool:
    """Return whether an observed field contains usable information.

    Scrapers commonly emit empty strings when a column is absent.  Treating
    those as updates would erase a richer value captured on an earlier run.
    Boolean ``False`` and numeric zero remain valid observations.
    """
    return value is not None and (not isinstance(value, str) or bool(value.strip()))


PACKAGE_FIELDS = (
    'rup_id', 'tender_id', 'package_name', 'description', 'organization', 'satker', 'location',
    'procurement_type', 'procurement_method', 'budget_amount', 'hps_amount', 'contract_type',
    'local_content_flag', 'small_business_flag', 'source_url', 'current_stage_code', 'current_stage_label',
)


def package_changes(row: ProcurementPackageModel, package: ProcurementPackage) -> dict:
    values = {field: getattr(package, field) for field in PACKAGE_FIELDS}
    values['current_contract_status'] = package.contract_status
    return {field: value for field, value in values.items() if _present(value) and getattr(row, field) != value}


@dataclass
class IngestionStats:
    seen: int = 0
    inserted: int = 0
    updated: int = 0
    rejected: int = 0
    unchanged: int = 0


class ProcurementRepository:
    """Transactional package upsert repository.

    ``create_schema`` is intentionally opt-in. Production schema changes must
    go through Alembic; it exists only for local smoke tests and first boot.
    """

    def __init__(self, database_url: str | None = None, *, create_schema: bool = False) -> None:
        self.engine = build_engine(database_url)
        if create_schema:
            Base.metadata.create_all(self.engine)

    def start_run(self, *, source: str, track: str | None, parameters: dict) -> str:
        run_id = f"run_{uuid.uuid4().hex}"
        now = _now()
        with Session(self.engine) as session:
            session.add(ScrapeRunModel(run_id=run_id, source=source, track=track, requested_at=now, started_at=now, status="running", parameters=parameters))
            session.commit()
        return run_id

    def finish_run(self, run_id: str, *, stats: IngestionStats, status: str = "succeeded", error: Exception | None = None) -> None:
        with Session(self.engine) as session:
            run = session.get(ScrapeRunModel, run_id)
            if run is None:
                return
            run.finished_at = _now()
            run.status = status
            run.records_seen = stats.seen
            run.records_inserted = stats.inserted
            run.records_updated = stats.updated
            run.records_rejected = stats.rejected
            if error:
                run.error_code = type(error).__name__
                run.error_message = str(error)[:4000]
            session.commit()

    def save_snapshot(self, *, package: ProcurementPackage, payload: str, run_id: str | None, action: str = "detail", http_status: int | None = 200) -> str:
        snapshot_id = f"snapshot_{_stable_id(package.source, action, package.external_id, package.source_url, payload)}"
        row = SourceDocumentModel(
            id=snapshot_id,
            source=package.source,
            action=action,
            source_url=package.source_url,
            external_id=package.external_id,
            fetched_at=_now(),
            http_status=http_status,
            access_mode="httpx",
            payload_hash=hashlib.sha256(payload.encode()).hexdigest(),
            parser_version="inaproc-v2",
            run_id=run_id,
        )
        with Session(self.engine) as session:
            existing = session.get(SourceDocumentModel, snapshot_id)
            if existing is None:
                session.add(row)
                session.commit()
        return snapshot_id

    def upsert_package(self, package: ProcurementPackage, *, run_id: str | None = None, snapshot_id: str | None = None) -> str:
        now = _now()
        key = (package.source, package.track.value, package.external_id, package.fiscal_year)
        with Session(self.engine) as session:
            row = session.scalar(select(ProcurementPackageModel).where(
                ProcurementPackageModel.source == key[0],
                ProcurementPackageModel.track == key[1],
                ProcurementPackageModel.external_id == key[2],
                ProcurementPackageModel.fiscal_year == key[3],
            ))
            if row is None:
                row = ProcurementPackageModel(
                    id=f"pkg_{_stable_id(*map(str, key))}", source=package.source, track=package.track.value,
                    external_id=package.external_id, rup_id=package.rup_id, tender_id=package.tender_id,
                    package_name=package.package_name, description=package.description, organization=package.organization,
                    satker=package.satker, location=package.location, procurement_type=package.procurement_type,
                    procurement_method=package.procurement_method, fiscal_year=package.fiscal_year,
                    budget_amount=package.budget_amount, hps_amount=package.hps_amount, contract_type=package.contract_type,
                    local_content_flag=package.local_content_flag, small_business_flag=package.small_business_flag,
                    source_url=package.source_url, first_seen_at=now, last_seen_at=now,
                    current_stage_code=package.current_stage_code, current_stage_label=package.current_stage_label,
                    current_contract_status=package.contract_status, raw_snapshot_id=snapshot_id or package.raw_snapshot_id,
                )
                session.add(row)
                session.add(ProcurementEventModel(
                    id=f"evt_{uuid.uuid4().hex}", package_id=row.id, event_type="package_seen",
                    event_code=package.current_stage_code, new_value=package.current_stage_label or package.contract_status,
                    event_at=now, observed_at=now, source_snapshot_id=snapshot_id or package.raw_snapshot_id,
                ))
            else:
                transitions = []
                changes = package_changes(row, package)
                stage_changed = 'current_stage_code' in changes or 'current_stage_label' in changes
                if stage_changed:
                    transitions.append(("stage_changed", row.current_stage_code, changes.get('current_stage_code', row.current_stage_code), changes.get('current_stage_label', row.current_stage_label)))
                if _present(package.contract_status) and row.current_contract_status != package.contract_status:
                    transitions.append(("contract_status_changed", row.current_contract_status, package.contract_status, package.contract_status))
                for event_type, old, new, event_code in transitions:
                    session.add(ProcurementEventModel(
                        id=f"evt_{uuid.uuid4().hex}", package_id=row.id, event_type=event_type,
                        event_code=event_code, old_value=old, new_value=new, event_at=now,
                        observed_at=now, source_snapshot_id=snapshot_id or package.raw_snapshot_id,
                    ))
                for field in (
                    "rup_id", "tender_id", "package_name", "description", "organization", "satker", "location",
                    "procurement_type", "procurement_method", "budget_amount", "hps_amount", "contract_type",
                    "local_content_flag", "small_business_flag", "source_url",
                ):
                    value = getattr(package, field)
                    if _present(value):
                        setattr(row, field, value)
                if _present(package.current_stage_code):
                    row.current_stage_code = package.current_stage_code
                if _present(package.current_stage_label):
                    row.current_stage_label = package.current_stage_label
                if _present(package.contract_status):
                    row.current_contract_status = package.contract_status
                if changes:
                    row.raw_snapshot_id = snapshot_id or package.raw_snapshot_id or row.raw_snapshot_id
                row.last_seen_at = now
            session.commit()
            return row.id

    def save_packages(self, packages: Iterable[ProcurementPackage], *, run_id: str | None = None) -> IngestionStats:
        stats = IngestionStats()
        for package in packages:
            stats.seen += 1
            try:
                with Session(self.engine) as session:
                    existing = session.scalar(select(ProcurementPackageModel).where(
                        ProcurementPackageModel.source == package.source,
                        ProcurementPackageModel.track == package.track.value,
                        ProcurementPackageModel.external_id == package.external_id,
                        ProcurementPackageModel.fiscal_year == package.fiscal_year,
                    ))
                    changed = existing is None or bool(package_changes(existing, package))
                snapshot_id = self.save_snapshot(
                    package=package,
                    payload=json.dumps(package.model_dump(mode="json", exclude={'raw_snapshot_id'}), sort_keys=True),
                    run_id=run_id,
                    action="normalized_package",
                ) if changed else None
                package_id = self.upsert_package(package, run_id=run_id, snapshot_id=snapshot_id)
                stats.inserted += 1 if existing is None else 0
                stats.updated += 1 if existing is not None and changed else 0
                stats.unchanged += 1 if existing is not None and not changed else 0
            except Exception:
                stats.rejected += 1
        return stats
