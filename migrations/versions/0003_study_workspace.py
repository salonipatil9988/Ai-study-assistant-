"""Add persistent tutor sessions and structured PYQ insights.

Revision ID: 0003_study_workspace
Revises: 0002_user_accounts
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_study_workspace"
down_revision = "0002_user_accounts"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("notes", sa.Column("subject", sa.String(length=120), nullable=True))
    op.add_column("pyq_analyses", sa.Column("exam_name", sa.String(length=255), nullable=True))
    op.add_column("pyq_analyses", sa.Column("academic_level", sa.String(length=255), nullable=True))
    op.add_column("pyq_analyses", sa.Column("year_range", sa.String(length=100), nullable=True))
    op.add_column(
        "pyq_analyses",
        sa.Column("question_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("pyq_analyses", sa.Column("trend_summary", sa.Text(), nullable=True))
    op.add_column("pyq_analyses", sa.Column("confidence_note", sa.Text(), nullable=True))
    op.add_column(
        "pyq_analyses",
        sa.Column("topics_json", sa.JSON(), nullable=True),
    )
    op.add_column(
        "pyq_analyses",
        sa.Column("practice_questions", sa.JSON(), nullable=True),
    )
    op.execute("UPDATE pyq_analyses SET topics_json = '[]' WHERE topics_json IS NULL")
    op.execute(
        "UPDATE pyq_analyses SET practice_questions = '[]' "
        "WHERE practice_questions IS NULL"
    )
    op.alter_column(
        "pyq_analyses",
        "topics_json",
        existing_type=sa.JSON(),
        nullable=False,
    )
    op.alter_column(
        "pyq_analyses",
        "practice_questions",
        existing_type=sa.JSON(),
        nullable=False,
    )
    op.create_table(
        "chat_threads",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("context_note_ids", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_chat_threads_user_id_users", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_chat_threads"),
    )
    op.create_index("ix_chat_threads_user_id", "chat_threads", ["user_id"])
    op.create_index("ix_chat_threads_updated_at", "chat_threads", ["updated_at"])
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["thread_id"],
            ["chat_threads.id"],
            name="fk_chat_messages_thread_id_chat_threads",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_chat_messages"),
    )
    op.create_index("ix_chat_messages_thread_id", "chat_messages", ["thread_id"])


def downgrade():
    op.drop_index("ix_chat_messages_thread_id", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_chat_threads_updated_at", table_name="chat_threads")
    op.drop_index("ix_chat_threads_user_id", table_name="chat_threads")
    op.drop_table("chat_threads")
    op.drop_column("pyq_analyses", "practice_questions")
    op.drop_column("pyq_analyses", "topics_json")
    op.drop_column("pyq_analyses", "confidence_note")
    op.drop_column("pyq_analyses", "trend_summary")
    op.drop_column("pyq_analyses", "question_count")
    op.drop_column("pyq_analyses", "year_range")
    op.drop_column("pyq_analyses", "academic_level")
    op.drop_column("pyq_analyses", "exam_name")
    op.drop_column("notes", "subject")
