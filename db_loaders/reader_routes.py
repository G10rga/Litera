# -*- coding: utf-8 -*-
"""
Chapter reader: original Vefxistyaosani on the left, modernised prose on the right.

Paste the two routes into app.py (or register the blueprint below), and drop
templates/vefxistyaosani_chapter.html next to your other templates.

The two columns are independent. The left is built from VefxistyaosaniLine
rows for one chapter, grouped into strophes of four lines, with archaic terms
wrapped in <span class="gloss"> carrying their modern meaning. The right is a
single ModernChapter row rendered as paragraphs. Nothing has to line up
horizontally, which is what makes this tractable.

Gloss resolution is per strophe, never per term. 182 terms are defensibly
polysemous (კვლა alone carries 7 distinct senses), so a global term->gloss
dictionary would show the wrong meaning often enough to matter.
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

# Georgian has no case distinction, so a plain boundary check on non-Georgian
# characters is enough to avoid matching inside a longer word.
GEORGIAN = r"\u10a0-\u10ff"


def _load_chapter_glosses(chapter_id):
    """Return {strophe_number: OrderedDict(term -> gloss)} for one chapter.

    Terms are ordered longest first so that a phrase wins over any single word
    it contains.
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
        out = {}
        for strophe, mapping in bucket.items():
            out[strophe] = OrderedDict(
                sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True)
            )
        return out

    return _sorted(by_global), _sorted(by_local)


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

        def _swap(match):
            index = len(slots)
            slots.append((match.group(1), gloss))
            return "\x00%d\x00" % index

        text = pattern.sub(_swap, text)

    def _expand(match):
        surface, gloss = slots[int(match.group(1))]
        return '<span class="gloss" data-gloss="%s" tabindex="0">%s</span>' % (
            escape(gloss),
            surface,
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
        return [], "none"

    by_global, by_local = _load_chapter_glosses(chapter_id)

    strophe_numbers = {row.strophe_id for row in lines}

    # strophe_local is NULL until load_glossary.py --backfill-local has run, so
    # prefer whichever numbering actually overlaps this chapter's strophes.
    overlap_global = len(strophe_numbers & set(by_global))
    overlap_local = len(strophe_numbers & set(by_local))

    if overlap_local > overlap_global:
        lookup, scheme = by_local, "local"
    elif overlap_global:
        lookup, scheme = by_global, "global"
    else:
        lookup, scheme = {}, "none"

    grouped = OrderedDict()
    for row in lines:
        grouped.setdefault(row.strophe_id, []).append(row)

    strophes = []
    for number, rows in grouped.items():
        glosses = lookup.get(number, {})
        strophes.append(
            {
                "number": number,
                "lines": [_annotate(r.line, glosses) for r in rows],
                "gloss_count": len(glosses),
            }
        )

    return strophes, scheme


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
    strophes, scheme = _build_strophes(chapter)
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
