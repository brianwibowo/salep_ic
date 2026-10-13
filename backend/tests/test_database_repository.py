"""Smoke tests for the SQLAlchemy repository used by PostgreSQL in production."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.agent.schemas import IntentType, LeadRecord
from app.db.lead_repository import SqlAlchemyLeadRepository
from app.db.procurement_repository import ProcurementRepository
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import ProcurementPackageModel
from app.domain.procurement import ProcurementPackage, ProcurementTrack


def make_lead() -> LeadRecord:
    return LeadRecord(
        lead_id="lead_pg_fixture",
        source="spse",
        source_url="https://spse.inaproc.id/nasional/lelang/10000000001/pengumumanlelang",
        author_name="Instansi Contoh",
        author_profile_url="https://spse.inaproc.id/nasional",
        published_at=datetime.now(timezone.utc),
        matched_keyword="managed service",
        content="Pengadaan managed service dan monitoring server",
        is_potential_lead=True,
        intent=IntentType.LOOKING_FOR_VENDOR,
        needs=["managed service"],
        pain_points=["monitoring"],
        recommended_services=[],
        lead_score=80,
        confidence=0.9,
        evidence=["managed service"],
        marketing_status="pending",
        sales_status="Belum Dihubungi",
    )


def test_sqlalchemy_repository_is_idempotent_and_preserves_review_status(tmp_path) -> None:
    repository = SqlAlchemyLeadRepository(
        f"sqlite:///{tmp_path / 'salep.db'}",
        create_schema=True,
    )
    lead = make_lead()

    first = repository.save_lead(lead)
    assert first["lead_id"] == "lead_pg_fixture"
    assert repository.count_leads(role="marketing") == 1

    assert repository.update_marketing_status("lead_pg_fixture", "valid") is not None
    lead.content = "Updated managed service package"
    second = repository.save_lead(lead)
    assert second["content"] == "Updated managed service package"
    assert second["marketing_status"] == "valid"
    assert repository.count_leads(role="sales") == 1


def test_procurement_repository_emits_status_transition(tmp_path) -> None:
    repository = ProcurementRepository(f"sqlite:///{tmp_path / 'procurement.db'}", create_schema=True)
    package = ProcurementPackage(
        source="spse", track=ProcurementTrack.TENDER, external_id="t-1", tender_id="t-1",
        package_name="Managed Service", fiscal_year=2026,
        current_stage_code="proposal_upload", current_stage_label="Upload Dokumen Penawaran",
        source_url="https://spse.inaproc.id/nasional/lelang/t-1/pengumumanlelang",
    )
    repository.save_packages([package])
    repository.save_packages([package.model_copy(update={
        "current_stage_code": "tender_completed", "current_stage_label": "Tender Sudah Selesai",
        "contract_status": "Selesai",
    })])
    from app.db.models import ProcurementEventModel
    with Session(repository.engine) as session:
        all_events = session.scalars(select(ProcurementEventModel)).all()
    assert any(event.event_type == "stage_changed" for event in all_events)
    assert any(event.event_type == "contract_status_changed" for event in all_events)


def test_procurement_replay_keeps_richer_fields_and_counts_unchanged(tmp_path) -> None:
    repository = ProcurementRepository(f"sqlite:///{tmp_path / 'procurement.db'}", create_schema=True)
    complete = ProcurementPackage(
        source="spse", track=ProcurementTrack.TENDER, external_id="t-replay", tender_id="t-replay",
        package_name="Managed Service", organization="Instansi Kaya Data", fiscal_year=2026,
        current_stage_code="proposal_upload", current_stage_label="Upload Dokumen Penawaran",
        source_url="https://spse.inaproc.id/nasional/lelang/t-replay/pengumumanlelang",
    )
    assert repository.save_packages([complete]).inserted == 1
    sparse = complete.model_copy(update={"organization": None, "current_stage_code": None, "current_stage_label": None})
    stats = repository.save_packages([sparse])
    assert stats.unchanged == 1
    with Session(repository.engine) as session:
        row = session.scalar(select(ProcurementPackageModel).where(ProcurementPackageModel.external_id == "t-replay"))
        assert row is not None
        assert row.organization == "Instansi Kaya Data"
        assert row.current_stage_code == "proposal_upload"

