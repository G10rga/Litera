#!/usr/bin/env python3
"""
Reset the Litera Postgres schema and reload all content from db_loaders.

Run from the project root with DATABASE_URL and FLASK_CONFIG=production set:

    python scripts/reset_and_load_db.py --reset-schema
    python scripts/reset_and_load_db.py --load-only   # schema already migrated

Requires requirements-dev.txt (pandas) for CSV loaders.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)


def _run_loader(script: str, *args: str) -> None:
    cmd = [sys.executable, os.path.join("db_loaders", script), *args]
    print(f"\n>>> {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=PROJECT_ROOT)


def reset_schema() -> None:
    from app import app, db

    print("Dropping all tables…")
    with app.app_context():
        db.drop_all()
    print("Running flask db upgrade…")
    subprocess.check_call(["flask", "--app", "app", "db", "upgrade"], cwd=PROJECT_ROOT)


def load_all_data() -> None:
    """Load every importer in dependency order."""
    _run_loader("load_vefxistyaosani.py")
    _run_loader(
        "load_modern_chapters.py",
        "--file",
        "static/Literature/modernised.md",
        "--dedupe",
        "--replace",
    )
    _run_loader(
        "load_glossary.py",
        "--csv",
        "db_loaders/db_checkers/gloss_occurrences.csv",
    )
    _run_loader("load_literature.py", "--all")
    _run_loader("load_shushaniki.py")
    _run_loader(
        "load_shushaniki_glossary.py",
        "--file",
        "db_loaders/db_literature/shushaniki_glossary.csv",
        "--replace",
    )
    _run_loader("load_shushaniki_modern.py", "--replace", "--file", "static/Literature/shushaniki_modernised.md")
    _run_loader("load_aphorisms.py")


def verify_counts() -> int:
    from app import app
    from models import (
        Aphorism,
        GlossOccurrence,
        GlossTerm,
        ModernChapter,
        ShushanikiGloss,
        ShushanikiModern,
        ShushanikiText,
        User,
        VefxistyaosaniLine,
        Work,
        db,
    )

    checks = [
        ("users", User),
        ("works", Work),
        ("vefxistyaosani_lines", VefxistyaosaniLine),
        ("modern_chapters", ModernChapter),
        ("gloss_terms", GlossTerm),
        ("gloss_occurrences", GlossOccurrence),
        ("shushaniki_main", ShushanikiText),
        ("shushaniki_glosses", ShushanikiGloss),
        ("shushaniki_modern", ShushanikiModern),
        ("aphorisms", Aphorism),
    ]

    print("\n=== Database counts ===")
    ok = True
    with app.app_context():
        for label, model in checks:
            try:
                count = db.session.query(model).count()
            except Exception as exc:
                print(f"  {label}: ERROR — {exc}")
                ok = False
                continue
            print(f"  {label}: {count}")
            if label != "users" and count == 0:
                ok = False
    if ok:
        print("\nContent tables populated. users may be 0 until someone registers.")
    else:
        print("\nSome tables are empty or missing — check loader output above.")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset-schema",
        action="store_true",
        help="DROP all tables and re-run Alembic migrations (destructive).",
    )
    parser.add_argument(
        "--load-only",
        action="store_true",
        help="Skip schema reset; only run db_loaders (schema must exist).",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Print row counts and exit.",
    )
    args = parser.parse_args()

    if args.verify_only:
        return verify_counts()

    if args.reset_schema:
        reset_schema()
        load_all_data()
        return verify_counts()

    if args.load_only:
        load_all_data()
        return verify_counts()

    parser.error("Pass --reset-schema, --load-only, or --verify-only.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
