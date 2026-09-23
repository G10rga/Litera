#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load the modernised შუშანიკის წამება into shushaniki_modern.

The source file is split by twenty markdown headings of the form

    # **I** თავი   ...   # **XX** თავი

which correspond one-to-one with sections I..XX of the original text. The
bold markers are inconsistent in the source (IV, VII, IX and X are not bold),
so the parser tolerates both forms rather than relying on the asterisks.

The text goes into shushaniki_modern, a table dedicated to this work. Nothing
else writes there, so a query cannot accidentally pick up Vefkhistkaosani
chapters the way a shared table allowed.

    python db_loaders/load_shushaniki_modern.py --dry-run
    python db_loaders/load_shushaniki_modern.py --show 1
    python db_loaders/load_shushaniki_modern.py
"""

from __future__ import print_function

import argparse
import io
import os
import re
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_FILE = os.path.join(
    PROJECT_ROOT, "static", "Literature", "shushaniki_modernised.md"
)

# Matches '# **I** თავი', '# IV თავი', '## **XX** თავი' and friends.
HEAD_RE = re.compile(
    u"^\\s*#+\\s*\\**\\s*([IVXLC]+)\\s*\\**\\s*(.*)$"
)

ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def roman_to_int(text):
    total = 0
    previous = 0
    for ch in reversed(text.upper()):
        value = ROMAN_VALUES.get(ch)
        if value is None:
            return None
        if value < previous:
            total -= value
        else:
            total += value
            previous = value
    return total


def read_text(path):
    if not os.path.exists(path):
        print("ERROR: file not found: %s" % path)
        sys.exit(1)
    with io.open(path, encoding="utf-8") as handle:
        return handle.read().replace(u"\ufeff", u"").replace("\r\n", "\n")


def parse(raw):
    """Return (chapters, intro_paragraphs).

    chapters is a list of dicts: number, roman, title, paragraphs.
    """
    chapters = []
    intro = []
    current = None

    for block in re.split(r"\n\s*\n", raw):
        block = block.strip()
        if not block:
            continue

        match = HEAD_RE.match(block)
        if match and roman_to_int(match.group(1)) is not None:
            number = roman_to_int(match.group(1))
            title = match.group(2).strip().strip("*").strip()
            current = {
                "number": number,
                "roman": match.group(1),
                "title": title,
                "paragraphs": [],
            }
            chapters.append(current)
            continue

        # Collapse hard-wrapped lines inside a paragraph into one line.
        text = " ".join(part.strip() for part in block.split("\n") if part.strip())
        if current is None:
            intro.append(text)
        else:
            current["paragraphs"].append(text)

    return chapters, intro


def validate(chapters):
    problems = []

    numbers = [c["number"] for c in chapters]
    if numbers != sorted(numbers):
        problems.append("chapters are not in ascending order: %s" % numbers)

    duplicates = set(n for n in numbers if numbers.count(n) > 1)
    if duplicates:
        problems.append("duplicate chapter numbers: %s" % sorted(duplicates))

    if numbers:
        expected = set(range(1, max(numbers) + 1))
        missing = sorted(expected - set(numbers))
        if missing:
            problems.append("missing chapter numbers: %s" % missing)

    for chapter in chapters:
        if not chapter["paragraphs"]:
            problems.append("chapter %d has no text" % chapter["number"])

    return problems


def report(chapters, intro):
    print("parsed chapters: %d" % len(chapters))
    if intro:
        print("preamble paragraphs before chapter I: %d" % len(intro))
    print("")
    print("   ch  roman   paras   chars   opening")
    print("   --  ------  -----   -----   -------")

    total_paras = 0
    total_chars = 0
    for chapter in chapters:
        text = "\n\n".join(chapter["paragraphs"])
        total_paras += len(chapter["paragraphs"])
        total_chars += len(text)
        opening = chapter["paragraphs"][0][:44] if chapter["paragraphs"] else ""
        print(u"   %2d  %-6s  %5d   %5d   %s"
              % (chapter["number"], chapter["roman"],
                 len(chapter["paragraphs"]), len(text), opening))

    print("")
    print("   totals: %d paragraphs, %d chars" % (total_paras, total_chars))


def bootstrap():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    for path in (root, here, os.getcwd()):
        if path not in sys.path:
            sys.path.insert(0, path)

    import models
    db = models.db

    if not hasattr(models, "ShushanikiModern"):
        print("ERROR: models.py has no ShushanikiModern class.")
        print("       Paste it in from shushaniki_modern_model.py, run")
        print("       db_loaders/create_shushaniki_table.py, then retry.")
        sys.exit(1)

    try:
        from app import app
    except Exception as exc:
        print("note: could not import app.py (%s); building a minimal app" % exc)
        from flask import Flask
        app = Flask(__name__)
        uri = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(
            root, "instance", "vepkhvi.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = uri
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)

    return app, db, models.ShushanikiModern


def write_rows(chapters, status, replace):
    app, db, Model = bootstrap()

    with app.app_context():
        from sqlalchemy import inspect
        if "shushaniki_modern" not in inspect(db.engine).get_table_names():
            print("ERROR: the shushaniki_modern table does not exist.")
            print("       Run: python db_loaders/create_shushaniki_table.py")
            return 1

        if replace:
            removed = Model.query.delete()
            db.session.commit()
            print("--replace: deleted %d existing rows" % removed)

        existing = {}
        for row in Model.query.all():
            existing[row.chapter_id] = row

        inserted = 0
        updated = 0
        for chapter in chapters:
            text = "\n\n".join(chapter["paragraphs"])
            title = chapter["title"] or None
            row = existing.get(chapter["number"])
            if row is None:
                db.session.add(Model(
                    chapter_id=chapter["number"],
                    title=title,
                    text=text,
                    review_status=status,
                ))
                inserted += 1
            else:
                row.text = text
                row.title = title
                row.review_status = status
                updated += 1

        db.session.commit()

        print("")
        print("inserted: %d" % inserted)
        print("updated : %d" % updated)

        total = Model.query.count()
        print("")
        print("shushaniki_modern rows: %d" % total)
        print("chapter ids present: %s"
              % sorted(r.chapter_id for r in Model.query.all()))

        # Confirm nothing of ours is still sitting in the shared table.
        try:
            from models import ModernChapter
            stray = ModernChapter.query.filter_by(
                source="shushaniki-modern").count()
            if stray:
                print("")
                print("NOTE: %d stray rows remain in modern_chapters." % stray)
                print("      Run: python db_loaders/cleanup_modern_chapters.py --write")
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=DEFAULT_FILE)
    parser.add_argument("--status", default="draft",
                        choices=["draft", "reviewed", "final"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--replace", action="store_true",
                        help="empty shushaniki_modern before loading")
    parser.add_argument("--show", type=int, metavar="N",
                        help="print chapter N in full and exit")
    args = parser.parse_args()

    raw = read_text(args.file)
    chapters, intro = parse(raw)

    if args.show:
        for chapter in chapters:
            if chapter["number"] == args.show:
                print(u"--- chapter %d (%s) ---"
                      % (chapter["number"], chapter["roman"]))
                for index, para in enumerate(chapter["paragraphs"], 1):
                    print(u"")
                    print(u"[%d] %s" % (index, para))
                return 0
        print("chapter %d not found" % args.show)
        return 1

    report(chapters, intro)

    problems = validate(chapters)
    print("")
    if problems:
        print("PROBLEMS:")
        for problem in problems:
            print("   - %s" % problem)
    else:
        print("structure looks consistent: %d chapters, no gaps or duplicates"
              % len(chapters))

    if intro:
        print("")
        print("NOTE: %d preamble paragraph(s) sit before chapter I and will NOT"
              % len(intro))
        print("      be loaded. This is editorial framing, not translated text:")
        print(u"      %s..." % intro[0][:70])

    if args.dry_run:
        print("")
        print("dry run -- nothing written.")
        return 0

    if problems:
        print("")
        print("refusing to write while problems remain.")
        return 1

    print("")
    return write_rows(chapters, args.status, args.replace)


if __name__ == "__main__":
    sys.exit(main())
