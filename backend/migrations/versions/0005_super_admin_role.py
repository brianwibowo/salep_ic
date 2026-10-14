"""Allow super_admin role for auth users."""

from alembic import op

revision = "0005_super_admin_role"
down_revision = "0004_sales_status_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_auth_user_role",
        "auth_users",
        type_="check",
    )
    op.create_check_constraint(
        "ck_auth_user_role",
        "auth_users",
        "role IN ('marketing', 'sales', 'super_admin')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_auth_user_role",
        "auth_users",
        type_="check",
    )
    op.create_check_constraint(
        "ck_auth_user_role",
        "auth_users",
        "role IN ('marketing', 'sales')",
    )