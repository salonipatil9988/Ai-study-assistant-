from datetime import datetime, timezone

from extensions import db


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    title = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(120))
    content = db.Column(db.Text, nullable=False)
    ai_summary = db.Column(db.Text)
    ai_confuser = db.Column(db.Text)
    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship("User", back_populates="notes")
