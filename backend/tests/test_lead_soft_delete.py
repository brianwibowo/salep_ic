"""Soft-delete visibility, retained history, replay safety and PostgreSQL locks."""

import asyncio
import importlib
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import AsyncMock

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import event, func, select, text
from sqlalchemy.orm import Session

from app.agent.schemas import IntentType, LeadAnalysis, LeadRecord, RawLead, SearchRequest
from app.db.models import ActivityLogModel, LeadAssignmentModel, LeadModel
from app.services import lead_service, spse_service
from tests.test_review_assignment import approve, workflow


def test_delete_retains_lead_history_actor_and_hides_every_active_path(workflow):
    repo, clients = workflow
    approved = approve(repo)
    assert clients["sales-a"].patch("/api/v1/leads/lead-review/sales-status", json={
        "sales_status": "Closing", "note": "PO diterima; onboarding Senin",
    }).status_code == 200
    before = repo.get_lead("lead-review")
    response = clients["mkt-b"].request("DELETE", "/api/v1/leads/lead-review",
        json={"deleted_by_user_id": "mkt-a"}, headers={"x-request-id": "soft-delete-test"})
    assert response.status_code == 200, response.text
    with Session(repo.engine) as session:
        row = session.get(LeadModel, "lead-review")
        assert row is not None and row.deleted_at is not None
        assert row.deleted_by_user_id == row.deleted_by_username == "mkt-b"
        assert row.sales_status_logs == before["sales_status_logs"]
        assert row.marketing_reviewed_by_user_id == "mkt-a"
        assignment = session.get(LeadAssignmentModel, approved["assignment"]["assignment_id"])
        assert assignment.sales_user_id == "sales-a"
        assert assignment.unassigned_at is None
        audit = session.scalar(select(ActivityLogModel).where(ActivityLogModel.action == "SOFT_DELETE_LEAD"))
        assert audit.user_id == "mkt-b"
        assert audit.request_id == "soft-delete-test"
        assert audit.old_value == {"deleted_at": None}
        assert audit.new_value["deleted_at"]
        assert audit.metadata_json["deleted_by_username"] == "mkt-b"
    assert repo.get_lead("lead-review") is None
    for user in ("mkt-a", "sales-a"):
        client = clients[user]
        listing = client.get("/api/v1/leads?assignment_status=assigned&sales_user_id=sales-a").json()["data"]
        assert listing["items"] == [] and listing["pagination"]["total"] == 0
        assert client.get("/api/v1/leads/stats").json()["data"]["valid"] == 0
        assert client.get("/api/v1/leads/lead-review").status_code == 404
        assert client.get("/api/v1/spse/leads/lead-review/jadwal").status_code == 404
    assert clients["mkt-a"].patch("/api/v1/leads/lead-review/status", json={
        "marketing_status": "valid", "expected_version": 1, "sales_user_id": "sales-b",
    }).status_code == 404
    assert clients["sales-a"].patch("/api/v1/leads/lead-review/sales-status", json={
        "sales_status": "Batal", "note": "Tidak boleh mengubah lead terhapus",
    }).status_code == 404


def test_only_marketing_can_delete_and_repeated_delete_keeps_original_actor(workflow):
    repo, clients = workflow
    assert clients["sales-a"].delete("/api/v1/leads/lead-review").status_code == 403
    assert clients["mkt-a"].delete("/api/v1/leads/lead-review").status_code == 200
    with Session(repo.engine) as session:
        deleted_at = session.get(LeadModel, "lead-review").deleted_at
    assert clients["mkt-b"].delete("/api/v1/leads/lead-review").status_code == 404
    assert clients["mkt-a"].delete("/api/v1/leads/missing").status_code == 404
    with Session(repo.engine) as session:
        row = session.get(LeadModel, "lead-review")
        assert row.deleted_by_user_id == "mkt-a" and row.deleted_at == deleted_at
        assert session.scalar(select(func.count()).select_from(ActivityLogModel)) == 1


def test_audit_failure_rolls_back_soft_delete(workflow):
    repo, clients = workflow
    def reject_delete_audit(mapper, connection, target):
        if target.action == "SOFT_DELETE_LEAD":
            raise RuntimeError("simulated delete audit failure")
    event.listen(ActivityLogModel, "before_insert", reject_delete_audit)
    try:
        response = clients["mkt-a"].delete("/api/v1/leads/lead-review")
        assert response.status_code == 500
        assert "simulated" not in response.text
    finally:
        event.remove(ActivityLogModel, "before_insert", reject_delete_audit)
    assert repo.get_lead("lead-review")["deleted_at"] is None
    assert repo.count_leads() == 1
    with Session(repo.engine) as session:
        assert session.scalar(select(func.count()).select_from(ActivityLogModel)) == 0


