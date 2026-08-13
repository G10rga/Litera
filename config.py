"""Application configuration objects for Litera.

Selected via the FLASK_CONFIG environment variable ("development" | "production"
| "testing"). Production refuses to start without an explicit SECRET_KEY.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _normalise_db_url(url: str) -> str:
    """Heroku/Render style postgres:// URLs are not understood by SQLAlchemy 2."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


class BaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    WTF_CSRF_TIME_LIMIT = None
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    # Where /contact submissions are routed for humans to read.
    CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "litera.support@gmail.com")

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
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"

    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _normalise_db_url(os.environ.get("DATABASE_URL", ""))

    @staticmethod
    def init_app(app):
        if not app.config.get("SECRET_KEY"):
            raise RuntimeError(
                "SECRET_KEY must be set in the environment for production."
            )
        if not app.config.get("SQLALCHEMY_DATABASE_URI"):
            raise RuntimeError(
                "DATABASE_URL must be set in the environment for production."
            )


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None):
    key = (name or os.environ.get("FLASK_CONFIG") or "development").lower()
    return CONFIGS.get(key, DevelopmentConfig)
