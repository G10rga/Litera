"""Litera application factory.

Run locally:
    flask --app app run --debug
Initialise the schema:
    flask --app app init-db
Production:
    gunicorn wsgi:application
"""

from __future__ import annotations

import logging
import os
from collections import defaultdict

import click
from dotenv import load_dotenv

# Load .env before importing config — ProductionConfig reads SECRET_KEY /
# DATABASE_URL at import time, so this must run first.
load_dotenv()

from flask import (  # noqa: E402
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_limiter import Limiter  # noqa: E402
from flask_limiter.util import get_remote_address  # noqa: E402
from flask_login import (  # noqa: E402
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_wtf.csrf import CSRFProtect  # noqa: E402
from sqlalchemy import func  # noqa: E402

from config import get_config  # noqa: E402
from mailutil import send_email  # noqa: E402
from models import (  # noqa: E402
    Aphorism,
    ContactMessage,
    User,
    VefxistyaosaniLine,
    Work,
    db,
)
from tokens import load_reset_token, make_reset_token  # noqa: E402

logger = logging.getLogger("litera.auth")

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Log in to continue."
login_manager.login_message_category = "error"

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])

# URLs that used to serve hand-written mockups with no data behind them.
# Kept as permanent redirects so existing links and search results do not 404.
RETIRED_PATHS = (
    "/syllabus",
    "/studyguide",
    "/examprep",
    "/practicetests",
    "/moderntraslations",
    "/characteranalysis",
    "/cheracteranalysis",
)


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    config_class = get_config(config_name)
    app.config.from_object(config_class)
    config_class.init_app(app)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    try:
        from flask_migrate import Migrate

        Migrate(app, db)
    except ImportError:  # migrations are optional in development
        pass

    _init_sentry(app)

    # True once `npm run build:css` has produced the compiled stylesheet. When
    # false, base.html falls back to the Tailwind CDN so the app still renders.
    app.config["TAILWIND_BUILT"] = os.path.exists(
        os.path.join(app.static_folder, "dist", "app.css")
    )

    register_blueprints(app)
    register_routes(app)
    register_error_handlers(app)
    register_security_headers(app)
    register_cli(app)

    return app


def _init_sentry(app: Flask) -> None:
    dsn = app.config.get("SENTRY_DSN")
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.05,
            send_default_pii=False,
        )
    except Exception:  # pragma: no cover - optional dependency
        app.logger.exception("Sentry initialisation failed")


def register_blueprints(app: Flask) -> None:
    from db_loaders.literature_routes import literature
    from db_loaders.reader_routes import reader
    from db_loaders.shushaniki_routes import shushaniki

    app.register_blueprint(reader)
    app.register_blueprint(literature)
    app.register_blueprint(shushaniki)


@login_manager.user_loader
def load_user(user_id):
    try:
        if "." in str(user_id):
            uid_s, version_s = str(user_id).split(".", 1)
            user = db.session.get(User, int(uid_s))
            if user is None:
                return None
            if int(user.session_version or 0) != int(version_s):
                return None
            return user
        # Legacy cookies that only stored the integer id.
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def _password_min_length() -> int:
    from flask import current_app

    return int(current_app.config.get("PASSWORD_MIN_LENGTH", 12))


def _check_your_email_response():
    flash(
        "If an account exists for that address, a reset link is on its way. "
        "The link expires in one hour.",
        "success",
    )
    return redirect(url_for("forgot_password"))


