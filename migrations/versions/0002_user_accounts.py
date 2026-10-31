"""Add user accounts and private data ownership.

Revision ID: 0002_user_accounts
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_user_accounts"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )

    op.add_column("notes", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_notes_user_id", "notes", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_notes_user_id_users", "notes", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )

    op.add_column("pyq_analyses", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_pyq_analyses_user_id", "pyq_analyses", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_pyq_analyses_user_id_users",
        "pyq_analyses",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("fk_pyq_analyses_user_id_users", "pyq_analyses", type_="foreignkey")
    op.drop_index("ix_pyq_analyses_user_id", table_name="pyq_analyses")
    op.drop_column("pyq_analyses", "user_id")
    op.drop_constraint("fk_notes_user_id_users", "notes", type_="foreignkey")
    op.drop_index("ix_notes_user_id", table_name="notes")
    op.drop_column("notes", "user_id")
    op.drop_table("users")
