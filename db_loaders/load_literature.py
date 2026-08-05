#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load every work in static/literature/ into works + text_units.

One loader for all works, driven by manifest.json. Verse and prose share a code
path because they differ only in what a unit is -- a line or a paragraph -- and
that is detected from the text rather than assumed from the genre.

Parsing is LINE-BASED, with wrapped lines reassembled into paragraphs. This
matters: khevisberi-gocha is hard-wrapped at ~62 characters, so only 32% of its
lines end in sentence punctuation. Treating each line as a paragraph would slice
sentences in half. Conversely, treating each blank-separated block as one unit
misses section markers, because in that file a marker can sit on the first line
of a block instead of alone between blank lines -- which is exactly how section
III went missing on the first run.

Structures handled, all of them present in the source files:

  verse, no sections        memento-mori, tano-tatano
  verse, roman sections     aluda-qetelauri
  prose, roman sections     gogia-uishvili, khevisberi-gocha (hard-wrapped)
  prose, 'I თავი' sections   shvlis-nukris-naambobi

Section I is usually UNLABELLED: markers begin at II and the opening text is
implicitly section I. Numbering follows each marker's roman value, so this comes
out right either way.

Non-body blocks are classified rather than silently dropped: title line,
subtitle, trailing date, trailing attribution, numbered footnotes.

    python db_loaders/load_literature.py --dry-run
    python db_loaders/load_literature.py --work gogia-uishvili --show 2
    python db_loaders/load_literature.py --all
