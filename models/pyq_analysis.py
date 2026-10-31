from datetime import datetime, timezone

from extensions import db


class PyqAnalysis(db.Model):
    __tablename__ = "pyq_analyses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    subject_name = db.Column(db.String(255), nullable=False)
    exam_name = db.Column(db.String(255))
    academic_level = db.Column(db.String(255))
    year_range = db.Column(db.String(100))
    question_count = db.Column(db.Integer, nullable=False, default=0)
    raw_pyqs = db.Column(db.Text, nullable=False)
    repeated_topics = db.Column(db.Text, nullable=False)
    exam_strategy = db.Column(db.Text, nullable=False)
    trend_summary = db.Column(db.Text)
    confidence_note = db.Column(db.Text)
    topics_json = db.Column(db.JSON, nullable=False, default=list)
    practice_questions = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship("User", back_populates="pyq_analyses")
