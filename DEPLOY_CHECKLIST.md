# Deployment readiness — remaining host-side checklist

Code for the Litera deployment checklist is in this repository.
Items below still need action on your machine / hosting provider.

## Secrets (host dashboard)

- [ ] Generate: `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] Set `SECRET_KEY` and `DATABASE_URL` in the host only (never commit)
- [ ] Confirm `.env` is ignored: `git check-ignore -v .env`
- [ ] Rotate any live instance still using `litera-dev-secret-change-me`

## SMTP (password reset)

- [ ] Choose Resend, Postmark, or SES
- [ ] Fill `MAIL_*` from `.env.example` on the host

## PostgreSQL

- [ ] Provision Postgres and note the connection cap
- [ ] `flask --app app db upgrade` (Procfile release does this)
- [ ] Re-run every importer in `db_loaders/` against Postgres
- [ ] Set `DB_POOL_SIZE` if the plan is small (default 5)
- [ ] Automated dumps + one tested restore
- [ ] Staging environment before production import

## Monitoring / HTTPS

- [ ] Point uptime checks at `/healthz`
- [ ] Set `SENTRY_DSN` if you want Sentry
- [ ] Confirm HSTS + secure cookies behind HTTPS (`ProductionConfig`)

## Content (legal)

- [ ] Walk `CONTENT_LICENSING.md` and every `source.json`
- [ ] Clear modern renderings and scholarly glosses before public launch

## Local one-time

```bash
cp .env.example .env
# set SECRET_KEY
flask --app app init-db   # or: flask --app app db upgrade
npm install && npm run build:css   # already committed; rebuild after template class changes
pytest
```

See `OPS.md` and `README.md` for details.
