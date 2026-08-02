"""Diagnose and repair whitespace damage in the loaded glossary.

utvalavi's markup uses &nbsp; heavily, so scraped terms can contain U+00A0
and other exotic whitespace. That makes `' ' in term` disagree with
`term.split()`, which is how is_phrase ended up misclassified for a large
number of rows.

This script normalises whitespace in gloss_terms, recomputes is_phrase from
the normalised text, and merges any rows that become duplicates as a result.

Usage:
    python db_loaders/fix_glossary.py --check        # report only, no writes
    python db_loaders/fix_glossary.py --audit-csv    # explain dropped CSV rows
    python db_loaders/fix_glossary.py --fix          # normalise and repair
"""

import argparse
import csv
import os
import sys
import unicodedata
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402
from models import GlossOccurrence, GlossTerm, db  # noqa: E402

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CSV = os.path.join(PROJECT_ROOT, 'gloss_occurrences.csv')

# Whitespace characters that survive HTML scraping and break naive splitting.
EXOTIC_WS = {
    '\u00a0': 'NO-BREAK SPACE',
    '\u2000': 'EN QUAD',
    '\u2001': 'EM QUAD',
    '\u2002': 'EN SPACE',
    '\u2003': 'EM SPACE',
    '\u2004': 'THREE-PER-EM SPACE',
    '\u2005': 'FOUR-PER-EM SPACE',
    '\u2006': 'SIX-PER-EM SPACE',
    '\u2007': 'FIGURE SPACE',
    '\u2008': 'PUNCTUATION SPACE',
    '\u2009': 'THIN SPACE',
    '\u200a': 'HAIR SPACE',
    '\u200b': 'ZERO WIDTH SPACE',
    '\u202f': 'NARROW NO-BREAK SPACE',
    '\u205f': 'MEDIUM MATHEMATICAL SPACE',
    '\u3000': 'IDEOGRAPHIC SPACE',
    '\ufeff': 'ZERO WIDTH NO-BREAK SPACE',
    '\t': 'TAB',
    '\n': 'NEWLINE',
    '\r': 'CARRIAGE RETURN',
}


def norm_ws(text):
    """Collapse every flavour of whitespace to single ASCII spaces."""
    if text is None:
        return ''
    # Zero-width characters are deletions, not separators.
    for zero_width in ('\u200b', '\ufeff'):
        text = text.replace(zero_width, '')
    return ' '.join(text.split())


def is_phrase_of(term):
    return len(norm_ws(term).split()) > 1


def describe(text):
    """Human-readable dump of the exotic characters in a string."""
    found = Counter()
    for char in text:
        if char in EXOTIC_WS:
            found[EXOTIC_WS[char]] += 1
    return ', '.join(f'{name} x{n}' for name, n in found.items())


def check():
    with app.app_context():
        terms = GlossTerm.query.all()
        print(f'gloss_terms: {len(terms)}')

        if not terms:
            sys.exit('ERROR: gloss_terms is empty. Run load_glossary.py first.')

        char_counts = Counter()
        dirty_terms = []
        would_reclassify = []
        norm_groups = defaultdict(list)

        for term in terms:
            raw = term.term or ''
            for char in raw:
                if char in EXOTIC_WS:
                    char_counts[EXOTIC_WS[char]] += 1

            normalised = norm_ws(raw)
            norm_groups[(normalised, norm_ws(term.gloss))].append(term.id)

            if normalised != raw:
                dirty_terms.append(term)

            correct = is_phrase_of(raw)
            if bool(term.is_phrase) != correct:
                would_reclassify.append((term, correct))

        print('')
        print('--- exotic whitespace in term text ---')
        if char_counts:
            for name, count in char_counts.most_common():
                print(f'  {name}: {count}')
        else:
            print('  none found')

        print('')
        print(f'terms whose text changes under normalisation: {len(dirty_terms)}')
        for term in dirty_terms[:10]:
            print(f'  id={term.id} is_phrase={term.is_phrase} '
                  f'[{describe(term.term)}]')
            print(f'     raw:  {term.term!r}')
            print(f'     norm: {norm_ws(term.term)!r}')
        if len(dirty_terms) > 10:
            print(f'  ... and {len(dirty_terms) - 10} more')

        to_phrase = sum(1 for _, correct in would_reclassify if correct)
        to_word = len(would_reclassify) - to_phrase

        print('')
        print('--- is_phrase correctness ---')
        print(f'  misclassified: {len(would_reclassify)}')
        print(f'    word -> phrase: {to_phrase}')
        print(f'    phrase -> word: {to_word}')

        current_phrases = sum(1 for t in terms if t.is_phrase)
        after_phrases = sum(1 for t in terms if is_phrase_of(t.term))
        print('')
        print(f'  phrases now:   {current_phrases}')
        print(f'  phrases after: {after_phrases}')
        print(f'  words now:     {len(terms) - current_phrases}')
        print(f'  words after:   {len(terms) - after_phrases}')

        collisions = {k: v for k, v in norm_groups.items() if len(v) > 1}
        print('')
        print(f'--- merge impact ---')
        print(f'  distinct pairs after normalisation: {len(norm_groups)}')
        print(f'  groups that would merge: {len(collisions)}')
        extra = sum(len(v) - 1 for v in collisions.values())
        print(f'  rows removed by merging: {extra}')

        if not dirty_terms and not would_reclassify:
            print('')
            print('nothing to fix.')


