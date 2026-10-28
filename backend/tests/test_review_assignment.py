"""Review/assignment atomicity, authorization, and real PostgreSQL contention.

Set SALEP_TEST_POSTGRES_URL to an isolated disposable database to run the
PostgreSQL cases. Every case owns and removes its own random schema.
"""

import os
import uuid
import importlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.agent.schemas import IntentType, LeadRecord
from app.api.routes import leads
from app.core import auth
from app.db.auth_models import AuthBase, AuthUser
from app.db.lead_repository import ReviewConflict, SqlAlchemyLeadRepository
from app.db.models import ActivityLogModel, LeadAssignmentModel, LeadModel
from app.main import app
from app.services.auth_service import AuthStore, hasher

PASSWORD = "review-assignment-test-passphrase"


@pytest.fixture(params=["sqlite", "postgres"])
def workflow(request, tmp_path, monkeypatch):
    root_engine = None
    schema = None
    if request.param == "postgres":
        url = os.getenv("SALEP_TEST_POSTGRES_URL")
        if not url:
            pytest.skip("Set SALEP_TEST_POSTGRES_URL to a disposable PostgreSQL test database")
        root_engine = create_engine(url)
        schema = "test_review_" + uuid.uuid4().hex
        with root_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        url = make_url(url).update_query_dict({"options": f"-csearch_path={schema}"}).render_as_string(hide_password=False)
    else:
        url = f"sqlite:///{tmp_path / 'workflow.db'}"
    monkeypatch.setattr(auth.settings, "app_env", "development")
    repo = SqlAlchemyLeadRepository(url, create_schema=True)
    AuthBase.metadata.create_all(repo.engine)
    hashed = hasher.hash(PASSWORD)
    with Session(repo.engine) as session:
        for user_id, role, active in (
            ("mkt-a", "marketing", True), ("mkt-b", "marketing", True),
            ("sales-a", "sales", True), ("sales-b", "sales", True), ("inactive-sales", "sales", False),
        ):
            session.add(AuthUser(id=user_id, username=user_id, role=role, active=active,
                                 password_hash=hashed, version=1, created_at=0))
        session.commit()
    repo.save_lead(LeadRecord(
        lead_id="lead-review", source="threads", source_url="https://www.threads.net/@test/post/review",
        content="Butuh layanan cloud", matched_keyword="cloud", is_potential_lead=True,
        intent=IntentType.LOOKING_FOR_VENDOR, lead_score=80, confidence=0.9,
    ))
    store = AuthStore(url)
    monkeypatch.setattr(auth, "get_auth_store", lambda: store)
    monkeypatch.setattr(leads, "lead_repository", repo)
    async def no_sheet(*args, **kwargs):
        return True
    monkeypatch.setattr(leads.sheets_service, "append_lead", no_sheet)
    clients = {}
    for user_id in ("mkt-a", "mkt-b", "sales-a", "sales-b"):
        client = TestClient(app)
        token, _ = store.login(user_id, PASSWORD, "testclient")
        client.cookies.set(auth.COOKIE, token)
        clients[user_id] = client
    yield repo, clients
    for client in clients.values():
        client.close()
    store.engine.dispose()
    repo.engine.dispose()
    if root_engine is not None:
        with root_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        root_engine.dispose()


def approve(repo, **overrides):
    args = dict(reviewed_by_user_id="mkt-a", expected_version=0, sales_user_id="sales-a")
    args.update(overrides)
    return repo.update_marketing_status("lead-review", "valid", **args)


def test_review_and_assignment_use_authenticated_actor_and_optional_note(workflow):
    repo, clients = workflow
    response = clients["mkt-a"].patch("/api/v1/leads/lead-review/status", json={
        "marketing_status": "valid", "expected_version": 0, "sales_user_id": "sales-a",
    })
    assert response.status_code == 200, response.text
    lead = response.json()["data"]
    assert lead["marketing_reviewed_by_user_id"] == "mkt-a"
    assert lead["marketing_review_note"] is None
    assert lead["assignment"]["sales_user_id"] == "sales-a"
    assert lead["review_version"] == 1
    with Session(repo.engine) as session:
        audit = session.scalar(select(ActivityLogModel))
        assert audit.user_id == "mkt-a"
        assert audit.old_value["sales_user_id"] is None
        assert audit.new_value["sales_user_id"] == "sales-a"


