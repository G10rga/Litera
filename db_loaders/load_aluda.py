#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load ალუდა ქეთელაური (Vazha-Pshavela, 1888) into aluda_lines,
plus its provenance row in text_sources.

Input is the Wikisource plain-text dump: one verse line per blank-separated
block, with roman section markers I..VI on their own lines.

Three things in the file are NOT verse and are stored as metadata rather than
as lines:
  - the subtitle '(ხევსურების ცხოვრებიდან)' before section I
  - the composition date '1888 წ.' at the end
  - the roman markers themselves

    python db_loaders/load_aluda.py --dry-run
    python db_loaders/load_aluda.py --show 1
    python db_loaders/load_aluda.py
"""

from __future__ import print_function

import argparse
import hashlib
import io
import json
import os
import re
import sys

DEFAULT_TEXT = "static/Literature/aluda-qetelauri/text.txt"
DEFAULT_META = "static/Literature/aluda-qetelauri/source.json"

WORK_SLUG = "aluda-ketelauri"
WORK_TITLE = u"\u10d0\u10da\u10e3\u10d3\u10d0 \u10e5\u10d4\u10d7\u10d4\u10da\u10d0\u10e3\u10e0\u10d8"
WORK_AUTHOR = u"\u10d5\u10d0\u10df\u10d0-\u10ff\u10e8\u10d0\u10d5\u10d4\u10da\u10d0"

ROMAN_RE = re.compile(r"^([IVXLC]+)\.?$")
SUBTITLE_RE = re.compile(r"^\(.+\)$")
DATE_RE = re.compile(u"^\\d{3,4}\\s*\u10ec\\.?$")
DASH_RE = re.compile(u"^[-\u2010\u2011\u2013\u2014]")

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


def read_meta(path, raw):
    """Load source.json and verify its checksum against the text actually read."""
    meta = {}
    if os.path.exists(path):
        with io.open(path, encoding="utf-8") as handle:
            meta = json.load(handle)
    else:
        print("note: %s not found; provenance will be incomplete" % path)
        return meta, None

    recorded = meta.get("sha256")
    actual = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    if recorded and recorded != actual:
        print("WARNING: checksum mismatch between source.json and the text file.")
        print("   recorded: %s" % recorded)
        print("   actual  : %s" % actual)
        print("   The text has changed since it was retrieved. Verify before loading.")
        return meta, False
    return meta, bool(recorded)


def parse(raw):
    """Return (lines, subtitle, composed, skipped).

    lines is a list of dicts: section, line_index, line_global, text,
    is_dialogue.
    """
    lines = []
    subtitle = None
    composed = None
    skipped = []

    section = None
    line_index = 0
    line_global = 0

    for block in re.split(r"\n\s*\n", raw):
        text = " ".join(p.strip() for p in block.split("\n") if p.strip())
        if not text:
            continue

        roman = ROMAN_RE.match(text)
        if roman and roman_to_int(roman.group(1)) is not None:
            section = roman_to_int(roman.group(1))
            line_index = 0
            continue

        # Metadata lines, only meaningful outside/at the edges of the poem.
        if section is None and SUBTITLE_RE.match(text):
            subtitle = text.strip("()")
            continue
        if DATE_RE.match(text):
            composed = text
            continue

        if section is None:
            skipped.append(text)
            continue

        line_index += 1
        line_global += 1
        lines.append({
            "section": section,
            "line_index": line_index,
            "line_global": line_global,
            "text": text,
            "is_dialogue": bool(DASH_RE.match(text)),
        })

    return lines, subtitle, composed, skipped


def validate(lines):
    problems = []
    if not lines:
        problems.append("no verse lines parsed")
        return problems

    sections = sorted(set(l["section"] for l in lines))
    expected = list(range(1, max(sections) + 1))
    if sections != expected:
        problems.append("section numbers are %s, expected %s"
                        % (sections, expected))

    globals_ = [l["line_global"] for l in lines]
    if globals_ != list(range(1, len(lines) + 1)):
        problems.append("line_global is not a gapless 1..N sequence")

    for section in sections:
        indices = [l["line_index"] for l in lines if l["section"] == section]
        if indices != list(range(1, len(indices) + 1)):
            problems.append("section %d line_index is not gapless" % section)

    blank = [l for l in lines if not l["text"].strip()]
    if blank:
        problems.append("%d empty line(s)" % len(blank))

    return problems


def report(lines, subtitle, composed, skipped, checksum_ok):
    print("verse lines parsed: %d" % len(lines))
    print("")
    print("   sec  lines  dialogue  first line")
    print("   ---  -----  --------  ----------")
    for section in sorted(set(l["section"] for l in lines)):
        rows = [l for l in lines if l["section"] == section]
        spoken = len([l for l in rows if l["is_dialogue"]])
        print(u"   %3d  %5d  %8d  %s"
              % (section, len(rows), spoken, rows[0]["text"][:38]))

    print("")
    print(u"subtitle : %s" % (subtitle or "(none)"))
    print(u"composed : %s" % (composed or "(none)"))
    print("dialogue lines total: %d"
          % len([l for l in lines if l["is_dialogue"]]))

    if checksum_ok is True:
        print("checksum : matches source.json")
    elif checksum_ok is False:
        print("checksum : MISMATCH")
    else:
        print("checksum : not recorded")

    if skipped:
        print("")
        print("unclassified blocks before section I: %d" % len(skipped))
        for text in skipped[:5]:
            print(u"   %s" % text[:60])


def bootstrap():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    for path in (root, here, os.getcwd()):
        if path not in sys.path:
            sys.path.insert(0, path)

    import models
    db = models.db

    missing = [name for name in ("AludaLine", "TextSource")
               if not hasattr(models, name)]
    if missing:
        print("ERROR: models.py is missing: %s" % ", ".join(missing))
        print("       Paste them in from aluda_model.py, then run")
        print("       flask db migrate -m 'aluda tables' && flask db upgrade")
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

    return app, db, models.AludaLine, models.TextSource


def write_rows(lines, subtitle, composed, meta, replace):
    app, db, AludaLine, TextSource = bootstrap()

    with app.app_context():
        from sqlalchemy import inspect
        present = inspect(db.engine).get_table_names()
        for table in ("aluda_lines", "text_sources"):
            if table not in present:
                print("ERROR: table '%s' does not exist." % table)
                print("       Run: flask db migrate -m 'aluda tables'")
                print("            flask db upgrade")
                return 1

        if replace:
            removed = AludaLine.query.delete()
            db.session.commit()
            print("--replace: deleted %d existing line(s)" % removed)

        existing = AludaLine.query.count()
        if existing and not replace:
            print("aluda_lines already holds %d rows." % existing)
            print("Pass --replace to reload from scratch. Nothing written.")
            return 1

        for row in lines:
            db.session.add(AludaLine(
                section=row["section"],
                line_index=row["line_index"],
                line_global=row["line_global"],
                text=row["text"],
                is_dialogue=row["is_dialogue"],
            ))

        source = TextSource.query.filter_by(work=WORK_SLUG).first()
        if source is None:
            source = TextSource(work=WORK_SLUG)
            db.session.add(source)
        source.title = WORK_TITLE
        source.author = WORK_AUTHOR
        source.subtitle = subtitle
        source.composed = composed
        source.source = meta.get("source")
        source.url = meta.get("url")
        source.revision = str(meta.get("revision") or "") or None
        source.retrieved = meta.get("retrieved")
        source.license = meta.get("transcription_license")
        source.sha256 = meta.get("sha256")

        db.session.commit()

        total = AludaLine.query.count()
        print("")
        print("inserted lines: %d" % len(lines))
        print("aluda_lines total: %d" % total)
        print("sections present : %s"
              % sorted(set(r.section for r in AludaLine.query.all())))
        print(u"text_sources row : %s / %s / %s"
              % (source.work, source.license, source.revision))

    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=DEFAULT_TEXT)
    parser.add_argument("--meta", default=DEFAULT_META)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--replace", action="store_true",
                        help="empty aluda_lines before loading")
    parser.add_argument("--show", type=int, metavar="N",
                        help="print section N in full and exit")
    parser.add_argument("--force", action="store_true",
                        help="load even if the checksum does not match")
    args = parser.parse_args()

    raw = read_text(args.file)
    meta, checksum_ok = read_meta(args.meta, raw)
    lines, subtitle, composed, skipped = parse(raw)

    if args.show:
        rows = [l for l in lines if l["section"] == args.show]
        if not rows:
            print("section %d not found" % args.show)
            return 1
        print("--- section %d (%d lines) ---" % (args.show, len(rows)))
        for row in rows:
            marker = "  " if not row["is_dialogue"] else "> "
            print(u"%s%4d  %s" % (marker, row["line_index"], row["text"]))
        return 0

    report(lines, subtitle, composed, skipped, checksum_ok)

    problems = validate(lines)
    print("")
    if problems:
        print("PROBLEMS:")
        for problem in problems:
            print("   - %s" % problem)
    else:
        print("structure looks consistent: %d lines across %d sections"
              % (len(lines), len(set(l["section"] for l in lines))))

    if args.dry_run:
        print("")
        print("dry run -- nothing written.")
        return 0

    if problems:
        print("")
        print("refusing to write while problems remain.")
        return 1

    if checksum_ok is False and not args.force:
        print("")
        print("refusing to write: checksum mismatch. Pass --force to override.")
        return 1

    print("")
    return write_rows(lines, subtitle, composed, meta, args.replace)


if __name__ == "__main__":
    sys.exit(main())
