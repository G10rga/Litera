#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reader route for შუშანიკის წამება.

Left column:  the original text from shushaniki_main, with archaic words
              wrapped so they show their gloss on hover.
Right column: the modernised text, read from shushaniki_modern.
              the column renders a placeholder until the rows exist.

How this differs from the Vefkhistkaosani reader
-----------------------------------------------
There is no alignment problem here. utvalavi anchored each gloss to a strophe
number, so a mismatch between editions could shift every gloss and silently
kill the tooltips. NPLG ships one global word list applied by string match, so
glosses are located by matching the text itself. There is no offset to resolve
and nothing that can drift out of register.

The cost is that matching has to be done properly: 300 of the 597 entries are
multi-word phrases, some up to twelve words long, so they must be matched
before single words and longest-first. Otherwise a short word inside a phrase
would claim the match and the phrase gloss would never appear.

Drop this file in the project root and register it in app.py:

    from shushaniki_routes import shushaniki
    app.register_blueprint(shushaniki)
"""

import html
import re
from collections import OrderedDict

from flask import Blueprint, abort, render_template

from models import ShushanikiGloss, ShushanikiText, db

try:
    from models import ShushanikiModern
except ImportError:  # modern text not modelled yet
    ShushanikiModern = None

shushaniki = Blueprint("shushaniki", __name__)

# No source filter is needed any more. shushaniki_glosses contains this work
# and nothing else, which is the whole point of the separate table: a shared
# table meant a common word such as პირველ or ჯერ pulled in every unrelated
# Vefkhistkaosani reading and buried the real gloss.

# The modernised text lives in its own table, shushaniki_modern, keyed by
# chapter_id alone. There is no source column to filter on and therefore no
# filter that can be forgotten.

GEORGIAN = u"\u10a0-\u10ff"

# Punctuation that may sit flush against a word. Used to build match
# boundaries, since Georgian script does not play well with \b.
BOUNDARY = u"(?<![%s])" % GEORGIAN
BOUNDARY_END = u"(?![%s])" % GEORGIAN


# ---------------------------------------------------------------- glosses

def _load_glosses():
    """Return [(term, gloss)] sorted longest-first.

    Longest-first is what makes phrase matching work. If 'ვითარ' were tried
    before 'ვითარცა-ესე', the compound would never match.
    """
    rows = db.session.query(
        ShushanikiGloss.term, ShushanikiGloss.gloss
    ).all()

    best = OrderedDict()
    for term, gloss in rows:
        term = " ".join((term or "").split())
        gloss = " ".join((gloss or "").split())
        if not term or not gloss:
            continue
        # If a term carries several glosses, keep the first and append the
        # others so the tooltip shows every reading rather than picking one.
        if term in best:
            if gloss not in best[term]:
                best[term].append(gloss)
        else:
            best[term] = [gloss]

    pairs = []
    for term, glosses in best.items():
        # The Shushaniki glossary has exactly one gloss per term, so this
        # normally yields a single string. The cap stops a future data problem
        # from rendering an unreadable tooltip.
        if len(glosses) > 3:
            glosses = glosses[:3] + ["\u2026"]
        pairs.append((term, " | ".join(glosses)))
    pairs.sort(key=lambda item: len(item[0]), reverse=True)
    return pairs


def _annotate(text, glosses):
    """Wrap every glossed term in `text` with a hover span.

    Matches are replaced by a NUL-delimited sentinel first so that an already
    matched region cannot be matched again by a shorter term, then the
    sentinels are expanded to markup. This is the same technique the
    Vefkhistkaosani reader uses.
    """
    escaped = html.escape(text)
    found = []

    for term, gloss in glosses:
        if not term:
            continue
        needle = html.escape(term)
        pattern = BOUNDARY + re.escape(needle) + BOUNDARY_END

        def substitute(match, _gloss=gloss):
            found.append((match.group(0), _gloss))
            return u"\x00%d\x00" % (len(found) - 1)

        escaped = re.sub(pattern, substitute, escaped)

    if not found:
        return escaped, 0

    def expand(match):
        surface, gloss = found[int(match.group(1))]
        return (
            u'<span class="gloss" data-gloss="%s" tabindex="0">%s</span>'
            % (html.escape(gloss, quote=True), surface)
        )

    return re.sub(u"\x00(\\d+)\x00", expand, escaped), len(found)


# ------------------------------------------------------------------ text

def _chapter_index():
    """Distinct chapter numbers present in shushaniki_main, in order."""
    rows = (
        db.session.query(ShushanikiText.chapter)
        .filter(ShushanikiText.chapter.isnot(None))
        .distinct()
        .order_by(ShushanikiText.chapter)
        .all()
    )
    numbers = [row[0] for row in rows]

    modernised = set()
    if ShushanikiModern is not None:
        modernised = set(
            row[0]
            for row in db.session.query(ShushanikiModern.chapter_id).all()
        )

    return [{"number": n, "modernised": n in modernised} for n in numbers]


def _paragraphs(chapter):
    rows = (
        ShushanikiText.query
        .filter(ShushanikiText.chapter == chapter)
        .order_by(ShushanikiText.id)
        .all()
    )
    return rows


def _modern(chapter):
    if ShushanikiModern is None:
        return None
    return ShushanikiModern.query.filter_by(chapter_id=chapter).first()


# ---------------------------------------------------------------- routes

@shushaniki.route("/shushaniki/")
@shushaniki.route("/shushaniki/<int:chapter>")
def reader(chapter=None):
    chapters = _chapter_index()
    if not chapters:
        return render_template(
            "shushaniki.html",
            chapter=None,
            chapters=[],
            paragraphs=[],
            modern_paragraphs=[],
            modern_missing=True,
            gloss_total=0,
            gloss_hits=0,
            prev_chapter=None,
            next_chapter=None,
            empty=True,
        )

    numbers = [c["number"] for c in chapters]
    if chapter is None:
        chapter = numbers[0]
    if chapter not in numbers:
        abort(404)

    rows = _paragraphs(chapter)
    glosses = _load_glosses()

    paragraphs = []
    hits = 0
    for row in rows:
        marked, count = _annotate(row.text or "", glosses)
        hits += count
        paragraphs.append({"id": row.id, "html": marked, "gloss_count": count})

    modern_row = _modern(chapter)
    if modern_row is not None and (modern_row.text or "").strip():
        modern_paragraphs = [
            p.strip() for p in re.split(r"\n\s*\n", modern_row.text) if p.strip()
        ]
        modern_missing = False
    else:
        modern_paragraphs = []
        modern_missing = True

    position = numbers.index(chapter)
    prev_chapter = numbers[position - 1] if position > 0 else None
    next_chapter = numbers[position + 1] if position + 1 < len(numbers) else None

    return render_template(
        "shushaniki.html",
        chapter=chapter,
        chapters=chapters,
        paragraphs=paragraphs,
        modern_paragraphs=modern_paragraphs,
        modern_missing=modern_missing,
        gloss_total=len(glosses),
        gloss_hits=hits,
        prev_chapter=prev_chapter,
        next_chapter=next_chapter,
        empty=False,
    )
