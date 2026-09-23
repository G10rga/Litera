# Operations runbook

Host-side steps that cannot live only in application code.

## Secrets

1. Generate: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Set `SECRET_KEY`, `DATABASE_URL`, and `MAIL_*` in the host dashboard only.
3. Confirm `.env` is gitignored: `git check-ignore -v .env`
4. Rotate any instance still using `litera-dev-secret-change-me`.

## PostgreSQL

1. Provision Postgres; note the connection cap.
2. Set `DATABASE_URL` and optionally `DB_POOL_SIZE` / `DB_MAX_OVERFLOW`.
3. `flask --app app db upgrade` (Procfile `release` phase does this).
4. Re-run every importer in `db_loaders/` against Postgres and fix type issues.
5. Schedule automated dumps and **test a restore** quarterly.
6. Keep a staging database; do not discover importer breakage in production.

### Full reset (schema + all content)

Use this when auth fails with 500 after a manual SQLite→Postgres copy. Do **not** import a `.db` file into Postgres; use Alembic + loaders instead.

On the server (`~/litera`, venv active, `FLASK_CONFIG=production`, `.env` with `DATABASE_URL`):

```bash
cd ~/litera
source .venv/bin/activate
pip install -r requirements.txt   # includes pandas for db_loaders
export FLASK_CONFIG=production

# Destructive: drops all tables, migrates, loads CSV/MD content
python scripts/reset_and_load_db.py --reset-schema

# Or, if schema is already correct but content is missing:
python scripts/reset_and_load_db.py --load-only

# Row counts only:
python scripts/reset_and_load_db.py --verify-only

sudo systemctl restart litera.service
```

Load order (handled automatically by the script):

1. `load_vefxistyaosani.py`
2. `load_modern_chapters.py` → `static/Literature/modernised.md`
3. `load_glossary.py` → `db_loaders/db_checkers/gloss_occurrences.csv`
4. `load_literature.py --all`
5. `load_shushaniki.py`
6. `load_shushaniki_glossary.py`
7. `load_shushaniki_modern.py`
8. `load_aphorisms.py`

After reset, register a test account at `/register` and confirm `/healthz` returns `{"status":"ok"}`.

If `flask db upgrade` fails with `Can't locate revision identified by '…'`, the DB still has a stale `alembic_version` row. Re-run the reset script (it drops app tables and clears `alembic_version`). If the app DB user cannot drop that table, as postgres superuser:

```bash
sudo -u postgres psql -d YOUR_DB -c "DROP TABLE IF EXISTS alembic_version CASCADE;"
flask --app app db upgrade
python scripts/reset_and_load_db.py --load-only
```

## Email

Configure SMTP (Resend / Postmark / SES) via `MAIL_*` in `.env.example`.
Password reset silently no-ops (logs only) when `MAIL_SERVER` is empty.

## Monitoring

| Check | Target |
| --- | --- |
| Uptime | `GET /healthz` → `{"status":"ok"}` |
| Errors | Set `SENTRY_DSN` |
| Auth abuse | Failed logins are logged as `litera.auth` warnings |

## HTTPS

Behind TLS termination, `ProductionConfig` sets secure cookies and HSTS.
Confirm the reverse proxy forwards `X-Forwarded-Proto`.

## Account deletion

```bash
flask --app app delete-user user@example.com --yes
```
