# AI Study Assistant

A Flask application for private study notes and AI-assisted previous year question (PYQ) analysis. It uses MySQL, SQLAlchemy/Flask-Migrate, Flask-Login sessions, CSRF protection, Gemini, and server-rendered HTML with vanilla JavaScript.

## Features

- Student registration and sign-in; passwords are stored as salted Werkzeug hashes.
- Private notes library with subject labels, search, full-note reading, editing, deletion, takeaways, conceptual questions, and downloadable study-material PDFs.
- Separate **My notes** and **AI study space** sections: original note content stays distinct from the AI Teacher takeaways and AI Confuser challenge.
- Persistent AI tutor conversations grounded in personal notes and PYQ analyses, with selectable note context and visible source references.
- PYQ analysis with exam/class/year metadata, year/marks-tagged question input, cited evidence, explainable topic-priority levels, and original practice-question patterns. Priority indicates revision focus—not a guaranteed exam prediction.
- Saved chat and PYQ history, account ownership checks, and deletion controls.
- CSRF protection for forms and browser API mutations, secure session-cookie defaults, response security headers, parameterized ORM queries, request size limits, and safe DOM text rendering.
- Incremental Flask-Migrate/Alembic database migrations.

## Requirements and setup

- Python 3.10+
- MySQL 8+
- Gemini API key for AI endpoints

1. Create a virtual environment and install packages:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Create the MySQL database with `study_assistant` as its default character set:

   ```sql
   CREATE DATABASE study_assistant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. Copy `.env.example` to `.env` and set your values. The app loads `.env` at startup; never commit that file or share its secrets. Generate `SECRET_KEY` with a cryptographically secure random generator. Use a MySQL account with access only to this database. Enable `SESSION_COOKIE_SECURE=true` when serving over HTTPS.

4. Apply migrations and run the app:

   ```powershell
   $env:FLASK_APP = "app:create_app"
   flask db upgrade
   python app.py
   ```

   Open `http://127.0.0.1:5000`. `schema.sql` describes the final MySQL schema if you prefer to provision tables manually; use either that schema or migrations, not both on the same empty database.

### Existing pre-authentication database

Back up the existing database first. If it contains the original `notes` and `pyq_analyses` tables created from the original `schema.sql`, mark that schema as the first migration and apply account ownership columns:

```powershell
$env:FLASK_APP = "app:create_app"
flask db stamp 0001_initial
flask db upgrade
```

Existing records keep a `NULL` owner because their original author cannot be determined. The app deliberately excludes unowned legacy rows from all account queries; new records are owned by the signed-in user. Export or otherwise preserve data before changing a database.

## Configuration

`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` configure MySQL. Defaults are `localhost:3306`, `root`, and `study_assistant`. `GEMINI_API_KEY` and optional `GEMINI_MODEL` configure AI generation. `SECRET_KEY` is required. `SESSION_COOKIE_SECURE=true` should be set behind HTTPS. Do not enable `FLASK_DEBUG` in production.

## Routes

- `GET /register`, `POST /register` — create a student account.
- `GET /login`, `POST /login` — sign in.
- `POST /logout` — sign out (CSRF-protected).
- `GET /`, `GET /pyq` — authenticated dashboard and analyzer.
- `GET /notes/<id>` — open a full note and its generated study material.
- `GET /tutor` — private AI tutor and saved conversations.
- `GET /api/notes?q=...` — list/search the current user's notes.
- `POST /api/notes` — create a note with JSON `{"title": "...", "subject": "...", "content": "..."}`.
- `PUT /api/notes/<id>` — edit a note; its previous AI material is cleared.
- `DELETE /api/notes/<id>` — delete a note.
- `POST /api/notes/<id>/generate` — generate three takeaways and a conceptual question.
- `GET /api/notes/<id>/study-material.pdf` — download a private PDF once that note has generated AI material.
- `POST /api/pyq/analyze` — analyze `{"subject": "...", "exam_name": "...", "academic_level": "...", "year_range": "...", "pyqs": "..."}`. Put one question per line; when possible, use `2025 | 5 marks | Question text`.
- `GET /api/pyq/history` — list up to 50 saved analyses.
- `DELETE /api/pyq/history/<id>` — delete an analysis owned by the current user.
- `GET /api/chat/threads` — list private tutor conversations.
- `POST /api/chat/threads` — create a conversation with optional owned note IDs.
- `GET /api/chat/threads/<id>` — retrieve a conversation and transcript.
- `POST /api/chat/threads/<id>/messages` — ask the tutor a question.
- `DELETE /api/chat/threads/<id>` — delete a conversation and its messages.

Browser requests that mutate data must send the CSRF token from the `csrf-token` meta tag in the `X-CSRFToken` header. APIs return `401` for missing authentication and `404` for another user's or nonexistent record.

## Project layout

```text
app.py                  Application factory and security configuration
controllers/            Auth, page, and JSON API blueprints
models/                 SQLAlchemy User, Note, and PyqAnalysis models
services/               Authentication, notes, PYQ, and Gemini logic
migrations/              Alembic migration environment and revisions
templates/               Shared layout, notes dashboard, tutor, PYQ, and auth pages
static/css/              Responsive application styles
static/js/               Vanilla JavaScript clients
schema.sql               Final MySQL schema
```
# Ai-study-assistant-
