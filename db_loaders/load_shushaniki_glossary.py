#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load the შუშანიკის წამება glossary into shushaniki_glosses.

Run from the project root, the same way as the other loaders:

    python db_loaders/load_shushaniki_glossary.py --dry-run
    python db_loaders/load_shushaniki_glossary.py

This writes ONLY to shushaniki_glosses. It does not touch gloss_terms,
vefxistyaosani_lines or anything else, and it never deletes rows unless you
explicitly pass --replace.

Why no occurrences table this time
---------------------------------
utvalavi anchored each gloss to a strophe through its `ganm_*` id, so the
glosses had positions and those positions could drift. NPLG ships one global
word list that the page applies by string match wherever a word appears, so
there is no authored position to store. Occurrences here are derived from the
text at render time (or by a later loader), not scraped.

Input: shushaniki_glossary.csv from extract_shushaniki.py
       columns: term, gloss, is_phrase, repaired, original_key
"""

from __future__ import print_function

import argparse
import csv
import io
import os
import re
import sys
from collections import Counter, OrderedDict

DEFAULT_CSV = "shushaniki_glossary.csv"
DEFAULT_SOURCE = "nplg"

# shushaniki_glosses.term is String(256); the longest term measured is 77 characters.
TERM_LIMIT = 256


# ------------------------------------------------------------- bootstrap

def bootstrap():
    """Return (app, db, GlossTerm) with an application context available.

    The script lives in db_loaders/ but is run from the project root, so the
    parent directory has to be importable before `models` can be found.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    for path in (root, here, os.getcwd()):
        if path not in sys.path:
            sys.path.insert(0, path)

    try:
        from models import db, ShushanikiGloss
    except ImportError as exc:
        print("could not import from models.py: %s" % exc)
        print("run this from the project root: python db_loaders/%s"
              % os.path.basename(__file__))
        raise SystemExit(1)

    # Prefer the real app so the database URI matches everything else.
    app = None
    try:
        from app import app as real_app
        app = real_app
    except Exception as exc:
        print("note: could not import app.py (%s); building a minimal app" % exc)
        from flask import Flask
        app = Flask(__name__)
        uri = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(
            root, "instance", "vepkhvi.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = uri
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)

    return app, db, ShushanikiGloss


# ------------------------------------------------------------------ read

DASH_RE = re.compile(u"[-\u2010\u2011\u2013\u2014]")


def truthy(value):
    return str(value).strip().lower() in ("1", "true", "yes", "t")


def read_rows(path):
    if not os.path.exists(path):
        print("not found: %s" % path)
        print("generate it first: python extract_shushaniki.py --write")
        raise SystemExit(1)

    rows = []
    skipped = []
    with io.open(path, encoding="utf-8-sig", newline="") as fh:
        for lineno, row in enumerate(csv.DictReader(fh), start=2):
            term = " ".join((row.get("term") or "").split())
            gloss = " ".join((row.get("gloss") or "").split())
            try:
                from sanitize import clean_gloss
                term = clean_gloss(term)
                gloss = clean_gloss(gloss)
            except ImportError:
                pass
            if not term or not gloss:
                skipped.append((lineno, row))
                continue
            if len(term) > TERM_LIMIT:
                skipped.append((lineno, row))
                continue
            rows.append({
                "term": term,
                "gloss": gloss,
                # A hyphenated compound such as ზრახვა-ყო is a single token in
                # the text, so it is NOT a phrase for hover purposes. Only
                # whitespace makes a term multi-token.
                "is_phrase": " " in term,
                "repaired": truthy(row.get("repaired")),
                "original_key": (row.get("original_key") or "").strip(),
            })

    return rows, skipped


def dedupe(rows):
    """Collapse exact (term, gloss) repeats, which the source has 44 of."""
    seen = OrderedDict()
    collapsed = 0
    for row in rows:
        key = (row["term"], row["gloss"])
        if key in seen:
            collapsed += 1
            continue
        seen[key] = row
    return list(seen.values()), collapsed


# --------------------------------------------------------------- reporting

