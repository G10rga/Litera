# Litera

**A reader for Georgian curriculum literature: the original text, a modern-Georgian rendering beside it, and archaic words glossed in place.**

> Status: working and deployable. Two full readers, a growing library, and no features advertised before they exist.

---

## What it does

| Area | State |
| --- | --- |
| `ვეფხისტყაოსანი` reader | Working — per chapter, original strophes beside the modern rendering, positional glosses from utvalavi |
| `შუშანიკის წამება` reader | Working — 20 sections, two columns, NPLG glossary applied by word match |
| Library (`/literature`) | Working — any work imported by `db_loaders/`, with provenance and a modernisation percentage |
| Aphorisms | Working — numbered for citation |
| Accounts | Working — register, log in, log out. No password reset yet |
| Contact form | Working — messages are stored in the database and read with `flask messages` |

Deliberately **not** in the product: exam-question banks, essay templates,
character-analysis pages, and an AI assistant. Earlier versions of the site had
pages for all four with nothing behind them; those pages were deleted and their
URLs now redirect to the library.

## Tech

| Layer | Choice |
| --- | --- |
| Backend | Python 3.11+, Flask 3, Flask-SQLAlchemy 2.0-style models |
| Auth | Flask-Login, Werkzeug password hashing |
| Forms | Flask-WTF (CSRF on every POST) |
| Database | PostgreSQL in production, SQLite locally |
| Frontend | Jinja templates, Tailwind CSS compiled to `static/dist/app.css`, ~250 lines of vanilla JS |
| Serving | gunicorn behind a reverse proxy, via `wsgi.py` |

There is no build step for JavaScript and no frontend framework.

---

## Running it locally

```bash
git clone https://github.com/G10rga/Litera.git
cd Litera

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt  # requirements.txt + pandas, for the importers

cp .env.example .env               # SECRET_KEY may stay blank in development

flask --app app init-db            # create the tables
python db_loaders/load_literature.py --all   # import the texts

flask --app app run --debug
```

The app comes up on <http://127.0.0.1:5000>.

### Stylesheet

`static/dist/app.css` is committed, so the site renders without Node installed.
After changing any template class, rebuild it:

```bash
npm install
npm run build:css      # or: npm run watch:css
```

If `static/dist/app.css` is missing, `base.html` falls back to the Tailwind CDN
so the site still renders — but do not ship that way.

---

## Deploying

1. Set the environment variables:

   | Variable | Required | Notes |
   | --- | --- | --- |
   | `APP_ENV` | yes | `production` |
   | `SECRET_KEY` | yes | `python -c "import secrets; print(secrets.token_hex(32))"`. Production refuses to boot without it |
   | `DATABASE_URL` | yes | `postgres://` and `postgresql://` are rewritten to `postgresql+psycopg://` automatically |
   | `CONTACT_EMAIL` | no | Address shown on the contact, terms and privacy pages |

2. Install and start:

   ```bash
   pip install -r requirements.txt
   flask --app app init-db
   gunicorn wsgi:application
   ```

   The included `Procfile` does both steps on Heroku-style platforms.

3. Import the texts once against the production database, using the same
   `DATABASE_URL`, with `pip install -r requirements-dev.txt` for pandas.

`wsgi.py` applies `ProxyFix`, so HTTPS detection and secure cookies work behind a
proxy. Security headers (CSP, HSTS, `X-Content-Type-Options`, `Referrer-Policy`,
`X-Frame-Options`) are set on every response. `/healthz` returns `{"status":"ok"}`
for uptime checks.

---

## Layout

```
app.py                 application factory, routes, CLI commands
config.py              per-environment config; production requires SECRET_KEY
wsgi.py                gunicorn entry point (ProxyFix)
models.py              all SQLAlchemy models
db_loaders/            blueprints (reader, literature, shushaniki) + import scripts
templates/             Jinja templates, all extending base.html
static/src/input.css   Tailwind source
static/dist/app.css    compiled stylesheet (committed)
static/main.js         progressive-enhancement JS; nothing depends on it to read
static/styles.css      hand-written CSS: the reader module and the gloss tooltips
```

## Texts and licences

Original texts are public domain. Each transcription is stored with its source
URL, revision and licence, and every reader page prints that provenance beneath
the text. Modern renderings carry a `draft` / `reviewed` / `final` status which
the reader displays rather than hides.

Corrections to a transcription or a gloss are the most useful contribution you
can make — see `CONTRIBUTING.md`.

---

*Built for Georgian students, by someone who remembers how hard exam season is. @G10rga*
