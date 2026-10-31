from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask import abort
from flask_login import current_user, login_required

from services.note_service import create_note, get_owned_note, list_notes

web_bp = Blueprint("web", __name__)


@web_bp.get("/")
@login_required
def dashboard():
    return render_template("index.html", notes=list_notes(current_user.id))


@web_bp.post("/notes")
@login_required
def create_note_from_form():
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    subject = request.form.get("subject", "").strip()
    if not title or not content:
        flash("Please enter a title and your notes before saving.", "error")
    elif len(title) > 255 or len(subject) > 120 or len(content.encode("utf-8")) > 60_000:
        flash("Title, subject, or note content exceeds the allowed length.", "error")
    else:
        create_note(current_user.id, title, content, subject)
        flash("Note saved. Ready when you are!", "success")
    return redirect(url_for("web.dashboard"))


@web_bp.get("/pyq")
@login_required
def pyq_page():
    return render_template("pyq.html")


@web_bp.get("/tutor")
@login_required
def tutor_page():
    return render_template("tutor.html")


@web_bp.get("/notes/<int:note_id>")
@login_required
def note_detail(note_id: int):
    note = get_owned_note(note_id, current_user.id)
    if note is None:
        abort(404)
    return render_template("note_detail.html", note=note)
