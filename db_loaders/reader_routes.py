# -*- coding: utf-8 -*-
"""
Chapter reader: original Vefxistyaosani on the left, modernised prose on the right.

Paste the two routes into app.py (or register the blueprint below), and drop
templates/vefxistyaosani_chapter.html next to your other templates.

The two columns are independent. The left is built from VefxistyaosaniLine
rows for one chapter, grouped into strophes of four lines, with archaic terms
wrapped in <span class="gloss"> carrying their modern meaning. The right is a
single ModernChapter row rendered as paragraphs.

Gloss resolution is per strophe, never per term. 182 terms are defensibly
polysemous (კვლა alone carries 7 distinct senses), so a global term->gloss
dictionary would show the wrong meaning often enough to matter.

NUMBERING
---------
vefxistyaosani_lines.strophe_id restarts at 1 in every chapter, while
gloss_occurrences.strophe_global counts straight through the poem. The two
schemes coincide only in chapter 1, so a naive join produces tooltips on the
first chapter and nowhere else.

_resolve_alignment() handles this without a migration: it tries the direct
join, then a constant offset derived from the chapter's own first strophe,
and keeps whichever explains more strophes. That works whether your rows are
locally numbered, globally numbered, or backfilled later.
"""

import re
from collections import OrderedDict, defaultdict

from flask import Blueprint, abort, render_template
from markupsafe import Markup, escape

from models import GlossOccurrence, GlossTerm, ModernChapter, VefxistyaosaniLine

reader = Blueprint("reader", __name__)


# Terms ending in a hyphen are preverbs (და-, მი-, წა-). They are legitimate
# glossary entries but never appear as literal substrings in the verse, so
# matching them wastes time and can produce nonsense partial hits.
PREVERB_RE = re.compile(r"[-\u2010\u2011\u2013\u2014]\s*$")

# Georgian is unicameral, so a boundary check against Georgian letters is
# enough to stop a short term matching inside a longer word.
GEORGIAN = r"\u10a0-\u10ff"


def _load_chapter_glosses(chapter_id):
    """Return (by_global, by_local), each {strophe_number: {term: gloss}}.

    Terms within a strophe are ordered longest first so a phrase wins over any
    single word it contains.
    """
    rows = (
        GlossOccurrence.query.join(GlossTerm, GlossOccurrence.term_id == GlossTerm.id)
        .filter(GlossOccurrence.chapter_id == chapter_id)
        .with_entities(
            GlossOccurrence.strophe_global,
            GlossOccurrence.strophe_local,
            GlossTerm.term,
            GlossTerm.gloss,
        )
        .all()
    )

    by_global = defaultdict(dict)
    by_local = defaultdict(dict)

    for strophe_global, strophe_local, term, gloss in rows:
        term = " ".join((term or "").split())
        gloss = " ".join((gloss or "").split())
        if not term or not gloss or PREVERB_RE.search(term):
            continue
        if strophe_global is not None:
            by_global[strophe_global].setdefault(term, gloss)
        if strophe_local is not None:
            by_local[strophe_local].setdefault(term, gloss)

    def _sorted(bucket):
        return {
            strophe: OrderedDict(
                sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True)
            )
            for strophe, mapping in bucket.items()
        }

    return _sorted(by_global), _sorted(by_local)


def _resolve_alignment(strophe_numbers, by_global, by_local):
    """Pick the mapping that explains the most strophes in this chapter.

    Returns (lookup_dict, offset, scheme_label). Applying the result means
    looking up ``lookup[strophe_id + offset]``.
    """
    if not strophe_numbers:
        return {}, 0, "none"

    lowest = min(strophe_numbers)
    candidates = []

    for label, bucket in (("local", by_local), ("global", by_global)):
        if not bucket:
            continue
        keys = set(bucket)

        # Direct join.
        candidates.append(
            (len(strophe_numbers & keys), 0, bucket, label)
        )

        # Constant offset: assume this chapter's first strophe corresponds to
        # the lowest glossed strophe recorded for the same chapter.
        offset = min(keys) - lowest
        if offset:
            hits = sum(1 for s in strophe_numbers if s + offset in keys)
            candidates.append((hits, offset, bucket, label + "+offset"))

    if not candidates:
        return {}, 0, "none"

    hits, offset, bucket, label = max(candidates, key=lambda c: c[0])
    if hits == 0:
        return {}, 0, "none"

    return bucket, offset, label