def test_valid_requires_active_sales_and_cannot_spoof_reviewer(workflow):
    repo, clients = workflow
    endpoint = "/api/v1/leads/lead-review/status"
    base = {"marketing_status": "valid", "expected_version": 0, "sales_user_id": "sales-a"}
    assert clients["mkt-a"].patch(endpoint, json={**base, "reviewed_by_user_id": "mkt-b"}).status_code == 422
    assert clients["mkt-a"].patch(endpoint, json={"marketing_status": "valid", "expected_version": 0}).status_code == 422
    assert clients["mkt-a"].patch(endpoint, json={"marketing_status": "invalid"}).status_code == 422
    for user_id in ("mkt-b", "inactive-sales", "missing"):
        assert clients["mkt-a"].patch(endpoint, json={**base, "sales_user_id": user_id}).status_code == 400
    assert repo.get_lead("lead-review")["review_version"] == 0
    assert clients["sales-a"].get("/api/v1/leads/sales-users").status_code == 403
    users = clients["mkt-a"].get("/api/v1/leads/sales-users").json()["data"]
    assert {user["user_id"] for user in users} == {"sales-a", "sales-b"}


def test_stale_marketing_form_returns_409_without_overwriting(workflow):
    repo, clients = workflow
    approve(repo)
    response = clients["mkt-b"].patch("/api/v1/leads/lead-review/status", json={
        "marketing_status": "valid", "expected_version": 0, "sales_user_id": "sales-b",
    })
    assert response.status_code == 409
    lead = repo.get_lead("lead-review")
    assert lead["marketing_reviewed_by_user_id"] == "mkt-a"
    assert lead["assignment"]["sales_user_id"] == "sales-a"


def test_only_assigned_sales_can_list_view_count_and_update(workflow):
    repo, clients = workflow
    approve(repo)
    for user, expected in (("sales-a", 1), ("sales-b", 0)):
        client = clients[user]
        listing = client.get("/api/v1/leads?role=marketing").json()["data"]
        assert len(listing["items"]) == listing["pagination"]["total"] == expected
        assert client.get("/api/v1/leads/stats").json()["data"]["valid"] == expected
        assert client.get("/api/v1/leads/lead-review").status_code == (200 if expected else 404)
        assert client.patch("/api/v1/leads/lead-review/sales-status", json={
            "sales_status": "Sedang Dihubungi", "note": "Menghubungi via LinkedIn",
        }).status_code == (200 if expected else 404)
    assert clients["sales-b"].get("/api/v1/spse/leads/lead-review/jadwal").status_code == 404


def test_reassignment_retains_history_and_revokes_previous_owner(workflow):
    repo, clients = workflow
    approve(repo)
    second = approve(repo, expected_version=1, sales_user_id="sales-b", reviewed_by_user_id="mkt-b")
    assert second["assignment"]["sales_user_id"] == "sales-b"
    assert clients["sales-a"].get("/api/v1/leads/lead-review").status_code == 404
    # Reconfirming the same recipient must not create a duplicate assignment.
    approve(repo, expected_version=2, sales_user_id="sales-b")
    with Session(repo.engine) as session:
        rows = session.scalars(select(LeadAssignmentModel)).all()
        assert len(rows) == 2
        assert sum(row.unassigned_at is None for row in rows) == 1
    invalid = repo.update_marketing_status("lead-review", "invalid", reviewed_by_user_id="mkt-b", expected_version=3)
    assert invalid["assignment"] is None
    assert clients["sales-b"].get("/api/v1/leads/lead-review").status_code == 404


def test_audit_failure_rolls_back_review_and_assignment(workflow):
    repo, _ = workflow
    def reject_audit(mapper, connection, target):
        raise RuntimeError("simulated audit write failure")
    event.listen(ActivityLogModel, "before_insert", reject_audit)
    try:
        with pytest.raises(RuntimeError, match="simulated"):
            approve(repo)
    finally:
        event.remove(ActivityLogModel, "before_insert", reject_audit)
    lead = repo.get_lead("lead-review")
    assert lead["marketing_status"] == "pending"
    assert lead["review_version"] == 0
    assert lead["assignment"] is None


