"""Create SALEP source-of-truth tables.

Revision ID: 0001_source_of_truth
Revises:
"""

from __future__ import annotations

from alembic import op

from app.db.models import Base


revision = "0001_source_of_truth"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Metadata-driven creation keeps this first migration aligned with the
    # typed models. Future migrations should use explicit operations.
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    # Drop only tables owned by SALEP, in dependency-safe order.
    for table_name in (
        "opportunities",
        "procurement_events",
        "procurement_packages",
        "source_documents",
        "scrape_runs",
        "leads",
    ):
        op.drop_table(table_name)

