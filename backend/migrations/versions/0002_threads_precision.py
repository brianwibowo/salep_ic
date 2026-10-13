"""Add Threads quality provenance fields and LLM analysis cache."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision = "0002_threads_precision"
down_revision = "0001_source_of_truth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in inspect(bind).get_columns("leads")}
    columns = {
        "canonical_post_id": sa.Column("canonical_post_id", sa.String(length=255), nullable=True),
        "deterministic_relevance_score": sa.Column("deterministic_relevance_score", sa.Integer(), server_default="0", nullable=False),
        "deterministic_relevance_label": sa.Column("deterministic_relevance_label", sa.String(length=40), server_default="unreviewed", nullable=False),
        "deterministic_relevance_reason": sa.Column("deterministic_relevance_reason", sa.Text(), nullable=True),
        "spam_label": sa.Column("spam_label", sa.String(length=40), server_default="unknown", nullable=False),
        "spam_score": sa.Column("spam_score", sa.Integer(), server_default="0", nullable=False),
        "is_spam": sa.Column("is_spam", sa.Boolean(), server_default=sa.false(), nullable=False),
        "quality_flags": sa.Column("quality_flags", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
    }
    for name, column in columns.items():
        if name not in existing:
            op.add_column("leads", column)
    indexes = {index["name"] for index in inspect(bind).get_indexes("leads")}
    if "ix_leads_canonical_post_id" not in indexes:
        op.create_index("ix_leads_canonical_post_id", "leads", ["canonical_post_id"])

    tables = set(inspect(bind).get_table_names())
    if "llm_analysis_cache" not in tables:
        op.create_table(
            "llm_analysis_cache",
        sa.Column("cache_key", sa.String(length=128), primary_key=True),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("prompt_version", sa.String(length=80), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hit_count", sa.Integer(), server_default="0", nullable=False),
        sa.UniqueConstraint("content_hash", "model_name", "prompt_version", name="uq_llm_cache_content_model_prompt"),
        )
    cache_indexes = {index["name"] for index in inspect(bind).get_indexes("llm_analysis_cache")}
    if "ix_llm_analysis_cache_content_hash" not in cache_indexes:
        op.create_index("ix_llm_analysis_cache_content_hash", "llm_analysis_cache", ["content_hash"])


def downgrade() -> None:
    op.drop_index("ix_llm_analysis_cache_content_hash", table_name="llm_analysis_cache")
    op.drop_table("llm_analysis_cache")
    op.drop_index("ix_leads_canonical_post_id", table_name="leads")
    for column in (
        "quality_flags", "is_spam", "spam_score", "spam_label",
        "deterministic_relevance_reason", "deterministic_relevance_label",
        "deterministic_relevance_score", "canonical_post_id",
    ):
        op.drop_column("leads", column)

