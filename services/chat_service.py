import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from extensions import db
from models.chat_thread import ChatMessage, ChatThread
from models.note import Note
from models.pyq_analysis import PyqAnalysis

WORD_PATTERN = re.compile(r"[a-zA-Z0-9]{3,}")


def create_thread(user_id: int, note_ids: list[int] | None = None) -> ChatThread:
    thread = ChatThread(
        user_id=user_id,
        title="New study session",
        context_note_ids=note_ids or [],
    )
    db.session.add(thread)
    db.session.commit()
    return thread


def get_owned_thread(thread_id: int, user_id: int) -> ChatThread | None:
    return db.session.scalar(
        select(ChatThread).where(
            ChatThread.id == thread_id,
            ChatThread.user_id == user_id,
        )
    )


def owned_note_ids(user_id: int, note_ids: list[int]) -> set[int]:
    if not note_ids:
        return set()
    return set(
        db.session.scalars(
            select(Note.id).where(Note.user_id == user_id, Note.id.in_(note_ids))
        )
    )


def list_threads(user_id: int) -> list[ChatThread]:
    return list(
        db.session.scalars(
            select(ChatThread)
            .where(ChatThread.user_id == user_id)
            .order_by(ChatThread.updated_at.desc(), ChatThread.id.desc())
            .limit(50)
        )
    )


def delete_thread(thread: ChatThread) -> None:
    db.session.delete(thread)
    db.session.commit()


def send_message(
    thread: ChatThread,
    question: str,
    answer: str,
    sources: list[dict[str, Any]],
) -> tuple[ChatMessage, ChatMessage]:
    user_message = ChatMessage(thread_id=thread.id, role="user", content=question)
    assistant_message = ChatMessage(
        thread_id=thread.id,
        role="assistant",
        content=answer,
        sources_json=sources,
    )
    db.session.add_all((user_message, assistant_message))
    if thread.title == "New study session":
        thread.title = question[:70].strip() or "Study session"
    thread.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return user_message, assistant_message


def get_messages(thread: ChatThread) -> list[ChatMessage]:
    return list(
        db.session.scalars(
            select(ChatMessage)
            .where(ChatMessage.thread_id == thread.id)
            .order_by(ChatMessage.id)
        )
    )


def get_context_sources(
    user_id: int,
    question: str,
    selected_note_ids: list[int],
) -> list[dict[str, Any]]:
    notes: list[Note] = []
    if selected_note_ids:
        notes = list(
            db.session.scalars(
                select(Note)
                .where(Note.user_id == user_id, Note.id.in_(selected_note_ids))
                .limit(10)
            )
        )
    else:
        notes = _rank_relevant_notes(user_id, question)

    sources: list[dict[str, Any]] = [
        {
            "label": f"Note {index}",
            "id": note.id,
            "title": note.title,
            "subject": note.subject,
            "content": note.content[:6000],
            "key_takeaways": (note.ai_summary or "")[:2000],
            "conceptual_challenge": (note.ai_confuser or "")[:1000],
        }
        for index, note in enumerate(notes, start=1)
    ]

    terms = _search_terms(question)
    analyses = list(
        db.session.scalars(
            select(PyqAnalysis)
            .where(PyqAnalysis.user_id == user_id)
            .order_by(PyqAnalysis.created_at.desc())
            .limit(30)
        )
    )
    scored_analyses = [
        (sum(term in f"{item.subject_name} {item.repeated_topics}".lower() for term in terms), item)
        for item in analyses
    ]
    for index, (score, analysis) in enumerate(
        sorted(scored_analyses, key=lambda pair: (pair[0], pair[1].id), reverse=True)[:3],
        start=1,
    ):
        if score > 0 or not terms:
            sources.append(
                {
                    "label": f"PYQ {index}",
                    "id": analysis.id,
                    "subject": analysis.subject_name,
                    "exam": analysis.exam_name,
                    "topics": analysis.repeated_topics[:3000],
                    "strategy": analysis.exam_strategy[:2000],
                }
            )
    return sources


def _rank_relevant_notes(user_id: int, question: str) -> list[Note]:
    candidates = list(
        db.session.scalars(
            select(Note)
            .where(Note.user_id == user_id)
            .order_by(Note.created_at.desc(), Note.id.desc())
            .limit(100)
        )
    )
    terms = _search_terms(question)
    if not terms:
        return candidates[:5]

    ranked = []
    for note in candidates:
        text = f"{note.title} {note.subject or ''} {note.content}".lower()
        score = sum(text.count(term) for term in terms)
        if score:
            ranked.append((score, note))
    ranked.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
    return [note for _, note in ranked[:5]]


def _search_terms(text: str) -> set[str]:
    return set(WORD_PATTERN.findall(text.lower())) - {
        "the", "and", "for", "that", "with", "what", "from", "this",
        "have", "does", "explain", "about", "into", "your", "when",
    }


def serialize_thread(thread: ChatThread) -> dict[str, Any]:
    return {
        "id": thread.id,
        "title": thread.title,
        "context_note_ids": thread.context_note_ids or [],
        "updated_at": _iso(thread.updated_at),
    }


def serialize_message(message: ChatMessage) -> dict[str, Any]:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "sources": message.sources_json or [],
        "created_at": _iso(message.created_at),
    }


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()
