"""Store timestamped Sales follow-up notes on each lead."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0004_sales_status_logs"
down_revision = "0003_shared_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("leads")}
    if "sales_status_logs" not in columns:
        op.add_column(
            "leads",
            sa.Column("sales_status_logs", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
        )


def downgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("leads")}
    if "sales_status_logs" in columns:
        op.drop_column("leads", "sales_status_logs")
