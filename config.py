import os

from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Check for direct database URL (e.g., sqlite:///study.db or custom connection string)
    _custom_db_uri = os.getenv("DATABASE_URL")
    if _custom_db_uri:
        SQLALCHEMY_DATABASE_URI = _custom_db_uri
    else:
        SQLALCHEMY_DATABASE_URI = URL.create(
            drivername="mysql+mysqlconnector",
            username=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            database=os.getenv("MYSQL_DATABASE", "study_assistant"),
            query={"charset": "utf8mb4"},
        )

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = 3600
