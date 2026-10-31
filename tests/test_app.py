import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

from app import create_app
from extensions import db


class StudyAssistantTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret-key",
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "WTF_CSRF_ENABLED": False,
            }
        )
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def register_and_login(self, username):
        response = self.client.post(
            "/register",
            data={"username": username, "password": "secure-test-password"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)

    def test_authentication_guards_pages_and_api(self):
        self.assertEqual(self.client.get("/").status_code, 302)
        self.assertEqual(self.client.get("/pyq").status_code, 302)
        response = self.client.get("/api/notes")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json["error"], "Authentication required.")

    def test_note_crud_and_user_ownership(self):
        self.register_and_login("student_one")
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/pyq").status_code, 200)
        response = self.client.post(
            "/api/notes",
            json={"title": "=1+1", "content": "Cells have membranes."},
        )
        self.assertEqual(response.status_code, 201)
        note_id = response.json["id"]
        self.assertEqual(self.client.get("/api/notes").json[0]["id"], note_id)
        self.assertEqual(self.client.get("/api/notes").json[0]["id"], note_id)
        self.assertEqual(self.client.get("/api/notes?q=cells").json[0]["id"], note_id)
        with patch(
            "controllers.api_controller.generate_note_material",
            return_value={"takeaways": "- One\n- Two\n- Three", "confuser": "Why?"},
        ):
            generated = self.client.post(f"/api/notes/{note_id}/generate")
        self.assertEqual(generated.status_code, 200)
        self.assertEqual(generated.json["ai_confuser"], "Why?")
        self.assertEqual(self.client.get("/api/notes/export").status_code, 404)
        self.assertEqual(
            self.client.get(f"/api/notes/{note_id}/study-material.pdf").status_code,
            200,
        )
        self.assertEqual(
            self.client.put(
                f"/api/notes/{note_id}",
                json={"title": "Updated", "content": "Updated content"},
            ).status_code,
            200,
        )
        self.assertIsNone(self.client.get("/api/notes").json[0]["ai_summary"])

        self.client.post("/logout")
        self.register_and_login("student_two")
        self.assertEqual(self.client.get("/api/notes").json, [])
        self.assertEqual(self.client.get("/api/notes/export").status_code, 404)
        self.assertEqual(self.client.get(f"/notes/{note_id}").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/notes/{note_id}").status_code, 404)

    def test_dashboard_form_fallback_saves_and_renders_note(self):
        self.register_and_login("form_fallback_student")
        response = self.client.post(
            "/notes",
            data={
                "title": "Fallback note",
                "subject": "Biology",
                "content": "Notes save even if JavaScript is unavailable.",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Note saved. Ready when you are!", response.data)
        self.assertIn(b"Fallback note", response.data)
        self.assertIn(
            "Fallback note",
            self.client.get("/api/notes").json[0]["title"],
        )

    def test_pdf_requires_generated_material_and_is_private(self):
        self.register_and_login("pdf_student")
        note = self.client.post(
            "/api/notes",
            json={"title": "Café Biology", "content": "Cells are the basic units."},
        ).json
        note_id = note["id"]
        missing_material = self.client.get(f"/api/notes/{note_id}/study-material.pdf")
        self.assertEqual(missing_material.status_code, 409)

        with patch(
            "controllers.api_controller.generate_note_material",
            return_value={
                "takeaways": "• Cells are basic units.\n• They contain DNA.\n• They divide.",
                "confuser": "Why are viruses not considered cells?",
            },
        ):
            self.assertEqual(
                self.client.post(f"/api/notes/{note_id}/generate").status_code,
                200,
            )
        pdf = self.client.get(f"/api/notes/{note_id}/study-material.pdf")
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf.mimetype, "application/pdf")
        self.assertTrue(pdf.data.startswith(b"%PDF-"))
        detail = self.client.get(f"/notes/{note_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertIn(b"Your original note", detail.data)
        self.assertIn(b"AI Confuser", detail.data)

    def test_pyq_analysis_is_persisted_per_account(self):
        self.register_and_login("pyq_student")
        with patch(
            "controllers.api_controller.analyze_pyqs",
            return_value={
                "repeated_topics": "Cell division",
                "exam_strategy": "Review diagrams and compare stages.",
                "topics": [
                    {
                        "topic": "Mitosis",
                        "question_count": 2,
                        "years": ["2024", "2025"],
                        "priority": "Medium",
                        "question_ids": [1, 2],
                        "year_coverage": 2,
                        "rationale": "Appears across two papers.",
                    }
                ],
                "practice_questions": [
                    {"topic": "Mitosis", "question": "Compare the stages.", "priority": "High"}
                ],
                "question_count": 2,
                "trend_summary": "Repeated across two year-tagged papers.",
            },
        ):
            response = self.client.post(
                "/api/pyq/analyze",
                json={
                    "subject": "Biology",
                    "exam_name": "Semester exam",
                    "academic_level": "Year 1",
                    "year_range": "2024-2025",
                    "pyqs": "2025 | 5 marks | Describe mitosis.\n2024 | 8 marks | Explain mitosis.",
                },
            )
        self.assertEqual(response.status_code, 201)
        history = self.client.get("/api/pyq/history").json
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["exam_name"], "Semester exam")
        self.assertEqual(history[0]["topics"][0]["year_coverage"], 2)
        self.assertEqual(history[0]["practice_questions"][0]["topic"], "Mitosis")

    def test_tutor_chat_persists_context_and_is_private(self):
        self.register_and_login("tutor_student")
        note = self.client.post(
            "/api/notes",
            json={"title": "Mitosis", "subject": "Biology", "content": "Cells divide."},
        ).json
        thread = self.client.post(
            "/api/chat/threads",
            json={"note_ids": [note["id"]]},
        )
        self.assertEqual(thread.status_code, 201)
        thread_id = thread.json["id"]
        with patch(
            "controllers.api_controller.chat_with_tutor",
            return_value="Mitosis divides one cell into two daughter cells. [Note 1]",
        ) as tutor:
            response = self.client.post(
                f"/api/chat/threads/{thread_id}/messages",
                json={"message": "Explain mitosis."},
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["assistant_message"]["sources"][0]["title"], "Mitosis")
        tutor.assert_called_once()
        self.assertEqual(
            len(self.client.get(f"/api/chat/threads/{thread_id}").json["messages"]),
            2,
        )

        self.client.post("/logout")
        self.register_and_login("other_tutor_student")
        self.assertEqual(self.client.get(f"/api/chat/threads/{thread_id}").status_code, 404)

    def test_csrf_required_for_mutating_api(self):
        csrf_app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret-key",
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
            }
        )
        with csrf_app.app_context():
            db.create_all()
        csrf_client = csrf_app.test_client()
        response = csrf_client.post(
            "/api/notes",
            json={"title": "Blocked", "content": "Missing CSRF token."},
        )
        self.assertEqual(response.status_code, 400)
        with csrf_app.app_context():
            db.drop_all()

    def test_pyq_topic_frequency_uses_only_valid_question_evidence(self):
        from services.ai_service import analyze_pyqs

        model_result = {
            "topics": [
                {
                    "topic": "Cell division",
                    "question_ids": [1, 2, 99],
                    "rationale": "Repeated in provided papers.",
                }
            ],
            "exam_strategy": "Review cell division.",
            "trend_summary": "Seen across multiple years.",
            "practice_questions": [
                {
                    "question": "Compare mitosis and meiosis.",
                    "topic": "Cell division",
                    "priority": "High",
                    "rationale": "Tests the repeated concept.",
                }
            ],
        }
        with patch("services.ai_service._generate_json", return_value=model_result):
            analysis = analyze_pyqs(
                "Biology",
                "2025 | 5 marks | Explain mitosis.\n2024 | 8 marks | Compare cell division.",
            )
        self.assertEqual(analysis["question_count"], 2)
        self.assertEqual(analysis["topics"][0]["question_ids"], [1, 2])
        self.assertEqual(analysis["topics"][0]["years"], ["2024", "2025"])
        self.assertEqual(analysis["topics"][0]["priority"], "Medium")
        self.assertIn("is a revision guide, not a prediction", analysis["confidence_note"])


if __name__ == "__main__":
    unittest.main()
