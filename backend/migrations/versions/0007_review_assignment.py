"""Atomic Marketing review and Sales assignment with optimistic concurrency."""

from alembic import op
import sqlalchemy as sa

revision = "0007_review_assignment"
down_revision = "0006_marketing_review_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("leads")}
    if "review_version" not in columns:
        op.add_column("leads", sa.Column("review_version", sa.Integer(), nullable=False, server_default="0"))

    if "lead_assignments" not in inspector.get_table_names():
        op.create_table(
            "lead_assignments",
            sa.Column("assignment_id", sa.String(80), primary_key=True),
            sa.Column("lead_id", sa.String(80), nullable=False),
            sa.Column("sales_user_id", sa.String(40), nullable=False),
            sa.Column("sales_username", sa.String(120)),
            sa.Column("assigned_by_user_id", sa.String(40), nullable=False),
            sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("unassigned_at", sa.DateTime(timezone=True)),
            sa.Column("unassigned_by_user_id", sa.String(40)),
            sa.Column("unassign_reason", sa.Text()),
            sa.CheckConstraint("unassigned_at IS NULL OR unassigned_at >= assigned_at", name="ck_assignment_dates"),
        )
    elif "sales_username" not in {c["name"] for c in sa.inspect(bind).get_columns("lead_assignments")}:
        # Compatible with the earlier standalone migration.sql.
        op.add_column("lead_assignments", sa.Column("sales_username", sa.String(120)))

    foreign_keys = {tuple(fk["constrained_columns"]) for fk in sa.inspect(bind).get_foreign_keys("lead_assignments")}
    for column, table, target, ondelete in (
        ("lead_id", "leads", "lead_id", "CASCADE"),
        ("sales_user_id", "auth_users", "id", "RESTRICT"),
        ("assigned_by_user_id", "auth_users", "id", "RESTRICT"),
        ("unassigned_by_user_id", "auth_users", "id", "SET NULL"),
    ):
        if (column,) not in foreign_keys:
            op.create_foreign_key(f"fk_assignments_{column}", "lead_assignments", table,
                                  [column], [target], ondelete=ondelete)

    indexes = {i["name"] for i in sa.inspect(bind).get_indexes("lead_assignments")}
    if "uq_lead_active_assignment" not in indexes:
        op.create_index("uq_lead_active_assignment", "lead_assignments", ["lead_id"], unique=True,
                        postgresql_where=sa.text("unassigned_at IS NULL"))
    if "ix_lead_assignments_sales_user" not in indexes:
        op.create_index("ix_lead_assignments_sales_user", "lead_assignments", ["sales_user_id", "unassigned_at"])
    op.execute(sa.text("""
        UPDATE lead_assignments AS a SET sales_username = u.username
        FROM auth_users AS u WHERE a.sales_user_id = u.id AND a.sales_username IS NULL
    """))
    # No automatic owner for legacy valid leads: Marketing must assign them explicitly.


def downgrade() -> None:
    # Deliberately retain assignment history and version tokens. Dropping either
    # would erase ownership evidence or allow stale requests to reuse old versions.
    pass
