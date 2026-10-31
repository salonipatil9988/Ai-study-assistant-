from datetime import datetime, timezone

from extensions import db


class ChatThread(db.Model):
    __tablename__ = "chat_threads"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(160), nullable=False, default="New study session")
    context_note_ids = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        index=True,
    )

    messages = db.relationship(
        "ChatMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ChatMessage.id",
    )


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(
        db.Integer,
        db.ForeignKey("chat_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = db.Column(db.String(16), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sources_json = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    thread = db.relationship("ChatThread", back_populates="messages")
