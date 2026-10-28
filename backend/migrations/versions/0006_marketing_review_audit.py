"""Persist Marketing reviewer identity and lead validation audit events."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import INET


revision = "0006_marketing_review_audit"
down_revision = "0005_super_admin_role"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("leads")}
    additions = {
        "marketing_reviewed_by_user_id": sa.Column("marketing_reviewed_by_user_id", sa.String(length=40), nullable=True),
        "marketing_reviewed_by_username": sa.Column("marketing_reviewed_by_username", sa.String(length=120), nullable=True),
        "marketing_reviewed_at": sa.Column("marketing_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        "marketing_review_note": sa.Column("marketing_review_note", sa.Text(), nullable=True),
    }
    for name, column in additions.items():
        if name not in columns:
            op.add_column("leads", column)

    constraints = {item["name"] for item in inspect(bind).get_foreign_keys("leads")}
    if "fk_leads_marketing_reviewer" not in constraints:
        op.create_foreign_key(
            "fk_leads_marketing_reviewer",
            "leads",
            "auth_users",
            ["marketing_reviewed_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )

    indexes = {index["name"] for index in inspect(bind).get_indexes("leads")}
    if "ix_leads_marketing_reviewer" not in indexes:
        op.create_index(
            "ix_leads_marketing_reviewer",
            "leads",
            ["marketing_reviewed_by_user_id", "marketing_reviewed_at"],
        )

    if "activity_logs" not in inspect(bind).get_table_names():
        op.create_table(
            "activity_logs",
            sa.Column("activity_id", sa.String(length=80), primary_key=True),
            sa.Column("user_id", sa.String(length=40), nullable=True),
            sa.Column("action", sa.String(length=40), nullable=False),
            sa.Column("entity_type", sa.String(length=80), nullable=True),
            sa.Column("entity_id", sa.String(length=120), nullable=True),
            sa.Column("api", sa.Text(), nullable=True),
            sa.Column("http_method", sa.String(length=10), nullable=True),
            sa.Column("http_status", sa.Integer(), nullable=True),
            sa.Column("request_id", sa.String(length=100), nullable=True),
            sa.Column("duration_ms", sa.Integer(), nullable=True),
            sa.Column("ip_address", INET(), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("old_value", sa.JSON(), nullable=True),
            sa.Column("new_value", sa.JSON(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    activity_indexes = {index["name"] for index in inspect(bind).get_indexes("activity_logs")}
    if "ix_activity_logs_entity" not in activity_indexes:
        op.create_index("ix_activity_logs_entity", "activity_logs", ["entity_type", "entity_id", "created_at"])
    if "ix_activity_logs_api_created" not in activity_indexes:
        op.create_index("ix_activity_logs_api_created", "activity_logs", ["api", "created_at"])


def downgrade() -> None:
    bind = op.get_bind()
    # Preserve audit records, including tables created by standalone SQL before
    # this revision. Audit history must survive an application rollback.

    indexes = {index["name"] for index in inspect(bind).get_indexes("leads")}
    if "ix_leads_marketing_reviewer" in indexes:
        op.drop_index("ix_leads_marketing_reviewer", table_name="leads")
    constraints = {item["name"] for item in inspect(bind).get_foreign_keys("leads")}
    if "fk_leads_marketing_reviewer" in constraints:
        op.drop_constraint("fk_leads_marketing_reviewer", "leads", type_="foreignkey")
    columns = {column["name"] for column in inspect(bind).get_columns("leads")}
    for name in (
        "marketing_review_note",
        "marketing_reviewed_at",
        "marketing_reviewed_by_username",
        "marketing_reviewed_by_user_id",
    ):
        if name in columns:
            op.drop_column("leads", name)
