from flask import Blueprint, Response, current_app, jsonify, request
from flask_login import current_user, login_required

from services.ai_service import (
    AIServiceError,
    analyze_pyqs,
    chat_with_tutor,
    generate_note_material,
)
from services.chat_service import (
    create_thread,
    delete_thread,
    get_context_sources,
    get_messages,
    get_owned_thread,
    list_threads,
    owned_note_ids,
    send_message,
    serialize_message,
    serialize_thread,
)
from services.note_service import (
    create_note,
    delete_note,
    get_owned_note,
    list_notes,
    save_note_material,
    serialize_note,
    update_note,
)
from services.pdf_service import build_study_material_pdf
from services.pyq_service import (
    delete_analysis,
    get_owned_analysis,
    list_analyses,
    save_analysis,
    serialize_analysis,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _required_text(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    return value.strip() if isinstance(value, str) else ""


def _json_payload() -> dict[str, object] | None:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else None


def _validation_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


@api_bp.get("/notes")
@login_required
def list_user_notes():
    search = request.args.get("q", "").strip()[:255]
    return jsonify([serialize_note(note) for note in list_notes(current_user.id, search)])


@api_bp.post("/notes")
@login_required
def create_user_note():
    payload = _json_payload()
    if payload is None:
        return _validation_error("Send a JSON object with title and content.")
    title = _required_text(payload, "title")
    content = _required_text(payload, "content")
    subject = _required_text(payload, "subject")
    if not title or not content:
        return _validation_error("Title and content are required.")
    if len(title) > 255 or len(subject) > 120 or len(content.encode("utf-8")) > 60_000:
        return _validation_error("Title must be at most 255 characters and note content at most 60,000 UTF-8 bytes.")
    note = create_note(current_user.id, title, content, subject)
    return jsonify(serialize_note(note)), 201


@api_bp.put("/notes/<int:note_id>")
@login_required
def update_user_note(note_id: int):
    note = get_owned_note(note_id, current_user.id)
    if note is None:
        return _validation_error("Note not found.", 404)
    payload = _json_payload()
    if payload is None:
        return _validation_error("Send a JSON object with title and content.")
    title = _required_text(payload, "title")
    content = _required_text(payload, "content")
    subject = _required_text(payload, "subject")
    if not title or not content:
        return _validation_error("Title and content are required.")
    if len(title) > 255 or len(subject) > 120 or len(content.encode("utf-8")) > 60_000:
        return _validation_error("Title must be at most 255 characters and note content at most 60,000 UTF-8 bytes.")
    return jsonify(serialize_note(update_note(note, title, content, subject)))


@api_bp.delete("/notes/<int:note_id>")
@login_required
def delete_user_note(note_id: int):
    note = get_owned_note(note_id, current_user.id)
    if note is None:
        return _validation_error("Note not found.", 404)
    delete_note(note)
    return jsonify({"message": "Note deleted."})


@api_bp.post("/notes/<int:note_id>/generate")
@login_required
def generate_user_note_material(note_id: int):
    note = get_owned_note(note_id, current_user.id)
    if note is None:
        return _validation_error("Note not found.", 404)
    try:
        material = generate_note_material(note.content)
    except AIServiceError as error:
        current_app.logger.warning("Gemini note generation failed: %s", error)
        return _validation_error(str(error), 502)
    save_note_material(note, material["takeaways"], material["confuser"])
    return jsonify(
        {
            "id": note.id,
            "ai_summary": material["takeaways"],
            "ai_confuser": material["confuser"],
        }
    )


@api_bp.get("/notes/<int:note_id>/study-material.pdf")
@login_required
def download_study_material(note_id: int):
    note = get_owned_note(note_id, current_user.id)
    if note is None:
        return _validation_error("Note not found.", 404)
    if not note.ai_summary or not note.ai_confuser:
        return _validation_error("Generate AI study material before downloading a PDF.", 409)
    pdf = build_study_material_pdf(note)
    safe_title = "".join(
        character if character.isalnum() or character in "-_" else "-"
        for character in note.title
    ).strip("-_")[:60] or f"note-{note.id}"
    response = Response(pdf, mimetype="application/pdf")
    response.headers["Content-Disposition"] = (
        f'attachment; filename="study-material-{safe_title}.pdf"'
    )
    response.headers["Cache-Control"] = "private, no-store"
    return response


@api_bp.post("/pyq/analyze")
@login_required
def analyze_user_pyq():
    payload = _json_payload()
    if payload is None:
        return _validation_error("Send a JSON object with subject and pyqs.")
    subject = _required_text(payload, "subject")
    pyqs = _required_text(payload, "pyqs")
    exam_name = _required_text(payload, "exam_name")
    academic_level = _required_text(payload, "academic_level")
    year_range = _required_text(payload, "year_range")
    if not subject or not pyqs:
        return _validation_error("Subject and previous year questions are required.")
    if (
        len(subject) > 255
        or len(exam_name) > 255
        or len(academic_level) > 255
        or len(year_range) > 100
        or len(pyqs.encode("utf-8")) > 60_000
    ):
        return _validation_error("Subject must be at most 255 characters and questions at most 60,000 UTF-8 bytes.")
    try:
        analysis = analyze_pyqs(subject, pyqs, exam_name, academic_level, year_range)
    except AIServiceError as error:
        current_app.logger.warning("Gemini PYQ analysis failed: %s", error)
        return _validation_error(str(error), 502)
    saved = save_analysis(
        current_user.id,
        subject,
        pyqs,
        analysis["repeated_topics"],
        analysis["exam_strategy"],
        exam_name=exam_name,
        academic_level=academic_level,
        year_range=year_range,
        question_count=analysis.get("question_count", 0),
        trend_summary=analysis.get("trend_summary", ""),
        confidence_note=analysis.get(
            "confidence_note",
            "Priority reflects the supplied PYQs; it is not a prediction guarantee.",
        ),
        topics=analysis.get("topics", []),
        practice_questions=analysis.get("practice_questions", []),
    )
    return jsonify(serialize_analysis(saved)), 201


@api_bp.get("/pyq/history")
@login_required
def get_pyq_history():
    return jsonify([serialize_analysis(item) for item in list_analyses(current_user.id)])


@api_bp.delete("/pyq/history/<int:analysis_id>")
@login_required
def remove_pyq_history(analysis_id: int):
    analysis = get_owned_analysis(analysis_id, current_user.id)
    if analysis is None:
        return _validation_error("Analysis not found.", 404)
    delete_analysis(analysis)
    return jsonify({"message": "Analysis deleted."})


@api_bp.get("/chat/threads")
@login_required
def get_chat_threads():
    return jsonify([serialize_thread(thread) for thread in list_threads(current_user.id)])


@api_bp.post("/chat/threads")
@login_required
def start_chat_thread():
    payload = _json_payload()
    if payload is None:
        return _validation_error("Send a JSON object with optional note_ids.")
    note_ids = payload.get("note_ids", [])
    if (
        not isinstance(note_ids, list)
        or len(note_ids) > 10
        or any(not isinstance(note_id, int) or isinstance(note_id, bool) for note_id in note_ids)
    ):
        return _validation_error("Choose up to 10 valid notes for tutor context.")
    normalized_ids = list(dict.fromkeys(note_ids))
    owned_ids = owned_note_ids(current_user.id, normalized_ids)
    if len(owned_ids) != len(normalized_ids):
        return _validation_error("One or more selected notes were not found.", 404)
    thread = create_thread(current_user.id, normalized_ids)
    return jsonify(serialize_thread(thread)), 201


@api_bp.get("/chat/threads/<int:thread_id>")
@login_required
def get_chat_thread(thread_id: int):
    thread = get_owned_thread(thread_id, current_user.id)
    if thread is None:
        return _validation_error("Study chat not found.", 404)
    return jsonify(
        {
            **serialize_thread(thread),
            "messages": [serialize_message(message) for message in get_messages(thread)],
        }
    )


@api_bp.delete("/chat/threads/<int:thread_id>")
@login_required
def remove_chat_thread(thread_id: int):
    thread = get_owned_thread(thread_id, current_user.id)
    if thread is None:
        return _validation_error("Study chat not found.", 404)
    delete_thread(thread)
    return jsonify({"message": "Study chat deleted."})


@api_bp.post("/chat/threads/<int:thread_id>/messages")
@login_required
def send_chat_message(thread_id: int):
    thread = get_owned_thread(thread_id, current_user.id)
    if thread is None:
        return _validation_error("Study chat not found.", 404)
    payload = _json_payload()
    if payload is None:
        return _validation_error("Send a JSON object with a message.")
    question = _required_text(payload, "message")
    if not question or len(question) > 8_000:
        return _validation_error("Message is required and must be 8,000 characters or fewer.")

    sources = get_context_sources(
        current_user.id,
        question,
        thread.context_note_ids or [],
    )
    prior = [
        {"role": message.role, "content": message.content}
        for message in get_messages(thread)[-12:]
    ]
    try:
        answer = chat_with_tutor(question, prior, sources)
    except AIServiceError as error:
        current_app.logger.warning("Gemini tutor response failed: %s", error)
        return _validation_error(str(error), 502)
    user_message, assistant_message = send_message(
        thread,
        question,
        answer,
        sources,
    )
    return jsonify(
        {
            "user_message": serialize_message(user_message),
            "assistant_message": serialize_message(assistant_message),
            "thread": serialize_thread(thread),
        }
    ), 201