def describe(rows, collapsed, skipped):
    print("=" * 66)
    print("PARSED")
    print("=" * 66)
    print("  usable rows:        %d" % len(rows))
    print("  collapsed repeats:  %d" % collapsed)
    print("  skipped rows:       %d" % len(skipped))
    for lineno, row in skipped[:5]:
        print("     line %d: %r" % (lineno, row))

    phrases = [r for r in rows if r["is_phrase"]]
    words = [r for r in rows if not r["is_phrase"]]
    hyphenated = [r for r in words if DASH_RE.search(r["term"])]
    repaired = [r for r in rows if r["repaired"]]

    print("")
    print("  single tokens:      %d  (of which hyphenated compounds: %d)"
          % (len(words), len(hyphenated)))
    print("  multi-word phrases: %d" % len(phrases))
    print("  repaired headwords: %d" % len(repaired))

    long_terms = [r for r in phrases if len(r["term"].split()) >= 5]
    print("  sentence-length citations (5+ words): %d" % len(long_terms))
    print("     these will never fire on word hover -- they are quotation")
    print("     glosses and need phrase matching or a separate display")

    counts = Counter(len(r["term"].split()) for r in rows)
    print("  words per term: %s" % dict(sorted(counts.items())))


def preview(rows, limit):
    print("")
    print("=" * 66)
    print("PREVIEW (first %d)" % limit)
    print("=" * 66)
    for row in rows[:limit]:
        flag = "P" if row["is_phrase"] else " "
        fixed = "*" if row["repaired"] else " "
        print(u"  %s%s %-34s %s" % (flag, fixed, row["term"][:34], row["gloss"][:44]))


# ------------------------------------------------------------------ write

def load(app, db, Model, rows, source, replace):
    with app.app_context():
        if replace:
            removed = Model.query.delete()
            db.session.commit()
            print("  --replace: deleted %d existing rows" % removed)

        existing = set()
        for term, gloss in db.session.query(Model.term, Model.gloss).all():
            existing.add((term, gloss))
        print("  rows already in shushaniki_glosses: %d" % len(existing))

        fresh = []
        for row in rows:
            key = (row["term"], row["gloss"])
            if key in existing:
                continue
            existing.add(key)
            fresh.append(row)

        for row in fresh:
            db.session.add(Model(
                term=row["term"],
                gloss=row["gloss"],
                is_phrase=row["is_phrase"],
                source=source,
            ))

        db.session.commit()

        print("")
        print("  inserted: %d" % len(fresh))
        print("  skipped as already present: %d" % (len(rows) - len(fresh)))

        total = Model.query.count()
        phrases = Model.query.filter_by(is_phrase=True).count()
        print("")
        print("  shushaniki_glosses total:  %d" % total)
        print("  of which phrases:          %d" % phrases)
        print("  single tokens:             %d" % (total - phrases))

        # Confirm the separation actually holds.
        try:
            from models import GlossTerm
            leaked = GlossTerm.query.filter(
                GlossTerm.source.in_(("nplg", "nplg-shushaniki"))
            ).count()
            print("  stray NPLG rows still in gloss_terms: %d" % leaked)
            if leaked:
                print("     run db_loaders/cleanup_gloss_terms.py --write")
        except Exception:
            pass

        print("")
        print("  spot check:")
        for probe in (u"პიტიახში", u"რაჟამს", u"ზრახვა-ყო"):
            hit = Model.query.filter_by(term=probe).all()
            if hit:
                for item in hit:
                    print(u"     %-16s -> %s" % (item.term, item.gloss[:46]))
            else:
                print(u"     %-16s -> NOT FOUND" % probe)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=DEFAULT_CSV)
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--dry-run", action="store_true",
                        help="parse and report without touching the database")
    parser.add_argument("--replace", action="store_true",
                        help="empty shushaniki_glosses before loading")
    parser.add_argument("--preview", type=int, default=15)
    args = parser.parse_args()

    rows, skipped = read_rows(args.file)
    rows, collapsed = dedupe(rows)

    describe(rows, collapsed, skipped)
    if args.preview:
        preview(rows, args.preview)

    if args.dry_run:
        print("")
        print("dry run -- nothing written. Drop --dry-run to load.")
        return 0

    app, db, Model = bootstrap()
    print("")
    print("=" * 66)
    print("LOADING as source=%r" % args.source)
    print("=" * 66)
    load(app, db, Model, rows, args.source, args.replace)
    return 0


if __name__ == "__main__":
    sys.exit(main())
