#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load modernised Vefxistyaosani prose into modern_chapters, one row per chapter.

Input is the numbered markdown export (modernised.md):

    1. <prose>

    2. <prose>
    ...

    chapters list - chapter 1 - 1-18 : დასაწყისი chapter 2 - 19 - 52 : ...
    chapter 3 - 53 - 62 : ...

The trailing "chapters list" block maps item numbers to chapters, which is the
only alignment this loader needs. Paragraphs belonging to one chapter are
joined with a blank line and stored as a single ModernChapter.text.

Two defects in the source file are repaired automatically:

  1. Fused items. Four items lost the blank line that separated them from the
     next, so items 30, 34, 36 and 38 each hold two paragraphs and the numbers
     31, 35, 37 and 39 are missing. Splitting on the internal newline restores
     a clean 1..103 with no gaps. Verified: the count of internal newlines
     equals the count of missing numbers, and each missing number is exactly
     one greater than a fused item.

  2. Orphan fragment. Item 94 is the single sentence
     "ავთანდილმა მეფეს მდაბლად თაყვანი სცა." which is repeated verbatim as the
     opening of item 95. --dedupe drops any item whose whole body is a prefix
     of the next item's body.

Usage
-----
    python db_loaders/load_modern_chapters.py --file modernised.md --dry-run
    python db_loaders/load_modern_chapters.py --file modernised.md --dedupe
    python db_loaders/load_modern_chapters.py --file modernised.md --show 2

