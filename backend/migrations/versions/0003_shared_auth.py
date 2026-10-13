"""Account authentication and shared, revocable sessions. Legacy tokens expire at cutover."""
from alembic import op
import sqlalchemy as sa

revision = '0003_shared_auth'
down_revision = '0002_threads_precision'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('auth_users',
        sa.Column('id', sa.String(40), primary_key=True),
        sa.Column('username', sa.String(120), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.Float(), nullable=False),
        sa.CheckConstraint("role IN ('marketing', 'sales')", name='ck_auth_user_role'))
    op.create_table('auth_sessions',
        sa.Column('token_hash', sa.String(64), primary_key=True),
        sa.Column('user_id', sa.String(40), sa.ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.Float(), nullable=False),
        sa.Column('expires_at', sa.Float(), nullable=False))
    op.create_index('ix_auth_sessions_user_id', 'auth_sessions', ['user_id'])
    op.create_index('ix_auth_sessions_expires_at', 'auth_sessions', ['expires_at'])
    op.create_table('auth_login_buckets',
        sa.Column('key', sa.String(64), primary_key=True),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.Float(), nullable=False))
    op.create_index('ix_auth_login_buckets_expires_at', 'auth_login_buckets', ['expires_at'])


def downgrade():
    op.drop_table('auth_login_buckets')
    op.drop_table('auth_sessions')
    op.drop_table('auth_users')