def test_simultaneous_marketing_reviews_have_one_winner(workflow):
    repo, _ = workflow
    if repo.engine.dialect.name != "postgresql":
        # SQLite does not implement PostgreSQL row locking; contention is tested on PG.
        return
    barrier = Barrier(2)
    def submit(marketer, recipient):
        barrier.wait(timeout=10)
        try:
            return approve(repo, reviewed_by_user_id=marketer, sales_user_id=recipient)
        except ReviewConflict:
            return "conflict"
    with ThreadPoolExecutor(max_workers=2) as executor:
        tasks = [executor.submit(submit, "mkt-a", "sales-a"), executor.submit(submit, "mkt-b", "sales-b")]
        results = [task.result(timeout=15) for task in tasks]
    assert sum(result == "conflict" for result in results) == 1
    with Session(repo.engine) as session:
        assert session.scalar(select(func.count()).select_from(LeadAssignmentModel)) == 1
        assert session.scalar(select(func.count()).select_from(ActivityLogModel)) == 1
    assert repo.get_lead("lead-review")["review_version"] == 1


def test_migration_preserves_existing_assignments_and_backfills_snapshot(workflow, monkeypatch):
    repo, _ = workflow
    if repo.engine.dialect.name != "postgresql":
        return
    # All DDL stays inside this test's randomly named, disposable schema.
    with repo.engine.begin() as connection:
        connection.execute(text("DROP TABLE lead_assignments"))
        connection.execute(text("ALTER TABLE leads DROP COLUMN review_version"))
        migration = importlib.import_module("migrations.versions.0007_review_assignment")
        monkeypatch.setattr(migration, "op", Operations(MigrationContext.configure(connection)))
        migration.upgrade()  # Upgrade from the deployed 0006 schema.
        connection.execute(text("""
            INSERT INTO lead_assignments
            (assignment_id, lead_id, sales_user_id, assigned_by_user_id, assigned_at)
            VALUES ('existing-assignment', 'lead-review', 'sales-a', 'mkt-a', CURRENT_TIMESTAMP)
        """))
        connection.execute(text("ALTER TABLE lead_assignments DROP COLUMN sales_username"))
        migration.upgrade()  # Also supports the earlier standalone SQL table.
        migration.upgrade()  # Safe to re-run without losing assignment history.
        result = connection.execute(text("SELECT sales_username FROM lead_assignments")).scalar_one()
        assert result == "sales-a"
    lead = approve(repo)
    assert lead["review_version"] == 1
    assert lead["assignment"]["assignment_id"] == "existing-assignment"


@pytest.mark.parametrize("source", ["threads", "spse"])
def test_marketing_can_track_sales_closing_and_notes(workflow, source):
    repo, clients = workflow
    with Session(repo.engine) as session:
        session.get(LeadModel, "lead-review").source = source
        session.commit()
    approve(repo)
    for status, note in (("Sedang Dihubungi", "Demo dijadwalkan hari Jumat"), ("Closing", "PO sudah diterima, lanjut onboarding")):
        response = clients["sales-a"].patch("/api/v1/leads/lead-review/sales-status", json={"sales_status": status, "note": note})
        assert response.status_code == 200, response.text
    detail = clients["mkt-b"].get("/api/v1/leads/lead-review").json()["data"]
    assert detail["sales_status"] == "Closing"
    assert len(detail["sales_status_logs"]) == 2
    assert detail["sales_status_logs"][-1]["note"] == "PO sudah diterima, lanjut onboarding"
    assert detail["sales_status_logs"][-1]["changed_by"] == "sales-a"
    assert detail["sales_status_logs"][-1]["changed_at"]
    listing = clients["mkt-a"].get("/api/v1/leads", params={"source": source, "sales_status": "Closing"}).json()["data"]
    assert listing["pagination"]["total"] == 1
    assert listing["items"][0]["sales_status_logs"] == detail["sales_status_logs"]


