from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    notes = db.relationship("Note", back_populates="user", cascade="all, delete-orphan")
    pyq_analyses = db.relationship(
        "PyqAnalysis", back_populates="user", cascade="all, delete-orphan"
    )
    chat_threads = db.relationship(
        "ChatThread", backref="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
