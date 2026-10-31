from datetime import datetime, timezone

from sqlalchemy import or_, select

from extensions import db
from models.note import Note


def list_notes(user_id: int, search: str = "") -> list[Note]:
    statement = select(Note).where(Note.user_id == user_id)
    if search:
        statement = statement.where(
            or_(Note.title.ilike(f"%{search}%"), Note.content.ilike(f"%{search}%"))
        )
    return list(
        db.session.scalars(statement.order_by(Note.created_at.desc(), Note.id.desc()))
    )


def get_owned_note(note_id: int, user_id: int) -> Note | None:
    return db.session.scalar(
        select(Note).where(Note.id == note_id, Note.user_id == user_id)
    )


def create_note(user_id: int, title: str, content: str, subject: str = "") -> Note:
    note = Note(user_id=user_id, title=title, content=content, subject=subject or None)
    db.session.add(note)
    db.session.commit()
    return note


def update_note(note: Note, title: str, content: str, subject: str = "") -> Note:
    note.title = title
    note.subject = subject or None
    note.content = content
    note.ai_summary = None
    note.ai_confuser = None
    db.session.commit()
    return note


def save_note_material(note: Note, takeaways: str, confuser: str) -> None:
    note.ai_summary = takeaways
    note.ai_confuser = confuser
    db.session.commit()


def delete_note(note: Note) -> None:
    db.session.delete(note)
    db.session.commit()


def serialize_note(note: Note) -> dict[str, object]:
    created_at = note.created_at
    if isinstance(created_at, datetime) and created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return {
        "id": note.id,
        "title": note.title,
        "subject": note.subject,
        "content": note.content,
        "ai_summary": note.ai_summary,
        "ai_confuser": note.ai_confuser,
        "created_at": created_at.isoformat() if created_at else None,
    }
