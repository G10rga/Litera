# How to apply this refactor

This archive is a drop-in set of files for `github.com/G10rga/Litera`, produced
because the connected GitHub token is read-only: branch creation and file writes
both returned `403 Resource not accessible by personal access token`, so no
branch, commit or pull request could be made for you.

If you want the change as a real PR instead, re-authorise the GitHub integration
with **`contents: write`** and **`pull_requests: write`** and say so — the same
tree can then be pushed to a `deploy-ready` branch.

---

## 1. Delete these files from the repo

Hand-written mockups with no data, no route worth keeping, and invented
statistics. Their URLs now `301` to `/literature`, so nothing 404s.

```
templates/practicetests.html
templates/examprep.html
templates/studyguide.html
templates/cheracteranalysis.html
templates/moderntraslations.html
templates/syllabus.html
static/litera_book_monogram_logo1.png     # unreferenced, 536 KB
```

```bash
git rm templates/practicetests.html templates/examprep.html \
       templates/studyguide.html templates/cheracteranalysis.html \
       templates/moderntraslations.html templates/syllabus.html \
       static/litera_book_monogram_logo1.png
```

## 2. Copy this archive over the repo root

Every file in the archive replaces or adds to the repo at the same path.
`db_loaders/`, `static/Literature/`, `static/litera_book_monogram_logo.png`,
`LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` and `SECURITY.md` are
untouched and are not included.

**Overwritten**

```
app.py                          models.py                requirements.txt
.gitignore                      README.md
static/main.js                  static/styles.css
templates/base.html             templates/index.html     templates/about.html
templates/contact.html          templates/tos.html       templates/privacypolicy.html
templates/login.html            templates/register.html  templates/aphorisms.html
templates/vefxistyaosani.html   templates/vefxistyaosani_chapter.html
templates/literature_index.html templates/literature_reader.html
templates/shushaniki.html
```

**New**

```
config.py            wsgi.py              Procfile           .env.example
requirements-dev.txt package.json         tailwind.config.js
static/src/input.css static/tailwind-cdn-config.js
templates/404.html   templates/500.html   APPLY.md
```

## 3. Build the stylesheet

The Tailwind CDN `<script>` is gone from `base.html`. Build the real stylesheet
and commit it, so deploys need no Node step:

```bash
npm install
npm run build:css      # writes static/dist/app.css
git add -f static/dist/app.css
```

Until that file exists, `base.html` falls back to the CDN automatically — the
site works, but do not ship in that state.

## 4. Local check

```bash
pip install -r requirements-dev.txt
cp .env.example .env
flask --app app init-db
flask --app app run --debug
```

Walk `/`, `/about`, `/contact`, `/terms`, `/privacy`, `/aphorisms`,
`/literature/`, `/vefxistyaosani`, `/shushaniki/1`, `/login`, `/register`, and a
URL that does not exist (for the 404 page).

## 5. Deploy

Set `APP_ENV=production`, `SECRET_KEY`, `DATABASE_URL`, optionally
`CONTACT_EMAIL`. Then `gunicorn wsgi:application`. The `Procfile` runs
`flask --app app init-db` as its release step.

---

# What changed, and why

## Blocking deployment before

| Problem | Fix |
| --- | --- |
| `SECRET_KEY` fell back to the hardcoded string `litera-dev-secret-change-me`, so a production deploy signed sessions with a key that is public in the repo | `config.py`; `ProductionConfig.init_app` raises if `SECRET_KEY` is unset |
| Database URI hardcoded to `sqlite:///vepkhvi.db` — on most hosts that file is wiped on every restart | `DATABASE_URL` env var, `postgres://` → `postgresql+psycopg://` normalised, SQLite only as the dev fallback |
| `db.create_all()` ran at import time on every worker boot | moved to `flask init-db`, plus the `Procfile` release step |
| No WSGI entry point and no `ProxyFix` — behind a proxy Flask built `http://` URLs and secure cookies never stuck | `wsgi.py` |
| Tailwind loaded from `cdn.tailwindcss.com`, which prints “do not use in production” and re-generates the entire stylesheet in the browser on every page view | `tailwind.config.js` + `package.json`, compiled to `static/dist/app.css` |
| No CSRF protection on `/login` or `/register` | `Flask-WTF` `CSRFProtect`, `csrf_token()` in every form, `/logout` is now POST-only |
| Session cookies not marked `Secure`, no `SameSite`, no security headers | set in `config.py`; CSP, HSTS, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` added in `app.py` |
| No error pages — users saw Werkzeug's default | `templates/404.html`, `templates/500.html`, handlers registered |
| `pandas` in `requirements.txt`, imported only by the offline importers, adding ~50 MB and a NumPy build to every deploy | moved to `requirements-dev.txt` |
| Nav and footer logos loaded from an ephemeral `lh3.googleusercontent.com/aida-public/…` URL that will 404 without warning | local `static/litera_book_monogram_logo.png` |

## Correctness bugs

| Problem | Fix |
| --- | --- |
| `class ModernSection` was **nested inside `class TextUnit`** in `models.py`, so `models.ModernSection` did not exist and every blueprint had to wrap its import in `try/except` | dedented to module level. The blueprints' optional-import guards can now be simplified, though they still work as written |
| `vefxistyaosani_chapter.html` computed progress as `chapter / chapters|length * 100`, which is wrong whenever chapter numbers are not 1..N, and raised `ZeroDivisionError` when no chapters were loaded | position index within `chapters`, guarded against an empty list |
| The same template hardcoded `/vefxistyaosani/{{ c.number }}` instead of `url_for` | `url_for('reader.vefxistyaosani_chapter', …)` everywhere |
| Stanza cards carried an inline `onclick="this.classList.toggle('is-flipped')"` **and** a `main.js` handler doing the same thing, so a click toggled twice and appeared to do nothing | inline handler removed; `main.js` is the only place that toggles it, and it keeps `aria-expanded` in sync |
| `main.js` hijacked any `.h-full.bg-primary` inside a `.bg-outline-variant` parent as a scroll bar, which silently animated the chapter-position meter | removed; only `#progress-bar` and `#scrollProgress` are driven |
| Reveal animations set `opacity-0` / `opacity: 0.4` from JS, so with JS disabled or errored, content stayed invisible | reveals are additive — the hidden class is applied only when `IntersectionObserver` exists and motion is not reduced; no-JS renders fully visible |
| `text-aphorism` was used in `aphorisms.html` but `fontSize.aphorism` was never defined, so it did nothing | added to the Tailwind theme |
| `no-scrollbar`, `font-hankenGrotesk` and `font-ebGaramond` were used but never defined | defined in `tailwind.config.js` / `input.css` |
| Flash messages were suppressed on `/login` and `/register` by `request.endpoint not in ['login','register']`, which is exactly where validation errors appear | one flash region for the whole site |
| `aphorisms.html` used `dir="rtl"`, `text-right` and `flex-row-reverse`. Georgian is left-to-right | removed |
| Disabled prev/next navigation was `<a href="#">`, focusable and clickable | `<span aria-disabled="true">` |
| `initTosScrollSpy`, `initCharacterSearch`, `initStudyGuideNav`, `initSyllabusReveal`, `initExamPrepRadios`, `initModernTranslations`, `initDemoCard` — all bound to pages that were deleted or never had the hooks | deleted; `main.js` went from 18 initialisers to 10, all of which have live targets |
| `.dual-view-grid`, `.notebook-lines`, `.skeleton`, `.skeleton-pulse` and three duplicate keyframe blocks were dead CSS | removed |