--dry-run and --show need no database and no Flask, so you can sanity-check
the parse before touching vepkhvi.db.
"""

from __future__ import print_function

import argparse
import io
import os
import re
import sys


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------

ITEM_RE = re.compile(r"^(\d+)\.[ \t]*(.*)$", re.S)

# "chapter 3 - 53 - 62 : title"  and also  "chapter 6 - title"
CHAPTER_HEAD_RE = re.compile(r"chapter[ \t]*(\d+)[ \t]*[-\u2013\u2014][ \t]*", re.I)
CHAPTER_RANGE_RE = re.compile(r"^(\d+)[ \t]*[-\u2013\u2014][ \t]*(\d+)[ \t]*:?[ \t]*(.*)$", re.S)


def read_text(path):
    with io.open(path, "r", encoding="utf-8-sig") as fh:
        raw = fh.read()
    return raw.replace("\r\n", "\n").replace("\r", "\n")


def split_paragraphs(text):
    return [p.strip() for p in re.split(r"\n[ \t]*\n", text) if p.strip()]


def normalise_ws(s):
    return " ".join(s.split())


def parse_items(paragraphs):
    """Return (items, leftovers).

    items is a list of (number, body). Fused paragraphs are split on their
    internal newline and the follower is given the next sequential number.
    leftovers is every paragraph that did not begin with "<n>.".
    """
    items = []
    leftovers = []

    for para in paragraphs:
        m = ITEM_RE.match(para)
        if not m:
            leftovers.append(para)
            continue

        number = int(m.group(1))
        body = m.group(2)

        # Repair 1: a fused item holds several paragraphs joined by single
        # newlines. Emit each as its own item, numbering the followers
        # sequentially from the parent.
        chunks = [c.strip() for c in body.split("\n") if c.strip()]
        if not chunks:
            continue

        for offset, chunk in enumerate(chunks):
            # A follower may itself carry an explicit number; honour it.
            fm = ITEM_RE.match(chunk)
            if offset > 0 and fm:
                items.append((int(fm.group(1)), normalise_ws(fm.group(2))))
            else:
                items.append((number + offset, normalise_ws(chunk)))

    return items, leftovers


def parse_chapter_list(leftovers):
    """Parse the trailing 'chapters list' block.

    Returns a list of dicts: {chapter, first, last, title}.
    'first'/'last' are item numbers, not strophe numbers. A chapter written
    without a range (the final one) gets first=None and is filled in later.
    """
    blob = " ".join(normalise_ws(p) for p in leftovers)
    if not blob:
        return []

    chapters = []
    matches = list(CHAPTER_HEAD_RE.finditer(blob))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(blob)
        payload = blob[start:end].strip()

        rm = CHAPTER_RANGE_RE.match(payload)
        if rm:
            chapters.append(
                {
                    "chapter": int(m.group(1)),
                    "first": int(rm.group(1)),
                    "last": int(rm.group(2)),
                    "title": normalise_ws(rm.group(3)).strip(" :-"),
                }
            )
        else:
            chapters.append(
                {
                    "chapter": int(m.group(1)),
                    "first": None,
                    "last": None,
                    "title": normalise_ws(payload).strip(" :-"),
                }
            )

    return chapters


def close_ranges(chapters, max_item):
    """Fill in any chapter written without an explicit item range."""
    for i, ch in enumerate(chapters):
        if ch["first"] is not None:
            continue
        prev_last = chapters[i - 1]["last"] if i > 0 else 0
        next_first = None
        for later in chapters[i + 1 :]:
            if later["first"] is not None:
                next_first = later["first"]
                break
        ch["first"] = (prev_last or 0) + 1
        ch["last"] = (next_first - 1) if next_first else max_item
        ch["inferred"] = True
    return chapters


def drop_prefix_duplicates(items):
    """Drop any item whose entire body opens the following item."""
    kept = []
    dropped = []
    for i, (num, body) in enumerate(items):
        if i + 1 < len(items):
            nxt = items[i + 1][1]
            if body and nxt.startswith(body) and len(nxt) > len(body):
                dropped.append((num, body))
                continue
        kept.append((num, body))
    return kept, dropped


def group_by_chapter(items, chapters):
    """Return list of dicts: {chapter, title, first, last, bodies, missing}."""
    by_number = {}
    for num, body in items:
        by_number.setdefault(num, []).append(body)

    grouped = []
    for ch in chapters:
        bodies = []
        missing = []
        for n in range(ch["first"], ch["last"] + 1):
            if n in by_number:
                bodies.extend(by_number[n])
            else:
                missing.append(n)
        grouped.append(
            {
                "chapter": ch["chapter"],
                "title": ch["title"],
                "first": ch["first"],
                "last": ch["last"],
                "inferred": ch.get("inferred", False),
                "bodies": bodies,
                "missing": missing,
            }
        )
    return grouped


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------


def report_parse(items, leftovers, chapters, grouped, dropped):
    numbers = [n for n, _ in items]
    print("items parsed:        %d" % len(items))
    if numbers:
        lo, hi = min(numbers), max(numbers)
        print("numbering:           %d..%d" % (lo, hi))
        gaps = sorted(set(range(lo, hi + 1)) - set(numbers))
        dupes = sorted({n for n in numbers if numbers.count(n) > 1})
        print("gaps:                %s" % (gaps if gaps else "none"))
        print("duplicate numbers:   %s" % (dupes if dupes else "none"))
    print("non-item paragraphs: %d" % len(leftovers))
    print("chapters declared:   %d" % len(chapters))
    if dropped:
        print("dropped duplicates:  %d" % len(dropped))
        for num, body in dropped:
            print("    [%d] %s" % (num, body[:70]))
    print("")

    total_bodies = 0
    total_chars = 0
    print("  ch  items      para   chars  title")
    print("  --  ---------  ----  ------  -----")
    for g in grouped:
        chars = sum(len(b) for b in g["bodies"])
        total_bodies += len(g["bodies"])
        total_chars += chars
        flag = "*" if g["inferred"] else " "
        print(
            "  %2d%s %4d-%-4d %5d  %6d  %s"
            % (g["chapter"], flag, g["first"], g["last"], len(g["bodies"]), chars, g["title"][:44])
        )
        if g["missing"]:
            print("      MISSING item numbers: %s" % g["missing"])
    print("  --  ---------  ----  ------")
    print("  %20d %5d  %6d" % (len(grouped), total_bodies, total_chars))
    print("")
    print("  * item range inferred, not stated in the chapters list")


def show_chapter(grouped, chapter):
    for g in grouped:
        if g["chapter"] == chapter:
            print("chapter %d: %s" % (g["chapter"], g["title"]))
            print("items %d-%d, %d paragraphs" % (g["first"], g["last"], len(g["bodies"])))
            print("")
            for i, b in enumerate(g["bodies"], 1):
                print("[%d] %s" % (i, b))
                print("")
            return
    print("no chapter %d" % chapter, file=sys.stderr)


# --------------------------------------------------------------------------
# database
# --------------------------------------------------------------------------


def write_rows(grouped, source, status, replace):
    from app import app, db
    from models import ModernChapter

    inserted = 0
    updated = 0
    skipped = 0

    with app.app_context():
        for g in grouped:
            if not g["bodies"]:
                skipped += 1
                continue

            body = "\n\n".join(g["bodies"])

            row = ModernChapter.query.filter_by(
                source=source, chapter_id=g["chapter"]
            ).first()

            if row is None:
                db.session.add(
                    ModernChapter(
                        chapter_id=g["chapter"],
                        title=g["title"] or None,
                        text=body,
                        source=source,
                        review_status=status,
                    )
                )
                inserted += 1
            elif replace:
                row.text = body
                row.title = g["title"] or row.title
                row.review_status = status
                updated += 1
            else:
                skipped += 1

        db.session.commit()

        total = ModernChapter.query.filter_by(source=source).count()

    print("")
    print("inserted: %d" % inserted)
    print("updated:  %d" % updated)
    print("skipped:  %d  (already present; pass --replace to overwrite)" % skipped)
    print("modern_chapters rows for source '%s': %d" % (source, total))


# --------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description="Load modernised chapters into the DB.")
    ap.add_argument("--file", default="modernised.md", help="numbered markdown input")
    ap.add_argument("--source", default="utvalavi", help="provenance tag")
    ap.add_argument("--status", default="draft", choices=["draft", "reviewed", "final"])
    ap.add_argument("--dry-run", action="store_true", help="parse and report, write nothing")
    ap.add_argument("--dedupe", action="store_true", help="drop fragments repeated in the next item")
    ap.add_argument("--replace", action="store_true", help="overwrite chapters already loaded")
    ap.add_argument("--show", type=int, metavar="N", help="print chapter N and exit")
    args = ap.parse_args()

    if not os.path.exists(args.file):
        print("no such file: %s" % args.file, file=sys.stderr)
        return 1

    text = read_text(args.file)
    paragraphs = split_paragraphs(text)
    items, leftovers = parse_items(paragraphs)

    dropped = []
    if args.dedupe:
        items, dropped = drop_prefix_duplicates(items)

    chapters = parse_chapter_list(leftovers)
    if not chapters:
        print("no 'chapters list' block found -- cannot assign chapters", file=sys.stderr)
        return 1

    max_item = max(n for n, _ in items) if items else 0
    chapters = close_ranges(chapters, max_item)
    grouped = group_by_chapter(items, chapters)

    if args.show is not None:
        show_chapter(grouped, args.show)
        return 0

    report_parse(items, leftovers, chapters, grouped, dropped)

    orphans = [n for n, _ in items if not any(g["first"] <= n <= g["last"] for g in grouped)]
    if orphans:
        print("")
        print("WARNING: %d item(s) fall outside every chapter range: %s" % (len(orphans), orphans))

    if args.dry_run:
        print("")
        print("dry run -- nothing written")
        return 0

    write_rows(grouped, args.source, args.status, args.replace)
    return 0


if __name__ == "__main__":
    sys.exit(main())
