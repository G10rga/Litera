#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose why hover glosses appear on chapter 1 only.

The hypothesis: VefxistyaosaniLine.strophe_id restarts at 1 in every chapter
(per-chapter numbering) while GlossOccurrence.strophe_global counts straight
through the whole poem (continuous numbering). In chapter 1 the two schemes
are identical, because 1..32 is both the first chapter's local range and the
poem's first global range. From chapter 2 onward they diverge, the join finds
nothing, and every tooltip silently disappears.

This script proves or disproves that without changing anything.

    python db_loaders/check_numbering.py
    python db_loaders/check_numbering.py --chapter 2 --verbose

Read the OFFSET column in the per-chapter table:

    offset 0            the two schemes agree, glosses will resolve
    offset == a jump    per-chapter vs continuous, glosses will NOT resolve
    offset varies       something is wrong beyond a simple scheme mismatch
"""

from __future__ import print_function

import argparse
import sys

from app import app
from models import GlossOccurrence, GlossTerm, VefxistyaosaniLine


def distinct_line_strophes(chapter_id):
    rows = (
        VefxistyaosaniLine.query.with_entities(VefxistyaosaniLine.strophe_id)
        .filter(VefxistyaosaniLine.chapter_id == chapter_id)
        .distinct()
        .all()
    )
    return sorted(r[0] for r in rows if r[0] is not None)


def distinct_gloss_strophes(chapter_id):
    rows = (
        GlossOccurrence.query.with_entities(GlossOccurrence.strophe_global)
        .filter(GlossOccurrence.chapter_id == chapter_id)
        .distinct()
        .all()
    )
    return sorted(r[0] for r in rows if r[0] is not None)


def all_chapters():
    a = {
        r[0]
        for r in VefxistyaosaniLine.query.with_entities(VefxistyaosaniLine.chapter_id)
        .distinct()
        .all()
        if r[0] is not None
    }
    b = {
        r[0]
        for r in GlossOccurrence.query.with_entities(GlossOccurrence.chapter_id)
        .distinct()
        .all()
        if r[0] is not None
    }
    return sorted(a | b), sorted(a), sorted(b)


def score_offset(lines, glosses, offset):
    gset = set(glosses)
    return sum(1 for s in lines if s + offset in gset)


def main():
    ap = argparse.ArgumentParser(description="Compare strophe numbering schemes.")
    ap.add_argument("--chapter", type=int, help="dump one chapter in detail")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    with app.app_context():
        chapters, line_chapters, gloss_chapters = all_chapters()

        print("chapters in vefxistyaosani_lines: %d" % len(line_chapters))
        print("chapters in gloss_occurrences:    %d" % len(gloss_chapters))

        only_lines = sorted(set(line_chapters) - set(gloss_chapters))
        only_gloss = sorted(set(gloss_chapters) - set(line_chapters))
        if only_lines:
            print("chapters with verse but no glosses: %s" % only_lines)
        if only_gloss:
            print("chapters with glosses but no verse: %s" % only_gloss)

        nulls = GlossOccurrence.query.filter(
            GlossOccurrence.strophe_local.is_(None)
        ).count()
        total = GlossOccurrence.query.count()
        print("strophe_local NULL: %d of %d occurrences" % (nulls, total))
        print("")

        if args.chapter is not None:
            chapters = [args.chapter]

        print("  ch   verse strophes      gloss strophes    direct  offset  fixed")
        print("  ---  ------------------  ------------------  ------  ------  -----")

        verdicts = []

        for ch in chapters:
            lines = distinct_line_strophes(ch)
            glosses = distinct_gloss_strophes(ch)

            if not lines or not glosses:
                print(
                    "  %3d  %-18s  %-18s  %6s  %6s  %5s"
                    % (
                        ch,
                        ("%d..%d (%d)" % (lines[0], lines[-1], len(lines))) if lines else "-",
                        ("%d..%d (%d)" % (glosses[0], glosses[-1], len(glosses)))
                        if glosses
                        else "-",
                        "-",
                        "-",
                        "-",
                    )
                )
                continue

            direct = score_offset(lines, glosses, 0)
            offset = glosses[0] - lines[0]
            fixed = score_offset(lines, glosses, offset)

            verdicts.append((ch, direct, offset, fixed, len(lines)))

            print(
                "  %3d  %-18s  %-18s  %6d  %+6d  %5d"
                % (
                    ch,
                    "%d..%d (%d)" % (lines[0], lines[-1], len(lines)),
                    "%d..%d (%d)" % (glosses[0], glosses[-1], len(glosses)),
                    direct,
                    offset,
                    fixed,
                )
            )

        print("")

        if verdicts:
            broken = [v for v in verdicts if v[1] == 0 and v[3] > 0]
            working = [v for v in verdicts if v[1] > 0]
            hopeless = [v for v in verdicts if v[1] == 0 and v[3] == 0]

            print("chapters where glosses resolve as-is:      %d" % len(working))
            print("chapters fixed by a constant offset:       %d" % len(broken))
            print("chapters that neither scheme explains:     %d" % len(hopeless))
            print("")

            if broken and len(working) <= 1:
                print("VERDICT: per-chapter vs continuous numbering, as suspected.")
                print("         vefxistyaosani_lines.strophe_id restarts each chapter;")
                print("         gloss_occurrences.strophe_global runs straight through.")
                print("         They coincide only in chapter 1, which is why hover")
                print("         works there and nowhere else.")
                print("")
                print("         Fix: run  load_glossary.py --backfill-local")
                print("         or use the offset-aware reader_routes.py, which needs")
                print("         no migration.")
            elif hopeless:
                print("VERDICT: the mismatch is not a clean offset. Inspect a chapter")
                print("         with --chapter N --verbose before changing anything.")
            else:
                print("VERDICT: numbering agrees. The blank tooltips have another")
                print("         cause -- check that gloss terms appear literally in the")
                print("         verse text, and re-run with --chapter N --verbose.")

        if args.chapter is not None and args.verbose:
            ch = args.chapter
            print("")
            print("--- chapter %d detail ---" % ch)

            lines = distinct_line_strophes(ch)
            glosses = distinct_gloss_strophes(ch)
            print("verse strophe ids: %s" % lines[:20])
            print("gloss strophe ids: %s" % glosses[:20])
            print("")

            offset = (glosses[0] - lines[0]) if (lines and glosses) else 0

            sample = (
                VefxistyaosaniLine.query.filter_by(chapter_id=ch)
                .order_by(VefxistyaosaniLine.strophe_id, VefxistyaosaniLine.line_id)
                .limit(4)
                .all()
            )
            if sample:
                target = sample[0].strophe_id + offset
                print("first verse strophe %d maps to gloss strophe %d" % (sample[0].strophe_id, target))
                for row in sample:
                    print("   %s" % row.line)
                print("")

                terms = (
                    GlossOccurrence.query.join(
                        GlossTerm, GlossOccurrence.term_id == GlossTerm.id
                    )
                    .filter(
                        GlossOccurrence.chapter_id == ch,
                        GlossOccurrence.strophe_global == target,
                    )
                    .with_entities(GlossTerm.term, GlossTerm.gloss)
                    .all()
                )
                print("glosses attached to strophe %d: %d" % (target, len(terms)))
                verse = " ".join(r.line or "" for r in sample)
                for term, gloss in terms:
                    hit = "OK " if term and term in verse else "MISS"
                    print("   %s %-22s %s" % (hit, term, (gloss or "")[:44]))
                print("")
                print("   MISS means the term does not appear literally in the verse,")
                print("   which points at a text-variant difference rather than numbering.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
