from datetime import datetime, timezone

from sqlalchemy import select

from extensions import db
from models.pyq_analysis import PyqAnalysis


def save_analysis(
    user_id: int,
    subject: str,
    pyqs: str,
    repeated_topics: str,
    exam_strategy: str,
    exam_name: str = "",
    academic_level: str = "",
    year_range: str = "",
    question_count: int = 0,
    trend_summary: str = "",
    confidence_note: str = "",
    topics: list[dict] | None = None,
    practice_questions: list[dict] | None = None,
) -> PyqAnalysis:
    analysis = PyqAnalysis(
        user_id=user_id,
        subject_name=subject,
        exam_name=exam_name or None,
        academic_level=academic_level or None,
        year_range=year_range or None,
        question_count=question_count,
        raw_pyqs=pyqs,
        repeated_topics=repeated_topics,
        exam_strategy=exam_strategy,
        trend_summary=trend_summary or None,
        confidence_note=confidence_note or None,
        topics_json=topics or [],
        practice_questions=practice_questions or [],
    )
    db.session.add(analysis)
    db.session.commit()
    return analysis


def list_analyses(user_id: int) -> list[PyqAnalysis]:
    return list(
        db.session.scalars(
            select(PyqAnalysis)
            .where(PyqAnalysis.user_id == user_id)
            .order_by(PyqAnalysis.created_at.desc(), PyqAnalysis.id.desc())
            .limit(50)
        )
    )


def get_owned_analysis(analysis_id: int, user_id: int) -> PyqAnalysis | None:
    return db.session.scalar(
        select(PyqAnalysis).where(
            PyqAnalysis.id == analysis_id,
            PyqAnalysis.user_id == user_id,
        )
    )


def delete_analysis(analysis: PyqAnalysis) -> None:
    db.session.delete(analysis)
    db.session.commit()


def serialize_analysis(analysis: PyqAnalysis) -> dict[str, object]:
    created_at = analysis.created_at
    if isinstance(created_at, datetime) and created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return {
        "id": analysis.id,
        "subject_name": analysis.subject_name,
        "exam_name": analysis.exam_name,
        "academic_level": analysis.academic_level,
        "year_range": analysis.year_range,
        "question_count": analysis.question_count,
        "raw_pyqs": analysis.raw_pyqs,
        "repeated_topics": analysis.repeated_topics,
        "exam_strategy": analysis.exam_strategy,
        "trend_summary": analysis.trend_summary,
        "confidence_note": analysis.confidence_note,
        "topics": analysis.topics_json or [],
        "practice_questions": analysis.practice_questions or [],
        "created_at": created_at.isoformat() if created_at else None,
    }
