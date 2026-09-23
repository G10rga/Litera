# Litera

**A reader for Georgian curriculum literature: the original text, a modern-Georgian rendering beside it, and archaic words glossed in place.**

> Status: deploy-ready. Auth includes password reset; rate limits, CI, and ops hooks are in place. Clear content licences before a public launch — see `CONTENT_LICENSING.md`.

---

## What it does

| Area | State |
| --- | --- |
| `ვეფხისტყაოსანი` reader | Working — per chapter, original strophes beside the modern rendering, positional glosses |
| `შუშანიკის წამება` reader | Working — 20 sections, two columns, NPLG glossary by word match |
| Library (`/literature`) | Working — imported works with provenance and modernisation percentage |
| Aphorisms | Working — numbered for citation |
| Accounts | Working — register, log in, log out, password reset (SMTP) |
| Contact form | Working — stored in DB; read with `flask messages` |

Deliberately **not** in the product: exam banks, essay templates, character-analysis mockups, AI assistant.

## Tech

| Layer | Choice |
| --- | --- |
| Backend | Python 3.11+, Flask 3, Flask-SQLAlchemy |
| Auth | Flask-Login, scrypt password hashes, timed reset tokens |
| Forms | Flask-WTF (CSRF) |
| Limits | Flask-Limiter (`5/min` login, `3/hour` contact + reset) |
| Database | PostgreSQL in production, SQLite locally; Alembic migrations |
| Frontend | Jinja, Tailwind → `static/dist/app.css`, vanilla JS |
| Serving | gunicorn via `wsgi.py` |

---

## Running locally

```bash
git clone https://github.com/G10rga/Litera.git
cd Litera

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env               # set SECRET_KEY for anything beyond toy use
flask --app app init-db            # or: flask --app app db upgrade
python db_loaders/load_literature.py --all

flask --app app run --debug
```

Open <http://127.0.0.1:5000>.

### Stylesheet

`static/dist/app.css` is committed. After changing template classes:

```bash
npm install
npm run build:css
```

---

## Deploying

See **`OPS.md`** for secrets, Postgres, backups, Sentry, and uptime.

| Variable | Required | Notes |
| --- | --- | --- |
| `FLASK_CONFIG` or `APP_ENV` | yes | `production` |
| `SECRET_KEY` | yes | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | yes | `postgres://` rewritten to `postgresql+psycopg://` |
| `MAIL_*` | for password reset | See `.env.example` (Resend / Postmark / SES) |
| `CONTACT_EMAIL` | no | Shown on contact / legal pages |
| `SENTRY_DSN` | no | Enables Sentry |
| `DB_POOL_SIZE` | no | Default `5` in production |

```bash
pip install -r requirements.txt
flask --app app db upgrade
gunicorn wsgi:application
```

The `Procfile` runs `db upgrade` on release. Import texts once against production with `requirements-dev.txt`.

`/healthz` returns `{"status":"ok"}`. Account deletion: `flask delete-user email@example.com --yes`.

---

## Design tokens

Marketing/auth pages use the crimson Tailwind palette. Long-form readers use the `.reader` parchment theme (`--parchment`, `--ink`, `--accent`). Those reader tokens are also registered in `tailwind.config.js` so the split is deliberate, not accidental.

## Licences

- **Code** — see `LICENSE`
- **Content** — see `CONTENT_LICENSING.md` (public-domain originals vs modern renderings / glosses)

---

*Built for Georgian students. @G10rga*
