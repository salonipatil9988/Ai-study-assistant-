"""Create the original notes and PYQ tables.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_confuser", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_notes"),
    )
    op.create_table(
        "pyq_analyses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subject_name", sa.String(length=255), nullable=False),
        sa.Column("raw_pyqs", sa.Text(), nullable=False),
        sa.Column("repeated_topics", sa.Text(), nullable=False),
        sa.Column("exam_strategy", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_pyq_analyses"),
    )


def downgrade():
    op.drop_table("pyq_analyses")
    op.drop_table("notes")
