# -*- coding: utf-8 -*-
"""
Reader for every work in the works table.

One blueprint and one template serve all of them, at a distinct URL per work:

    /literature/                      index of works
    /literature/<slug>/               first section
    /literature/<slug>/<section>      one section, original beside modern

Eleven separate template files would mean fixing every layout change eleven
times. The pages are still separate; only the source is shared.

The left column comes from text_units, the right from modern_sections. Both are
scoped by work_id, which is a NOT NULL foreign key -- unlike the optional source
string that let the Vefkhistkaosani glossary leak into the Shushaniki reader.
"""

from flask import Blueprint, abort, redirect, render_template, url_for

from models import TextUnit, Work, db

# Optional so the app still boots before the migration is applied.
try:
    from models import ModernSection
except ImportError:  # pragma: no cover
    ModernSection = None

literature = Blueprint("literature", __name__, url_prefix="/literature")

# Sentinel section number for works that have no divisions at all.
WHOLE_WORK = 0


def _section_numbers(work):
    """Ordered section numbers that actually contain body text."""
    rows = (db.session.query(TextUnit.section)
            .filter(TextUnit.work_id == work.id,
                    TextUnit.section.isnot(None),
                    TextUnit.kind != "note")
            .distinct()
            .order_by(TextUnit.section)
            .all())
    return [row[0] for row in rows]


def _section_labels(work):
    """Map section number -> marker as printed in the source ('II', 'I თავი').

    The source files disagree about marker style, so the reader shows whatever
    the edition showed rather than inventing a uniform one.
    """
    rows = (db.session.query(TextUnit.section, TextUnit.section_label)
            .filter(TextUnit.work_id == work.id,
                    TextUnit.section.isnot(None),
                    TextUnit.section_label.isnot(None))
            .all())
    labels = {}
    for number, label in rows:
        labels.setdefault(number, label)
    return labels


def _modern_sections(work):
    """Set of section numbers that have modernised text."""
    if ModernSection is None:
        return set()
    rows = (db.session.query(ModernSection.section)
            .filter(ModernSection.work_id == work.id)
            .all())
    return set(row[0] for row in rows)


def _modern(work, section):
    if ModernSection is None:
        return None
    return (ModernSection.query
            .filter_by(work_id=work.id, section=section)
            .first())


def _units(work, section):
    """Body units for one section, in reading order."""
    query = TextUnit.query.filter(TextUnit.work_id == work.id,
                                  TextUnit.kind != "note")
    if section == WHOLE_WORK:
        query = query.filter(TextUnit.section.is_(None))
    else:
        query = query.filter(TextUnit.section == section)
    return query.order_by(TextUnit.unit_global).all()


def _notes(work):
    """Footnotes, shown at the foot of the final section."""
    return (TextUnit.query
            .filter_by(work_id=work.id, kind="note")
            .order_by(TextUnit.unit_global)
            .all())


@literature.route("/")
def index():
    """List every loaded work with its modernisation progress."""
    works = Work.query.order_by(Work.author, Work.title).all()

    rows = []
    for work in works:
        numbers = _section_numbers(work)
        done = _modern_sections(work)
        total = len(numbers) or 1
        covered = len([n for n in numbers if n in done]) or (
            1 if (not numbers and WHOLE_WORK in done) else 0)
        rows.append({
            "work": work,
            "sections": len(numbers),
            "covered": covered,
            "total": total,
            "percent": int(round(100.0 * covered / total)),
        })

    return render_template("literature_index.html", rows=rows)


@literature.route("/<slug>/")
def start(slug):
    work = Work.query.filter_by(slug=slug).first()
    if work is None:
        abort(404)
    numbers = _section_numbers(work)
    first = numbers[0] if numbers else WHOLE_WORK
    return redirect(url_for("literature.reader", slug=slug, section=first))


@literature.route("/<slug>/<int:section>")
def reader(slug, section):
    work = Work.query.filter_by(slug=slug).first()
    if work is None:
        abort(404)

    numbers = _section_numbers(work)

    # A work with no divisions is served only at section 0.
    if not numbers and section != WHOLE_WORK:
        abort(404)
    if numbers and section not in numbers:
        abort(404)

    labels = _section_labels(work)
    covered = _modern_sections(work)

    chapters = [{
        "number": number,
        "label": labels.get(number) or str(number),
        "has_modern": number in covered,
    } for number in numbers]

    position = numbers.index(section) if numbers else 0
    previous = numbers[position - 1] if numbers and position > 0 else None
    following = (numbers[position + 1]
                 if numbers and position + 1 < len(numbers) else None)

    modern = _modern(work, section)
    units = _units(work, section)

    return render_template(
        "literature_reader.html",
        work=work,
        units=units,
        chapters=chapters,
        section=section,
        section_label=labels.get(section),
        modern=modern,
        modern_paragraphs=(modern.paragraphs if modern else []),
        modern_missing=(modern is None),
        prev_section=previous,
        next_section=following,
        notes=(_notes(work) if following is None else []),
        is_verse=(work.kind == "verse"),
    )
