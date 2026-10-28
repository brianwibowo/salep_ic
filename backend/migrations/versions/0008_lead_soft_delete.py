"""Retain deleted leads, Sales history, and the authenticated deletion actor."""

from alembic import op
import sqlalchemy as sa

revision = "0008_lead_soft_delete"
down_revision = "0007_review_assignment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("leads")}
    for name, column_type in (
        ("deleted_at", sa.DateTime(timezone=True)),
        ("deleted_by_user_id", sa.String(40)),
        ("deleted_by_username", sa.String(120)),
    ):
        if name not in columns:
            op.add_column("leads", sa.Column(name, column_type, nullable=True))
    foreign_keys = {tuple(fk["constrained_columns"]) for fk in sa.inspect(bind).get_foreign_keys("leads")}
    if ("deleted_by_user_id",) not in foreign_keys:
        op.create_foreign_key("fk_leads_deleted_by", "leads", "auth_users", ["deleted_by_user_id"], ["id"], ondelete="SET NULL")
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("leads")}
    if "ix_leads_active_created_at" not in indexes:
        op.create_index("ix_leads_active_created_at", "leads", ["created_at"],
                        postgresql_where=sa.text("deleted_at IS NULL"))


def downgrade() -> None:
    # Removing tombstones would silently make deleted leads visible again.
    raise RuntimeError("Soft-delete tombstones must be retained; automatic downgrade is not supported")