def test_scraper_replay_cannot_restore_or_mutate_deleted_evidence(workflow):
    repo, clients = workflow
    with Session(repo.engine) as session:
        session.get(LeadModel, "lead-review").canonical_post_id = "canonical-deleted-post"
        session.commit()
    original = repo.get_lead("lead-review")
    clients["mkt-a"].delete("/api/v1/leads/lead-review")
    for lead_id, url in (("new-id", original["source_url"]), ("another-id", "https://www.threads.com/@test/post/review")):
        replay = LeadRecord(lead_id=lead_id, source="threads", source_url=url,
            content="Changed text from scraper", matched_keyword="cloud", is_potential_lead=True,
            intent=IntentType.LOOKING_FOR_VENDOR, lead_score=90, confidence=0.9,
            canonical_post_id="canonical-deleted-post")
        saved = repo.save_lead(replay)
        assert saved["deleted_at"] and saved["lead_id"] == replay.lead_id == "lead-review"
        assert saved["content"] == original["content"]
    assert repo.get_leads() == []
    with Session(repo.engine) as session:
        assert session.scalar(select(func.count()).select_from(LeadModel)) == 1


@pytest.mark.parametrize("source", ["threads", "spse"])
def test_deleted_leads_are_not_returned_by_rediscovery(workflow, monkeypatch, source):
    repo, clients = workflow
    before = repo.get_lead("lead-review")
    clients["mkt-a"].delete("/api/v1/leads/lead-review")
    raw = RawLead(source=source, source_url=before["source_url"], content=before["content"], matched_keyword="cloud")
    if source == "spse":
        monkeypatch.setattr(spse_service, "lead_repository", repo)
        monkeypatch.setattr(spse_service.SPSESourceAdapter, "search", AsyncMock(return_value=[raw]))
        response = asyncio.run(spse_service.discover_spse_tenders(["cloud"]))
        assert response["matched"] == 1 and response["saved"] == 0 and response["leads"] == []
    else:
        monkeypatch.setattr(lead_service, "lead_repository", repo)
        monkeypatch.setattr(lead_service, "search_sources", AsyncMock(return_value=[raw]))
        monkeypatch.setattr(lead_service, "analyze_lead", AsyncMock(return_value=LeadAnalysis(
            is_potential_lead=True, intent=IntentType.LOOKING_FOR_VENDOR, lead_score=80, confidence=0.9)))
        append = AsyncMock(return_value=0)
        monkeypatch.setattr(lead_service.sheets_service, "append_leads", append)
        response = asyncio.run(lead_service.run_search(SearchRequest(
            keywords=["cloud"], start_date="2026-10-01", end_date="2026-10-23", sources=["threads"], limit=1)))
        assert response.total_found == 1 and response.leads == [] and response.qualified == 0
        append.assert_awaited_once_with([])
        monkeypatch.setattr(lead_service, "extract_post_from_url", AsyncMock(return_value=raw))
        with pytest.raises(ValueError, match="sudah dihapus"):
            asyncio.run(lead_service.analyze_and_save_url(raw.source_url))


def test_historical_sheet_endpoint_suppresses_deleted_references(workflow, monkeypatch):
    repo, clients = workflow
    url = repo.get_lead("lead-review")["source_url"]
    clients["mkt-a"].delete("/api/v1/leads/lead-review")
    monkeypatch.setattr(lead_service.sheets_service, "get_recent_leads", AsyncMock(return_value=[
        {"Link Postingan": url}, {"source_url": url}, {"Link Postingan": "https://example.com/other"},
    ]))
    response = clients["mkt-a"].get("/api/v1/leads/recent")
    assert response.status_code == 200, response.text
    assert response.json()["data"] == [{"Link Postingan": "https://example.com/other"}]


def test_soft_delete_migration_preserves_existing_rows(workflow, monkeypatch):
    repo, clients = workflow
    if repo.engine.dialect.name != "postgresql":
        return
    with repo.engine.begin() as connection:
        for name in ("deleted_at", "deleted_by_user_id", "deleted_by_username"):
            connection.execute(text(f"ALTER TABLE leads DROP COLUMN {name}"))
        migration = importlib.import_module("migrations.versions.0008_lead_soft_delete")
        monkeypatch.setattr(migration, "op", Operations(MigrationContext.configure(connection)))
        migration.upgrade()
        migration.upgrade()
        assert connection.execute(text("SELECT count(*) FROM leads WHERE deleted_at IS NULL")).scalar_one() == 1
        with pytest.raises(RuntimeError, match="tombstones"):
            migration.downgrade()
    assert clients["mkt-a"].delete("/api/v1/leads/lead-review").status_code == 200


def test_concurrent_delete_is_recorded_once(workflow):
    repo, _ = workflow
    if repo.engine.dialect.name != "postgresql":
        return
    barrier = Barrier(2)
    def submit(actor):
        barrier.wait(timeout=10)
        return repo.delete_lead("lead-review", deleted_by_user_id=actor)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(submit, actor) for actor in ("mkt-a", "mkt-b")]
        assert sorted(future.result(timeout=15) for future in futures) == [False, True]
    with Session(repo.engine) as session:
        assert session.scalar(select(func.count()).select_from(LeadModel)) == 1
        assert session.scalar(select(func.count()).select_from(ActivityLogModel)) == 1
