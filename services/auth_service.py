import re

from sqlalchemy import select

from extensions import db
from models.user import User

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,80}$")


class RegistrationError(ValueError):
    pass


def register_user(username: str, password: str) -> User:
    normalized_username = username.strip()
    if not USERNAME_PATTERN.fullmatch(normalized_username):
        raise RegistrationError(
            "Username must be 3–80 characters and use only letters, numbers, or underscores."
        )
    if len(password) < 10 or len(password) > 128:
        raise RegistrationError("Password must be between 10 and 128 characters.")
    if db.session.scalar(
        select(User.id).where(User.username == normalized_username)
    ) is not None:
        raise RegistrationError("That username is already in use.")

    user = User(username=normalized_username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(username: str, password: str) -> User | None:
    user = db.session.scalar(select(User).where(User.username == username.strip()))
    if user is not None and user.check_password(password):
        return user
    return None