def test_combined_filters_count_pagination_active_owner_and_wib_boundaries(workflow):
    repo, clients = workflow
    rows = [
        ("lead-review", "threads", "valid", "2026-09-30T17:00:00+00:00", "sales-a"),
        ("lead-b", "spse", "valid", "2026-10-15T05:00:00+00:00", "sales-b"),
        ("lead-free", "spse", "valid", "2026-10-31T16:59:59.999999+00:00", None),
        ("lead-pending", "threads", "pending", "2026-10-20T05:00:00+00:00", None),
        ("lead-invalid", "linkedin", "invalid", "2026-10-20T05:00:00+00:00", None),
        ("lead-history", "spse", "valid", "2026-09-30T16:59:59+00:00", "sales-b"),
        ("lead-nov", "spse", "valid", "2026-10-31T17:00:00+00:00", None),
    ]
    for lead_id, source, status, created, owner in rows:
        if lead_id != "lead-review":
            repo.save_lead(LeadRecord(lead_id=lead_id, source=source, source_url=f"https://example.com/{lead_id}", content="Cloud", matched_keyword="cloud", is_potential_lead=True, intent=IntentType.LOOKING_FOR_VENDOR, lead_score=80, confidence=0.9))
        if lead_id == "lead-history":
            repo.update_marketing_status(lead_id, "valid", reviewed_by_user_id="mkt-a", expected_version=0, sales_user_id="sales-a")
        if owner:
            repo.update_marketing_status(lead_id, "valid", reviewed_by_user_id="mkt-a", expected_version=1 if lead_id == "lead-history" else 0, sales_user_id=owner)
        with Session(repo.engine) as session:
            row = session.get(LeadModel, lead_id)
            row.marketing_status = status
            row.created_at = datetime.fromisoformat(created)
            session.commit()
    cases = [
        ({"status": "pending"}, {"lead-pending"}),
        ({"status": "valid", "source": "spse"}, {"lead-b", "lead-free", "lead-history", "lead-nov"}),
        ({"sales_user_id": "sales-a"}, {"lead-review"}),
        ({"sales_user_id": "sales-b"}, {"lead-b", "lead-history"}),
        ({"assignment_status": "unassigned"}, {"lead-free", "lead-nov"}),
        ({"assignment_status": "assigned"}, {"lead-review", "lead-b", "lead-history"}),
        ({"date_from": "2026-10-01", "date_to": "2026-10-31"}, {"lead-review", "lead-b", "lead-free", "lead-pending", "lead-invalid"}),
        ({"date_from": "2026-10-31", "date_to": "2026-10-31"}, {"lead-free"}),
        ({"source": "spse", "status": "valid", "assignment_status": "unassigned", "date_from": "2026-10-01", "date_to": "2026-10-31"}, {"lead-free"}),
        ({"date_from": "2026-01-01", "date_to": "2026-12-31", "source": "social_media"}, {"lead-review", "lead-pending", "lead-invalid"}),
    ]
    for params, expected in cases:
        response = clients["mkt-a"].get("/api/v1/leads", params=params)
        assert response.status_code == 200, response.text
        listing = response.json()["data"]
        assert {lead["lead_id"] for lead in listing["items"]} == expected, params
        assert listing["pagination"]["total"] == len(expected), params
    page = clients["mkt-a"].get("/api/v1/leads", params={"sales_user_id": "sales-b", "limit": 1, "page": 2}).json()["data"]
    assert len(page["items"]) == 1
    assert page["pagination"]["total"] == 2
    for params in ({"sales_user_id": "sales-b"}, {"assignment_status": "unassigned"}):
        restricted = clients["sales-a"].get("/api/v1/leads", params=params).json()["data"]
        assert restricted["items"] == []
        assert restricted["pagination"]["total"] == 0


def test_filter_validation_and_inactive_sales_options(workflow):
    repo, clients = workflow
    for params in (
        {"date_from": "2026-11-01", "date_to": "2026-10-01"},
        {"date_from": "not-a-date"}, {"date_to": "1899-12-31"},
        {"assignment_status": "anything"},
        {"assignment_status": "unassigned", "sales_user_id": "sales-a"},
        {"assignment_status": "unassigned", "status": "pending"},
    ):
        assert clients["mkt-a"].get("/api/v1/leads", params=params).status_code == 422
    users = clients["mkt-a"].get("/api/v1/leads/sales-users?include_inactive=true").json()["data"]
    assert {user["user_id"] for user in users} == {"sales-a", "sales-b", "inactive-sales"}
    assert next(user for user in users if user["user_id"] == "inactive-sales")["active"] is False
