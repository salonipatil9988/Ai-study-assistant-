import logging
import os

from flask import Flask, jsonify, redirect, request, url_for
from flask_login import current_user
from flask_wtf.csrf import CSRFError

from config import Config
from routes import api_bp, auth_bp, web_bp
from extensions import csrf, db, login_manager, migrate
from models.user import User


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if not app.testing and not app.config.get("SECRET_KEY"):
        raise RuntimeError("Set SECRET_KEY to a long, random value before starting the app.")

    logging.basicConfig(level=logging.INFO)
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        try:
            return db.session.get(User, int(user_id))
        except ValueError:
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/"):
            return jsonify({"error": "Authentication required."}), 401
        return redirect(url_for("auth.login", next=request.full_path))

    @app.context_processor
    def inject_user():
        return {"current_user": current_user}

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
            "base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        return response

    @app.errorhandler(CSRFError)
    def handle_csrf_error(_error: CSRFError):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Your session token expired. Refresh the page and try again."}), 400
        return _error.description, 400

    @app.errorhandler(413)
    def handle_payload_too_large(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Request is too large."}), error.code
        return "Request is too large.", error.code

    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