def _annotate(line, glosses):
    """Wrap every glossed term in one line of verse.

    Works on escaped text and inserts markup via sentinels, so a gloss can
    never be matched a second time inside markup already emitted.
    """
    if not line:
        return Markup("")

    text = str(escape(line))
    if not glosses:
        return Markup(text)

    slots = []

    for term, gloss in glosses.items():
        pattern = re.compile(
            r"(?<![%s])(%s)(?![%s])" % (GEORGIAN, re.escape(str(escape(term))), GEORGIAN)
        )

        def _swap(match, _gloss=gloss):
            index = len(slots)
            slots.append((match.group(1), _gloss))
            return "\x00%d\x00" % index

        text = pattern.sub(_swap, text)

    def _expand(match):
        surface, gloss = slots[int(match.group(1))]
        return (
            '<span class="gloss" data-gloss="%s" tabindex="0" '
            'role="button" aria-label="%s: %s">%s</span>'
            % (escape(gloss), surface, escape(gloss), surface)
        )

    text = re.sub(r"\x00(\d+)\x00", _expand, text)
    return Markup(text)


def _build_strophes(chapter_id):
    """Group a chapter's lines into strophes and annotate them."""
    lines = (
        VefxistyaosaniLine.query.filter_by(chapter_id=chapter_id)
        .order_by(VefxistyaosaniLine.strophe_id, VefxistyaosaniLine.line_id)
        .all()
    )
    if not lines:
        return [], "none", 0

    by_global, by_local = _load_chapter_glosses(chapter_id)
    strophe_numbers = {row.strophe_id for row in lines if row.strophe_id is not None}

    lookup, offset, scheme = _resolve_alignment(strophe_numbers, by_global, by_local)

    grouped = OrderedDict()
    for row in lines:
        grouped.setdefault(row.strophe_id, []).append(row)

    strophes = []
    for number, rows in grouped.items():
        glosses = lookup.get(number + offset, {})
        strophes.append(
            {
                "number": number,
                "lines": [_annotate(r.line, glosses) for r in rows],
                "gloss_count": len(glosses),
            }
        )

    return strophes, scheme, offset


def _chapter_index():
    """Every chapter present in the poem, with a flag for modern coverage."""
    numbers = [
        n
        for (n,) in VefxistyaosaniLine.query.with_entities(VefxistyaosaniLine.chapter_id)
        .distinct()
        .order_by(VefxistyaosaniLine.chapter_id)
        .all()
        if n is not None
    ]

    titles = {}
    modernised = set()
    for row in ModernChapter.query.all():
        modernised.add(row.chapter_id)
        if row.title:
            titles[row.chapter_id] = row.title

    return [
        {"number": n, "title": titles.get(n, ""), "modernised": n in modernised}
        for n in numbers
    ]


@reader.route("/vefxistyaosani/")
def vefxistyaosani_index():
    chapters = _chapter_index()
    if not chapters:
        abort(404)
    return vefxistyaosani_chapter(chapters[0]["number"])


@reader.route("/vefxistyaosani/<int:chapter>")
def vefxistyaosani_chapter(chapter):
    strophes, scheme, offset = _build_strophes(chapter)
    if not strophes:
        abort(404)

    modern = (
        ModernChapter.query.filter_by(chapter_id=chapter)
        .order_by(ModernChapter.source)
        .first()
    )

    chapters = _chapter_index()
    numbers = [c["number"] for c in chapters]
    position = numbers.index(chapter) if chapter in numbers else -1

    return render_template(
        "vefxistyaosani_chapter.html",
        chapter=chapter,
        title=(modern.title if modern else ""),
        strophes=strophes,
        modern_paragraphs=(modern.paragraphs if modern else []),
        modern_missing=(modern is None),
        gloss_scheme=scheme,
        gloss_offset=offset,
        gloss_total=sum(s["gloss_count"] for s in strophes),
        chapters=chapters,
        prev_chapter=(numbers[position - 1] if position > 0 else None),
        next_chapter=(
            numbers[position + 1] if 0 <= position < len(numbers) - 1 else None
        ),
    )


# In app.py:
#
#     from reader_routes import reader
#     app.register_blueprint(reader)
#
# Then visit /vefxistyaosani/1