## Fabricated content removed

Every one of these was a number or a feature with nothing behind it:

- **“AI Study Assistant · Active Beta”** with a pulsing green dot, on the home page. No such feature exists anywhere in the codebase.
- **“100% Curriculum Aligned”, “50+ Essay Templates”, “1.5k+ Key Quotes”** on the about page. Invented.
- **An 85%-full “Essay Templates” progress bar** on the home page — a hardcoded `w-[85%]` div measuring nothing.
- **Invented “Modern Analysis” prose** presented beside a hardcoded couplet on the home page, as if it came from the database.
- **The contact form's “Message Sent” confirmation**, which was a `setTimeout` in `main.js`; the form had no `action` and posted nowhere. There is now a real `/contact` route, a `contact_messages` table, and a confirmation that says the message is stored and that replies are not automatic.
- **A “STUDY NOTES & ESSAY PRACTICE” textarea** in the chapter reader that no code ever persisted.
- **Terms and privacy pages describing subscriptions, billing and a “Scholar” tier**, plus data-rights promises with no mechanism behind them. Rewritten to describe what the app actually stores: name, email, optional school year, a password hash, and contact messages — and to state plainly that deletion requests are handled by hand and that no password reset exists.
- **README claiming “Nothing is built yet”** while listing an AI study assistant as a planned feature. Rewritten to match the code.

## Leaked internals removed

User-facing pages were printing developer diagnostics:

- `literature_index.html`: `ბაზაში ნაწარმოები არ არის. გაუშვით load_literature.py --all`
- `shushaniki.html`: `ცხრილი shushaniki_main ცარიელია`, and a warning naming the `shushaniki_glosses` table when no glosses matched

Both now say, in Georgian, that the text has not been prepared yet.

## Consistency

- Every page extends `base.html` and inherits one nav, one footer, one flash region and one set of meta tags. Nav clearance is handled once in `base.html` (`pt-16`), not re-guessed per page as `pt-32`.
- Nav and footer link only to pages that exist: Library, `ვეფხისტყაოსანი`, `შუშანიკის წამება`, Aphorisms, About, Contact, Terms, Privacy.
- Interface chrome is in English throughout; the texts, and the reader labels that sit beside them, are in Georgian, with `lang="ka"` on those blocks so screen readers and hyphenation behave.
- Every `<img>` has a real `alt`; the old `data-alt` attributes holding AI image prompts are gone. Decorative icons are `aria-hidden="true"`.
- Both auth pages use the same field markup, the same `text-on-primary` button, and the same password-visibility toggle.

---

# Known gaps, stated rather than hidden

1. **No password reset.** The login page and the terms page both say so.
2. **No tests.** There is no test suite in the repo and I did not invent one.
3. **Two design systems still coexist.** Marketing and auth pages use the Tailwind palette; the three readers use the hand-written `.reader` module with its own parchment variables. They are visually reconciled, not merged. Merging them is a larger piece of work and would change how the texts look.
4. **No i18n layer.** The English/Georgian split is by hand, not by `gettext`.
5. **Contact messages are stored, not emailed.** Read them with `flask --app app messages`. Wiring SMTP is a config change, not a code change.
6. **`static/dist/app.css` is not in this archive** — it needs a `npm run build:css` on your machine, since Node is not available here.
7. **The `db_loaders/` blueprints are unchanged.** They still guard the `ModernSection` import in a `try/except`, which is now unnecessary but harmless.
