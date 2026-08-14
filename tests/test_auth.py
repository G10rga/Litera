"""Auth, contact, password-reset and empty-database smoke tests."""

from models import ContactMessage, User, Work, db


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_empty_literature_index(client):
    """Empty works table must not crash (previously divided by zero)."""
    assert Work.query.count() == 0
    response = client.get("/literature/")
    assert response.status_code == 200
    assert "ჯერ ცარიელია" in response.get_data(as_text=True)


def test_register_login_logout(client, app):
    response = client.post(
        "/register",
        data={
            "full_name": "Test Scholar",
            "email": "scholar@example.com",
            "grade": "11",
            "password": "twelvechars!!",
            "confirm_password": "twelvechars!!",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Your account is ready" in response.data

    client.post("/logout", follow_redirects=True)

    bad = client.post(
        "/login",
        data={"email": "scholar@example.com", "password": "wrong-password!!"},
        follow_redirects=True,
    )
    assert b"Incorrect email or password" in bad.data

    good = client.post(
        "/login",
        data={"email": "scholar@example.com", "password": "twelvechars!!"},
        follow_redirects=True,
    )
    assert good.status_code == 200
    assert b"Test Scholar" in good.data


def test_password_policy_rejects_short(client):
    response = client.post(
        "/register",
        data={
            "full_name": "Short Pass",
            "email": "short@example.com",
            "password": "short",
            "confirm_password": "short",
        },
        follow_redirects=True,
    )
    assert b"at least 12 characters" in response.data


def test_contact_persists(client):
    response = client.post(
        "/contact",
        data={
            "name": "Reader",
            "email": "reader@example.com",
            "subject": "Hello",
            "body": "This is long enough to pass validation.",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Message received" in response.data
    assert ContactMessage.query.count() == 1


def test_forgot_password_identical_response(client, app):
    client.post(
        "/register",
        data={
            "full_name": "Reset Me",
            "email": "reset@example.com",
            "password": "twelvechars!!",
            "confirm_password": "twelvechars!!",
        },
    )
    client.post("/logout")

    known = client.post(
        "/forgot-password",
        data={"email": "reset@example.com"},
        follow_redirects=True,
    )
    unknown = client.post(
        "/forgot-password",
        data={"email": "nobody@example.com"},
        follow_redirects=True,
    )
    assert b"If an account exists" in known.data
    assert b"If an account exists" in unknown.data
    assert known.status_code == unknown.status_code == 200


def test_password_reset_invalidates_sessions(client, app):
    from tokens import make_reset_token

    client.post(
        "/register",
        data={
            "full_name": "Session User",
            "email": "session@example.com",
            "password": "twelvechars!!",
            "confirm_password": "twelvechars!!",
        },
    )
    assert b"Session User" in client.get("/").data

    with app.app_context():
        user = User.query.filter_by(email="session@example.com").first()
        old_version = user.session_version
        token = make_reset_token(user.id, user.session_version)

    client.post("/logout", follow_redirects=True)

    reset = client.post(
        f"/reset-password/{token}",
        data={
            "password": "brandnewpass!!",
            "confirm_password": "brandnewpass!!",
        },
        follow_redirects=True,
    )
    assert b"Password updated" in reset.data

    with app.app_context():
        user = User.query.filter_by(email="session@example.com").first()
        assert user.session_version == old_version + 1

    # Old password rejected; new password works.
    bad = client.post(
        "/login",
        data={"email": "session@example.com", "password": "twelvechars!!"},
        follow_redirects=True,
    )
    assert b"Incorrect email or password" in bad.data

    good = client.post(
        "/login",
        data={"email": "session@example.com", "password": "brandnewpass!!"},
        follow_redirects=True,
    )
    assert b"Session User" in good.data

    # A second reset with the old token must fail (single-use via session_version).
    client.post("/logout", follow_redirects=True)
    replay = client.get(f"/reset-password/{token}", follow_redirects=True)
    assert b"invalid or has expired" in replay.data


def test_robots_and_sitemap(client):
    assert client.get("/robots.txt").status_code == 200
    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert b"<urlset" in sitemap.data


def test_study_module_pages(client):
    for path in (
        "/syllabus",
        "/studyguide",
        "/examprep",
        "/practicetests",
        "/moderntraslations",
        "/cheracteranalysis",
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert b"Litera" in response.data


def test_delete_user_cli(app):
    runner = app.test_cli_runner()
    with app.app_context():
        user = User(full_name="Gone", email="gone@example.com")
        user.set_password("twelvechars!!")
        db.session.add(user)
        db.session.commit()

    result = runner.invoke(args=["delete-user", "gone@example.com", "--yes"])
    assert result.exit_code == 0
    with app.app_context():
        assert User.query.filter_by(email="gone@example.com").first() is None