def register_routes(app: Flask) -> None:  # noqa: C901 - flat route table
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/contact", methods=["GET", "POST"])
    @limiter.limit("3 per hour", methods=["POST"])
    def contact():
        form = {"name": "", "email": "", "subject": "", "body": ""}

        if request.method == "POST":
            form = {
                "name": (request.form.get("name") or "").strip(),
                "email": (request.form.get("email") or "").strip().lower(),
                "subject": (request.form.get("subject") or "").strip(),
                "body": (request.form.get("body") or "").strip(),
            }

            errors = []
            if not form["name"]:
                errors.append("Enter your name.")
            if "@" not in form["email"] or "." not in form["email"]:
                errors.append("Enter a valid email address.")
            if len(form["body"]) < 10:
                errors.append("Write at least a sentence so we can help.")

            if errors:
                for error in errors:
                    flash(error, "error")
            else:
                message = ContactMessage(
                    name=form["name"][:120],
                    email=form["email"][:255],
                    subject=form["subject"][:160] or None,
                    body=form["body"],
                )
                db.session.add(message)
                db.session.commit()
                flash(
                    "Message received. It is stored and will be read "
                    "by a human — replies are not automatic.",
                    "success",
                )
                return redirect(url_for("contact"))

        return render_template("contact.html", form=form)

    @app.route("/terms")
    def tos():
        return render_template("tos.html")

    @app.route("/privacy")
    def privacypolicy():
        return render_template("privacypolicy.html")

    @app.route("/aphorisms")
    def aphorisms():
        rows = Aphorism.query.order_by(Aphorism.id).all()
        return render_template("aphorisms.html", aphorisms=rows)

    @app.route("/vefxistyaosani")
    def vefxistyaosani():
        first = (
            db.session.query(VefxistyaosaniLine.chapter_id)
            .filter(VefxistyaosaniLine.chapter_id.isnot(None))
            .order_by(VefxistyaosaniLine.chapter_id)
            .first()
        )
        if first:
            return redirect(
                url_for("reader.vefxistyaosani_chapter", chapter=first[0])
            )
        return render_template("vefxistyaosani.html", stanzas={})

    @app.route("/vefxistyaosani/all")
    def vefxistyaosani_all():
        lines = (
            VefxistyaosaniLine.query.order_by(
                VefxistyaosaniLine.chapter_id,
                VefxistyaosaniLine.strophe_id,
                VefxistyaosaniLine.line_id,
            ).all()
        )
        stanzas = defaultdict(list)
        for line in lines:
            stanzas[(line.chapter_id, line.strophe_id)].append(line)
        return render_template("vefxistyaosani.html", stanzas=dict(stanzas))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        full_name = email = grade = ""
        min_len = _password_min_length()

        if request.method == "POST":
            full_name = (request.form.get("full_name") or "").strip()
            email = (request.form.get("email") or "").strip().lower()
            grade = (request.form.get("grade") or "").strip()
            password = request.form.get("password") or ""
            confirm_password = request.form.get("confirm_password") or ""

            errors = []
            if not full_name:
                errors.append("Enter your full name.")
            if not email:
                errors.append("Enter your email address.")
            elif db.session.query(
                User.query.filter(func.lower(User.email) == email).exists()
            ).scalar():
                errors.append("An account with that email already exists.")
            if len(password) < min_len:
                errors.append(f"Password must be at least {min_len} characters.")
            if password != confirm_password:
                errors.append("Passwords do not match.")

            if errors:
                for error in errors:
                    flash(error, "error")
            else:
                user = User(
                    full_name=full_name,
                    email=email,
                    grade=grade or None,
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash("Your account is ready.", "success")
                return redirect(url_for("index"))

        return render_template(
            "register.html",
            full_name=full_name,
            email=email,
            grade=grade,
            password_min_length=min_len,
        )

    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit("5 per minute", methods=["POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        email = ""

        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            remember = bool(request.form.get("remember"))

            user = User.query.filter(func.lower(User.email) == email).first()
            if user and user.check_password(password):
                login_user(user, remember=remember)
                next_page = request.args.get("next")
                if (
                    next_page
                    and next_page.startswith("/")
                    and not next_page.startswith("//")
                ):
                    return redirect(next_page)
                return redirect(url_for("index"))

            logger.warning(
                "Failed login for email=%s ip=%s",
                email or "(empty)",
                request.headers.get("X-Forwarded-For", request.remote_addr),
            )
            flash("Incorrect email or password.", "error")

        return render_template("login.html", email=email)

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("index"))

    @app.route("/forgot-password", methods=["GET", "POST"])
    @limiter.limit("3 per hour", methods=["POST"])
    def forgot_password():
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            user = User.query.filter(func.lower(User.email) == email).first()
            if user:
                token = make_reset_token(user.id, user.session_version or 0)
                reset_url = url_for("reset_password", token=token, _external=True)
                send_email(
                    to=user.email,
                    subject="Reset your Litera password",
                    text_body=(
                        "Use this link to choose a new password. "
                        "It expires in one hour and can only be used once.\n\n"
                        f"{reset_url}\n\n"
                        "If you did not ask for a reset, ignore this email."
                    ),
                )
            # Identical response whether or not the account exists.
            return _check_your_email_response()

        return render_template("forgot_password.html")

    @app.route("/reset-password/<token>", methods=["GET", "POST"])
    @limiter.limit("3 per hour", methods=["POST"])
    def reset_password(token):
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        payload = load_reset_token(token)
        user = None
        if payload:
            user = db.session.get(User, int(payload["uid"]))
            if user is None or int(user.session_version or 0) != int(
                payload.get("sv", -1)
            ):
                user = None

        if user is None:
            flash(
                "That reset link is invalid or has expired. Request a new one.",
                "error",
            )
            return redirect(url_for("forgot_password"))

        min_len = _password_min_length()

        if request.method == "POST":
            password = request.form.get("password") or ""
            confirm = request.form.get("confirm_password") or ""
            errors = []
            if len(password) < min_len:
                errors.append(f"Password must be at least {min_len} characters.")
            if password != confirm:
                errors.append("Passwords do not match.")
            if errors:
                for error in errors:
                    flash(error, "error")
            else:
                # set_password bumps session_version, invalidating this token
                # and every active session.
                user.set_password(password)
                db.session.commit()
                flash("Password updated. You can log in now.", "success")
                return redirect(url_for("login"))

        return render_template(
            "reset_password.html",
            token=token,
            password_min_length=min_len,
        )

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    @app.route("/robots.txt")
    def robots_txt():
        body = (
            "User-agent: *\n"
            "Allow: /\n"
            f"Sitemap: {url_for('sitemap_xml', _external=True)}\n"
        )
        return app.response_class(body, mimetype="text/plain")

    @app.route("/sitemap.xml")
    def sitemap_xml():
        static_endpoints = (
            "index",
            "about",
            "contact",
            "tos",
            "privacypolicy",
            "aphorisms",
            "literature.index",
            "reader.vefxistyaosani_index",
        )
        urls = [url_for(ep, _external=True) for ep in static_endpoints]
        urls.append(url_for("shushaniki.reader", chapter=1, _external=True))
        for work in Work.query.with_entities(Work.slug).order_by(Work.slug).all():
            urls.append(
                url_for("literature.start", slug=work.slug, _external=True)
            )

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        for loc in urls:
            lines.append("  <url>")
            lines.append(f"    <loc>{loc}</loc>")
            lines.append("  </url>")
        lines.append("</urlset>")
        return app.response_class("\n".join(lines) + "\n", mimetype="application/xml")

    # Permanent redirects for the retired mockup pages.
    def _retired():
        return redirect(url_for("literature.index"), code=301)

    for path in RETIRED_PATHS:
        app.add_url_rule(
            path,
            endpoint="retired_" + path.strip("/"),
            view_func=_retired,
        )

    # Old legal URLs.
    app.add_url_rule(
        "/tos",
        endpoint="retired_tos",
        view_func=lambda: redirect(url_for("tos"), code=301),
    )
    app.add_url_rule(
        "/privacypolicy",
        endpoint="retired_privacypolicy",
        view_func=lambda: redirect(url_for("privacypolicy"), code=301),
    )


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return render_template("500.html"), 500

    @app.errorhandler(413)
    def too_large(_error):
        return (
            "Upload too large. Maximum size is "
            f"{app.config.get('MAX_CONTENT_LENGTH', 0) // (1024 * 1024)} MB.",
            413,
        )

    @app.errorhandler(429)
    def rate_limited(_error):
        flash("Too many attempts. Wait a minute and try again.", "error")
        return redirect(request.referrer or url_for("index")), 429


def register_security_headers(app: Flask) -> None:
    @app.before_request
    def assign_csp_nonce():
        g.csp_nonce = os.urandom(16).hex()

    @app.after_request
    def set_headers(response):
        nonce = getattr(g, "csp_nonce", "")
        # When the compiled stylesheet is present we no longer need the Tailwind
        # CDN. Inline styles remain in a few reader meters, so style-src still
        # allows 'unsafe-inline' until those are converted to CSS variables.
        script_src = f"'self' 'nonce-{nonce}'"
        if not app.config.get("TAILWIND_BUILT"):
            script_src += " https://cdn.tailwindcss.com 'unsafe-inline'"

        csp = (
            "default-src 'self'; "
            "img-src 'self' data: https://www.transparenttextures.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            f"script-src {script_src}; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers.setdefault("Content-Security-Policy", csp)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        # Long-cache fingerprinted/static assets; HTML stays revalidated.
        if request.path.startswith("/static/"):
            response.headers.setdefault(
                "Cache-Control", "public, max-age=604800, immutable"
            )
        elif response.mimetype == "text/html":
            response.headers.setdefault(
                "Cache-Control", "no-cache, must-revalidate"
            )

        return response


def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db():
        """Create any missing tables and backfill new auth columns on SQLite."""
        db.create_all()
        _ensure_user_auth_columns()
        click.echo("Schema is up to date.")

    def _ensure_user_auth_columns() -> None:
        """Add password-reset columns to existing DBs that pre-date Alembic."""
        from sqlalchemy import inspect, text

        inspector = inspect(db.engine)
        if "users" not in inspector.get_table_names():
            return
        cols = {c["name"] for c in inspector.get_columns("users")}
        statements = []
        if "password_reset_at" not in cols:
            statements.append(
                "ALTER TABLE users ADD COLUMN password_reset_at DATETIME"
            )
        if "session_version" not in cols:
            statements.append(
                "ALTER TABLE users ADD COLUMN session_version INTEGER DEFAULT 0 NOT NULL"
            )
        if not statements:
            return
        with db.engine.begin() as conn:
            for statement in statements:
                conn.execute(text(statement))

    @app.cli.command("messages")
    @click.option("--all", "show_all", is_flag=True, help="Include handled ones.")
    def messages(show_all):
        """Print contact-form submissions."""
        query = ContactMessage.query.order_by(ContactMessage.created_at.desc())
        if not show_all:
            query = query.filter_by(handled=False)
        rows = query.all()
        if not rows:
            click.echo("No messages.")
            return
        for row in rows:
            click.echo(f"[{row.created_at:%Y-%m-%d %H:%M}] {row.name} <{row.email}>")
            if row.subject:
                click.echo(f"  Subject: {row.subject}")
            click.echo(f"  {row.body}\n")

    @app.cli.command("delete-user")
    @click.argument("email")
    @click.option("--yes", is_flag=True, help="Skip the confirmation prompt.")
    def delete_user(email, yes):
        """Delete an account by email (privacy-policy fulfilment)."""
        email = (email or "").strip().lower()
        user = User.query.filter(func.lower(User.email) == email).first()
        if user is None:
            raise click.ClickException(f"No account for {email!r}.")
        if not yes:
            click.confirm(
                f"Delete account {user.full_name!r} <{user.email}>?",
                abort=True,
            )
        db.session.delete(user)
        db.session.commit()
        click.echo(f"Deleted {email}.")


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
