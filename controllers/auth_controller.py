from urllib.parse import urljoin, urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from extensions import db
from services.auth_service import (
    RegistrationError,
    authenticate_user,
    register_user,
)

auth_bp = Blueprint("auth", __name__)


def _safe_redirect_target(target: str | None) -> str | None:
    if not target:
        return None
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    if redirect_url.scheme in {"http", "https"} and redirect_url.netloc == host_url.netloc:
        return target
    return None


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("web.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        try:
            user = register_user(username, password)
        except RegistrationError as error:
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            flash("That username is already in use.", "error")
        else:
            login_user(user)
            return redirect(url_for("web.dashboard"))
    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("web.dashboard"))
    if request.method == "POST":
        user = authenticate_user(
            request.form.get("username", ""),
            request.form.get("password", ""),
        )
        if user is None:
            flash("Username or password is incorrect.", "error")
        else:
            login_user(user)
            return_to = _safe_redirect_target(request.args.get("next"))
            return redirect(return_to or url_for("web.dashboard"))
    return render_template("auth/login.html")


@auth_bp.post("/logout")
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
