"""Shared pytest fixtures."""

import pytest

from app import create_app
from models import db


@pytest.fixture()
def app():
    application = create_app("testing")
    application.config["RATELIMIT_ENABLED"] = False
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
