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
