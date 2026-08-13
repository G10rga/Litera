"""Litera application factory.

Run locally:
    flask --app app run --debug
Initialise the schema:
    flask --app app init-db
Production:
    gunicorn wsgi:application
"""

import os
from collections import defaultdict

import click
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func

from config import get_config
from models import (
    Aphorism,
    ContactMessage,
    User,
    VefxistyaosaniLine,
    db,
)

load_dotenv()

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Log in to continue."
login_manager.login_message_category = "error"

csrf = CSRFProtect()

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

    try:
        from flask_migrate import Migrate

        Migrate(app, db)
    except ImportError:  # migrations are optional in development
        pass

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
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def register_routes(app: Flask) -> None:  # noqa: C901 - flat route table
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/contact", methods=["GET", "POST"])
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
            if len(password) < 8:
                errors.append("Password must be at least 8 characters.")
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
            "register.html", full_name=full_name, email=email, grade=grade
        )

    @app.route("/login", methods=["GET", "POST"])
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
                if next_page and next_page.startswith("/") and not next_page.startswith("//"):
                    return redirect(next_page)
                return redirect(url_for("index"))

            flash("Incorrect email or password.", "error")

        return render_template("login.html", email=email)

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("index"))

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}, 200

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
        return render_template("500.html"), 413


def register_security_headers(app: Flask) -> None:
    # Google Fonts, the transparenttextures backgrounds and (when the CSS has
    # not been built) the Tailwind CDN are the only third-party origins used.
    csp = (
        "default-src 'self'; "
        "img-src 'self' data: https://www.transparenttextures.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    @app.after_request
    def set_headers(response):
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
        return response


def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db():
        """Create any missing tables. Safe to run repeatedly."""
        db.create_all()
        click.echo("Schema is up to date.")

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


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
