"""WSGI entrypoint. Run with: gunicorn wsgi:application"""

from dotenv import load_dotenv

load_dotenv()

from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: E402

from app import create_app  # noqa: E402

application = create_app()

# Trust one layer of reverse proxy (Render/Fly/Heroku/nginx) so that
# url_for(_external=True), request.scheme and remote_addr are correct.
application.wsgi_app = ProxyFix(
    application.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Convenience alias so `gunicorn wsgi:app` also works.
app = application