"""

from __future__ import print_function

import argparse
import hashlib
import io
import json
import os
import re
import sys

DEFAULT_ROOT = os.path.join("static", "literature")

ROMAN_RE = re.compile(r"^([IVXLC]+)\.?$")
ROMAN_TAVI_RE = re.compile(u"^([IVXLC]+)\\s*\u10d7\u10d0\u10d5\u10d8\\.?$")
NUM_TAVI_RE = re.compile(u"^(\\d+)\\s*\u10d7\u10d0\u10d5\u10d8\\.?$")
DATE_RE = re.compile(u"^\\d{3,4}\\s*\u10ec\\.?$")
SUBTITLE_RE = re.compile(r"^\((.+)\)$")
FOOTNOTE_RE = re.compile(r"^(\d+)\s+\S")
DASH_RE = re.compile(u"^[-\u2010\u2011\u2013\u2014]")

# Legacy Georgian fonts (AcadNusx and friends) decode as Latin-1 accented
# letters. Two of the khevisberi-gocha footnotes are in this state.
MOJIBAKE_RE = re.compile(u"[\u00c0-\u00ff]")

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
    return total or None


def squash(text):
    """Normalise for comparison only: letters, lowercased."""
    return re.sub(u"[^\u10a0-\u10ffa-zA-Z]", "", text or "").lower()


def match_marker(line):
    """Return (value, label) if the line is a section marker, else None."""
    for pattern, convert in ((ROMAN_RE, roman_to_int),
                             (ROMAN_TAVI_RE, roman_to_int),
                             (NUM_TAVI_RE, int)):
        match = pattern.match(line)
        if match:
            value = convert(match.group(1))
            return (value, line) if value else None
    return None


# ------------------------------------------------------------------ reading

def read_manifest(root):
    path = os.path.join(root, "manifest.json")
    if not os.path.exists(path):
        print("note: no manifest.json at %s" % path)
        return {}
    data = json.load(io.open(path, encoding="utf-8"))
    return dict((w["id"], w) for w in data.get("works", []))


def read_work(root, slug):
    folder = os.path.join(root, slug)
    tpath = os.path.join(folder, "text.txt")
    mpath = os.path.join(folder, "source.json")

    if not os.path.exists(tpath):
        return None, {}, None

    raw = io.open(tpath, encoding="utf-8").read()
    raw = raw.replace(u"\ufeff", u"").replace("\r\n", "\n")

    meta = {}
    if os.path.exists(mpath):
        meta = json.load(io.open(mpath, encoding="utf-8"))

    recorded = meta.get("sha256")
    if not recorded:
        checksum = None
    else:
        checksum = (recorded == hashlib.sha256(raw.encode("utf-8")).hexdigest())

    return raw, meta, checksum


# ------------------------------------------------------------------ parsing

def split_records(raw):
    """Walk lines, emitting ('marker', value, label) and ('para', text).

    A paragraph is a run of consecutive non-blank, non-marker lines joined with
    single spaces -- this reassembles hard-wrapped prose. A marker on its own
    line ends the current paragraph, whether or not a blank line follows it.
    """
    records = []
    buffer = []

    def flush():
        if buffer:
            records.append(("para", " ".join(buffer)))
            del buffer[:]

    for line in raw.split("\n"):
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        marker = match_marker(stripped)
        if marker:
            flush()
            records.append(("marker", marker[0], marker[1]))
            continue
        buffer.append(stripped)

    flush()
    return records


def detect_kind(records):
    """verse if the paragraphs are uniformly short single lines."""
    paras = [r[1] for r in records if r[0] == "para"]
    if not paras:
        return "prose"
    lens = sorted(len(p) for p in paras)
    return "verse" if lens[len(lens) // 2] < 60 else "prose"


def parse(raw, titles, author):
    """Return a dict describing one work."""
    records = split_records(raw)
    kind = detect_kind(records)
    unit_kind = "line" if kind == "verse" else "paragraph"

    has_markers = any(r[0] == "marker" for r in records)
    para_positions = [i for i, r in enumerate(records) if r[0] == "para"]
    last_para = para_positions[-1] if para_positions else -1
    tail_start = para_positions[-8] if len(para_positions) >= 8 else 0

    title_squashed = set(squash(t) for t in titles if t)
    author_tokens = [squash(t) for t in re.split(r"[\s-]+", author or "")
                     if len(squash(t)) > 3]

    units = []
    notes = []
    subtitle = None
    composed = None
    attribution = None
    title_line = None

    section = None
    section_label = None
    unit_index = 0
    unit_global = 0
    seen_text = False

    for position, record in enumerate(records):
        if record[0] == "marker":
            section, section_label = record[1], record[2]
            unit_index = 0
            continue

        text = record[1].strip()
        if not text:
            continue

        # --- title line, only before any body text ---
        if not seen_text and squash(text) in title_squashed:
            title_line = text
            continue

        # --- parenthesised subtitle, only before any body text ---
        if not seen_text and SUBTITLE_RE.match(text) and len(text) < 80:
            subtitle = SUBTITLE_RE.match(text).group(1)
            continue

        # --- trailing composition date ---
        if DATE_RE.match(text):
            composed = text
            continue

        # --- trailing author attribution ---
        # Restricted to the very last paragraph and to short lines. An earlier
        # version allowed the last two paragraphs, and swallowed the Memento
        # Mori line "ჩემი გვარი: გრანელი - პოეზიას დარჩება," as an
        # attribution because the poet names himself inside the poem.
        if (position == last_para and author_tokens
                and len(text.split()) <= 5
                and any(token in squash(text) for token in author_tokens)):
            attribution = text
            continue

        # --- numbered footnotes, only near the end ---
        if FOOTNOTE_RE.match(text) and position >= tail_start:
            notes.append(text)
            continue

        seen_text = True

        effective = section
        if effective is None and has_markers:
            effective = 1  # unlabelled opening section

        unit_index += 1
        unit_global += 1
        units.append({
            "section": effective,
            "section_label": section_label if section is not None else None,
            "unit_index": unit_index,
            "unit_global": unit_global,
            "kind": unit_kind,
            "text": text,
            "is_dialogue": bool(DASH_RE.match(text)),
        })

    # Footnotes are kept, numbered after the body, so nothing is discarded.
    for note in notes:
        unit_global += 1
        units.append({
            "section": None,
            "section_label": None,
            "unit_index": unit_global,
            "unit_global": unit_global,
            "kind": "note",
            "text": note,
            "is_dialogue": False,
        })

    sections = sorted(set(u["section"] for u in units
                          if u["section"] is not None))

    return {
        "units": units,
        "kind": kind,
        "subtitle": subtitle,
        "composed": composed,
        "attribution": attribution,
        "title_line": title_line,
        "notes": notes,
        "sections": sections,
    }


def validate(parsed, raw):
    """Return (problems, warnings).

    problems block the load. warnings describe defects in the transcription
    that are not the loader's business to fix silently.
    """
    problems = []
    warnings = []
    units = parsed["units"]

    if not units:
        problems.append("no units parsed")
        return problems, warnings

    globals_ = [u["unit_global"] for u in units]
    if globals_ != list(range(1, len(units) + 1)):
        problems.append("unit_global is not a gapless 1..N sequence")

    sections = parsed["sections"]
    if sections:
        expected = list(range(1, max(sections) + 1))
        if sections != expected:
            gaps = [n for n in expected if n not in sections]
            problems.append("missing section(s) %s of 1..%d"
                            % (gaps, max(sections)))

    if any(not u["text"].strip() for u in units):
        problems.append("empty unit text")

    if raw.count(u"\ufffd"):
        problems.append("%d replacement characters (broken encoding)"
                        % raw.count(u"\ufffd"))

    # Legacy font mojibake, e.g. AcadNusx read as Latin-1.
    mojibake = MOJIBAKE_RE.findall(raw)
    if len(mojibake) > 20:
        affected = [u["unit_global"] for u in units
                    if len(MOJIBAKE_RE.findall(u["text"])) > 5]
        warnings.append(
            "%d legacy-font characters (AcadNusx mojibake) in unit(s) %s -- "
            "these need re-transcribing, not loading"
            % (len(mojibake), affected[:6]))

    # A Latin letter wedged inside a Georgian word is a transcription typo.
    mixed = re.findall(u"[\u10a0-\u10ff][a-zA-Z][\u10a0-\u10ff]", raw)
    if mixed:
        warnings.append("%d Latin letter(s) inside Georgian words: %s"
                        % (len(mixed), ", ".join(mixed[:5])))

    body = [u for u in units if u["kind"] != "note"]
    if body and parsed["kind"] == "prose":
        lens = sorted(len(u["text"]) for u in body)
        median = lens[len(lens) // 2]
        if median > 900:
            warnings.append(
                "median paragraph is %d characters -- the source uses blank "
                "lines sparsely, so paragraph granularity is coarse" % median)

    return problems, warnings


# ------------------------------------------------------------------ reporting

def report(slug, info, parsed, problems, warnings, checksum):
    units = parsed["units"]
    body = [u for u in units if u["kind"] != "note"]
    print("-" * 70)
    print(u"%-26s %s" % (slug, info.get("title", "")))
    print("-" * 70)
    print(u"  author    : %s" % info.get("author", "?"))
    print(u"  kind      : %-6s %d units" % (parsed["kind"], len(body)))
    if parsed["sections"]:
        print(u"  sections  : %d  (1..%d)"
              % (len(parsed["sections"]), max(parsed["sections"])))
    else:
        print(u"  sections  : none")
    if body:
        lens = sorted(len(u["text"]) for u in body)
        print(u"  unit chars: median %d  max %d"
              % (lens[len(lens) // 2], lens[-1]))
    if parsed["title_line"]:
        print(u"  title line: dropped (%s)" % parsed["title_line"][:44])
    if parsed["subtitle"]:
        print(u"  subtitle  : %s" % parsed["subtitle"])
    if parsed["composed"]:
        print(u"  composed  : %s" % parsed["composed"])
    if parsed["attribution"]:
        print(u"  attributed: %s" % parsed["attribution"])
    if parsed["notes"]:
        print(u"  footnotes : %d (kind='note')" % len(parsed["notes"]))
    print(u"  dialogue  : %d" % len([u for u in body if u["is_dialogue"]]))
    print(u"  checksum  : %s"
          % ("MATCH" if checksum else
             ("MISMATCH" if checksum is False else "not recorded")))
    for warning in warnings:
        print(u"  WARNING   : %s" % warning)
    for problem in problems:
        print(u"  PROBLEM   : %s" % problem)
    if body:
        print(u"  opens     : %s" % body[0]["text"][:54])


# ------------------------------------------------------------------ database

def bootstrap():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    for path in (root, here, os.getcwd()):
        if path not in sys.path:
            sys.path.insert(0, path)

    import models
    db = models.db

    missing = [n for n in ("Work", "TextUnit") if not hasattr(models, n)]
    if missing:
        print("ERROR: models.py is missing: %s" % ", ".join(missing))
        print("       Paste them in from literature_model.py, then:")
        print("         flask db migrate -m 'works and text_units'")
        print("         flask db upgrade")
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

    return app, db, models.Work, models.TextUnit


def write_all(payloads, replace):
    app, db, Work, TextUnit = bootstrap()

    with app.app_context():
        from sqlalchemy import inspect
        present = inspect(db.engine).get_table_names()
        for table in ("works", "text_units"):
            if table not in present:
                print("ERROR: table '%s' does not exist." % table)
                print("       Run: flask db migrate -m 'works and text_units'")
                print("            flask db upgrade")
                return 1

        written = 0
        skipped = 0

        for slug, info, parsed, meta in payloads:
            work = Work.query.filter_by(slug=slug).first()

            if work is not None and not replace:
                print("  %-26s already loaded (%d units) -- skipped"
                      % (slug, work.units.count()))
                skipped += 1
                continue

            if work is None:
                work = Work(slug=slug)
                db.session.add(work)
            else:
                work.units.delete()

            work.title = info.get("title") or parsed["title_line"] or slug
            work.author = info.get("author")
            work.subtitle = parsed["subtitle"]
            work.kind = parsed["kind"]
            work.composed = parsed["composed"]
            work.death_year = info.get("death_year")
            work.source = meta.get("source")
            work.url = meta.get("url")
            work.revision = str(meta.get("revision") or "") or None
            work.retrieved = meta.get("retrieved")
            work.license = meta.get("transcription_license")
            work.sha256 = meta.get("sha256")
            work.unit_count = len(parsed["units"])
            work.section_count = len(parsed["sections"])

            db.session.flush()  # need work.id before adding units

            for unit in parsed["units"]:
                db.session.add(TextUnit(
                    work_id=work.id,
                    section=unit["section"],
                    section_label=unit["section_label"],
                    unit_index=unit["unit_index"],
                    unit_global=unit["unit_global"],
                    kind=unit["kind"],
                    text=unit["text"],
                    is_dialogue=unit["is_dialogue"],
                ))

            written += len(parsed["units"])
            print("  %-26s %-6s %5d units  %2d sections"
                  % (slug, parsed["kind"], len(parsed["units"]),
                     len(parsed["sections"])))

        db.session.commit()

        print("")
        print("units written    : %d" % written)
        if skipped:
            print("works skipped    : %d  (pass --replace to reload)" % skipped)
        print("works in database: %d" % Work.query.count())
        print("units in database: %d" % TextUnit.query.count())

    return 0


# ------------------------------------------------------------------ main

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--work", help="load only this slug")
    parser.add_argument("--all", action="store_true", help="write every work")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--replace", action="store_true",
                        help="reload works already in the database")
    parser.add_argument("--show", type=int, metavar="N",
                        help="with --work, print section N and exit")
    parser.add_argument("--force", action="store_true",
                        help="load despite a checksum mismatch")
    parser.add_argument("--skip-problems", action="store_true",
                        help="load the clean works and leave the broken ones")
    args = parser.parse_args()

    root = args.root
    if not os.path.isdir(root):
        print("ERROR: no such directory: %s" % root)
        return 1

    manifest = read_manifest(root)

    slugs = sorted(d for d in os.listdir(root)
                   if os.path.isdir(os.path.join(root, d)))
    if args.work:
        if args.work not in slugs:
            print("ERROR: %s not found under %s" % (args.work, root))
            print("available: %s" % ", ".join(slugs))
            return 1
        slugs = [args.work]

    print("root     : %s" % root)
    print("folders  : %d" % len(slugs))
    print("manifest : %d works listed" % len(manifest))
    if manifest and not args.work:
        absent = [s for s in manifest
                  if s not in slugs and "path" not in manifest[s]]
        ready = [s for s in absent if manifest[s].get("status") == "ready"]
        if absent:
            print("missing  : %d listed but not on disk, %d of them status=ready"
                  % (len(absent), len(ready)))
            if ready:
                print("           %s" % ", ".join(sorted(ready)))
    print("")

    payloads = []
    blocked = []

    for slug in slugs:
        raw, meta, checksum = read_work(root, slug)
        if raw is None:
            print("%-26s no text.txt -- skipped" % slug)
            continue

        info = dict(manifest.get(slug, {}))
        info.setdefault("title", meta.get("page"))

        parsed = parse(raw, [info.get("title"), meta.get("page")],
                       info.get("author"))
        problems, warnings = validate(parsed, raw)

        if args.show is not None and args.work:
            rows = [u for u in parsed["units"] if u["section"] == args.show]
            if not rows:
                print("section %d not found (sections: %s)"
                      % (args.show, parsed["sections"]))
                return 1
            print("--- %s section %d (%d units) ---"
                  % (slug, args.show, len(rows)))
            for row in rows:
                mark = "> " if row["is_dialogue"] else "  "
                print(u"%s%4d  %s" % (mark, row["unit_index"], row["text"][:100]))
            return 0

        report(slug, info, parsed, problems, warnings, checksum)

        if problems:
            blocked.append(slug)
        elif checksum is False and not args.force:
            print("  BLOCKED   : checksum mismatch; pass --force to override")
            blocked.append(slug)
        else:
            payloads.append((slug, info, parsed, meta))

    body = sum(len([u for u in p[2]["units"] if u["kind"] != "note"])
               for p in payloads)

    print("")
    print("=" * 70)
    print("loadable : %d      blocked: %d" % (len(payloads), len(blocked)))
    if blocked:
        print("blocked  : %s" % ", ".join(blocked))
    print("units ready: %d" % body)

    if args.dry_run or not (args.all or args.work):
        print("")
        print("nothing written. Pass --all to load everything,")
        print("or --work <slug> to load one.")
        return 0

    if blocked and not args.skip_problems:
        print("")
        print("refusing to write while %d work(s) have problems." % len(blocked))
        print("Fix them, or pass --skip-problems to load the rest.")
        return 1

    if not payloads:
        print("nothing loadable.")
        return 1

    print("")
    return write_all(payloads, args.replace)


if __name__ == "__main__":
    sys.exit(main())