def audit_csv(csv_path):
    """Explain which CSV rows the loader dropped and why."""
    if not os.path.exists(csv_path):
        sys.exit(f'ERROR: CSV not found at {csv_path}')

    total = 0
    unusable = []
    keys = Counter()

    with open(csv_path, encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        for line_no, row in enumerate(reader, start=2):
            total += 1
            term = (row.get('term') or '').strip()
            gloss = (row.get('gloss') or '').strip()
            chapter = (row.get('chapter_id') or '').strip()
            strophe = (row.get('strophe_id') or '').strip()

            if not term or not gloss or not chapter.isdigit() or not strophe.isdigit():
                unusable.append((line_no, row))
                continue

            keys[(row.get('ganm_id'), strophe, term, gloss)] += 1

    duplicates = {k: v for k, v in keys.items() if v > 1}
    collapsed = sum(v - 1 for v in duplicates.values())

    print(f'csv rows: {total}')
    print('')
    print(f'--- unusable rows: {len(unusable)} ---')
    for line_no, row in unusable:
        print(f'  line {line_no}: {dict(row)}')

    print('')
    print(f'--- duplicate (ganm_id, strophe, term, gloss) keys ---')
    print(f'  distinct keys duplicated: {len(duplicates)}')
    print(f'  rows collapsed on insert: {collapsed}')
    for key, count in list(sorted(duplicates.items(), key=lambda kv: -kv[1]))[:10]:
        ganm, strophe, term, _ = key
        print(f'  {ganm} strophe={strophe} term={term!r} x{count}')
    if len(duplicates) > 10:
        print(f'  ... and {len(duplicates) - 10} more')

    print('')
    print(f'expected rows in gloss_occurrences: {total - len(unusable) - collapsed}')


def fix():
    with app.app_context():
        terms = GlossTerm.query.order_by(GlossTerm.id).all()
        print(f'gloss_terms before: {len(terms)}')

        if not terms:
            sys.exit('ERROR: gloss_terms is empty. Run load_glossary.py first.')

        # Group by normalised identity; lowest id wins.
        groups = defaultdict(list)
        for term in terms:
            key = (norm_ws(term.term), norm_ws(term.gloss))
            groups[key].append(term)

        merged_terms = 0
        moved_occurrences = 0
        dropped_occurrences = 0
        renormalised = 0
        reclassified = 0

        for (norm_term, norm_gloss), members in groups.items():
            if not norm_term or not norm_gloss:
                continue

            canonical = members[0]
            correct_phrase = len(norm_term.split()) > 1

            if canonical.term != norm_term or canonical.gloss != norm_gloss:
                canonical.term = norm_term
                canonical.gloss = norm_gloss
                renormalised += 1

            if bool(canonical.is_phrase) != correct_phrase:
                canonical.is_phrase = correct_phrase
                reclassified += 1

            for duplicate in members[1:]:
                # Repoint occurrences, respecting the unique constraint.
                existing = {
                    (o.ganm_id, o.strophe_global)
                    for o in GlossOccurrence.query.filter_by(
                        term_id=canonical.id
                    ).with_entities(
                        GlossOccurrence.ganm_id,
                        GlossOccurrence.strophe_global,
                    ).all()
                }

                for occurrence in GlossOccurrence.query.filter_by(
                    term_id=duplicate.id
                ).all():
                    key = (occurrence.ganm_id, occurrence.strophe_global)
                    if key in existing:
                        db.session.delete(occurrence)
                        dropped_occurrences += 1
                    else:
                        occurrence.term_id = canonical.id
                        existing.add(key)
                        moved_occurrences += 1

                db.session.delete(duplicate)
                merged_terms += 1

            db.session.flush()

        db.session.commit()

        print(f'  renormalised text on:  {renormalised} term(s)')
        print(f'  is_phrase corrected on: {reclassified} term(s)')
        print(f'  merged duplicate terms: {merged_terms}')
        print(f'  occurrences repointed:  {moved_occurrences}')
        print(f'  occurrences dropped as exact dupes: {dropped_occurrences}')

        total = GlossTerm.query.count()
        phrases = GlossTerm.query.filter_by(is_phrase=True).count()
        occurrences = GlossOccurrence.query.count()

        print('')
        print(f'gloss_terms:       {total}')
        print(f'  single words:    {total - phrases}')
        print(f'  phrases:         {phrases}')
        print(f'gloss_occurrences: {occurrences}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='report problems, write nothing')
    parser.add_argument('--audit-csv', action='store_true', help='explain dropped CSV rows')
    parser.add_argument('--fix', action='store_true', help='normalise, reclassify, merge')
    parser.add_argument('--csv', default=DEFAULT_CSV, help='path to gloss_occurrences.csv')
    args = parser.parse_args()

    if args.audit_csv:
        audit_csv(args.csv)
    elif args.fix:
        fix()
    else:
        check()


if __name__ == '__main__':
    main()
