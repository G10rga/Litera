"""Application configuration objects for Litera.

Selected via the FLASK_CONFIG environment variable ("development" | "production"
| "testing"). Production refuses to start without an explicit SECRET_KEY.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Minimum accepted password length (register + reset).
PASSWORD_MIN_LENGTH = 12

# Password-reset token lifetime in seconds.
PASSWORD_RESET_MAX_AGE = 60 * 60  # 1 hour


def _normalise_db_url(url: str) -> str:
    """Heroku/Render style postgres:// URLs are not understood by SQLAlchemy 2."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _engine_options() -> dict:
    """Shared engine options. pool_size is capped for small hosted Postgres plans."""
    options = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    pool_size = os.environ.get("DB_POOL_SIZE")
    if pool_size:
        options["pool_size"] = max(1, int(pool_size))
        options["max_overflow"] = max(0, int(os.environ.get("DB_MAX_OVERFLOW", "2")))
    return options


class BaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options()

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    WTF_CSRF_TIME_LIMIT = None
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "litera.support@gmail.com")
    PASSWORD_MIN_LENGTH = PASSWORD_MIN_LENGTH
    PASSWORD_RESET_MAX_AGE = PASSWORD_RESET_MAX_AGE

    # SMTP — Resend, Postmark, SES, or any SMTP relay.
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "")
    MAIL_TIMEOUT = int(os.environ.get("MAIL_TIMEOUT", "20"))

    # Optional error tracking. Leave unset to disable.
    SENTRY_DSN = os.environ.get("SENTRY_DSN", "")

    # Public site URL for sitemap canonicals (no trailing slash).
    PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")

    # Flask-Limiter storage. memory:// is fine for a single worker; use Redis
    # when running multiple gunicorn workers.
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = "200 per hour"

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "litera-dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = _normalise_db_url(
        os.environ.get("DATABASE_URL")
        or "sqlite:///" + os.path.join(BASE_DIR, "instance", "vepkhvi.db")
    )
    SESSION_COOKIE_SECURE = False


class TestingConfig(BaseConfig):
    TESTING = True
    SECRET_KEY = "testing"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": __import__("sqlalchemy.pool", fromlist=["StaticPool"]).StaticPool,
        "connect_args": {"check_same_thread": False},
    }
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    MAIL_SERVER = ""
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"

    # Sensible default for free-tier Postgres (often 20–25 connections).
    SQLALCHEMY_ENGINE_OPTIONS = {
        **_engine_options(),
        "pool_size": int(os.environ.get("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", "2")),
    }

    @staticmethod
    def init_app(app):
        # Re-read from the process environment so .env / systemd EnvironmentFile
        # win even if this module was imported before load_dotenv().
        secret = os.environ.get("SECRET_KEY") or app.config.get("SECRET_KEY")
        database_url = _normalise_db_url(os.environ.get("DATABASE_URL", ""))
        app.config["SECRET_KEY"] = secret
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url

        if not app.config.get("SECRET_KEY"):
            raise RuntimeError(
                "SECRET_KEY must be set in the environment for production."
            )
        if not app.config.get("SQLALCHEMY_DATABASE_URI"):
            raise RuntimeError(
                "DATABASE_URL must be set in the environment for production."
            )
        if app.config.get("SECRET_KEY") == "litera-dev-secret-change-me":
            raise RuntimeError(
                "Refuse to start: SECRET_KEY is still the public development default."
            )


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None):
    key = (name or os.environ.get("FLASK_CONFIG") or "development").lower()
    # APP_ENV is accepted as an alias used in older deploy docs.
    if key == "development" and os.environ.get("APP_ENV"):
        key = os.environ["APP_ENV"].lower()
    return CONFIGS.get(key, DevelopmentConfig)
