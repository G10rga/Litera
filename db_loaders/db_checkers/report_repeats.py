"""Full repetition report over every term in the glossary.

Nothing is hardcoded. Every term is examined.

Three distinct senses of "repeated" are reported separately:

  1. term-level     one term carrying several different glosses
  2. occurrence     one term+gloss pair attached to several strophes
  3. near-duplicate glosses that differ only by punctuation, dash style,
                    trailing period, or synonym ordering

The third is the interesting one. utvalavi's editors typed glosses by hand,
so the same reading appears as "\u10e1\u10d0\u10ed\u10d8\u10e0\u10dd\u10d0, \u10ef\u10d4\u10e0-\u10d0\u10e0\u10e1." and "\u10e1\u10d0\u10ed\u10d8\u10e0\u10dd\u10d0, \u10ef\u10d4\u10e0 \u10d0\u10e0\u10e1" and
"\u10e1\u10d0\u10ed\u10d8\u10e0\u10dd\u10d0, \u10ef\u10d4\u10e0\u2013\u10d0\u10e0\u10e1." -- three rows, one meaning.

Usage:
    python db_loaders/report_repeats.py
    python db_loaders/report_repeats.py --csv
    python db_loaders/report_repeats.py --term \u10ee\u10d0\u10db\u10e1
    python db_loaders/report_repeats.py --min 5
"""

import argparse
import csv
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402
from models import GlossOccurrence, GlossTerm, db  # noqa: E402

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Every dash-like character utvalavi's editors might have typed.
DASHES = '\u002d\u2010\u2011\u2012\u2013\u2014\u2015\u2212'
DASH_RE = re.compile('[' + DASHES + ']')
TRAILING_PUNCT_RE = re.compile(r'[.;:,\s]+$')


def canon_gloss(gloss):
    """Reduce a gloss to a comparable core.

    Unifies dash styles, drops spaces around dashes, strips trailing
    punctuation, collapses whitespace, and sorts comma-separated synonyms
    so that ordering differences do not count as distinct readings.
    """
    if not gloss:
        return ''
    text = DASH_RE.sub('-', gloss)
    text = re.sub(r'\s*-\s*', '-', text)
    text = ' '.join(text.split())
    text = TRAILING_PUNCT_RE.sub('', text)
    parts = [p.strip() for p in text.split(',')]
    parts = [p for p in parts if p]
    return ', '.join(sorted(parts)).lower()


def gather():
    """Return term -> list of (GlossTerm, occurrence_count)."""
    counts = Counter()
    for term_id, in db.session.query(GlossOccurrence.term_id).all():
        counts[term_id] += 1

    by_term = defaultdict(list)
    for entry in GlossTerm.query.order_by(GlossTerm.id).all():
        by_term[entry.term].append((entry, counts.get(entry.id, 0)))
    return by_term


def report(min_count, term_filter=None):
    with app.app_context():
        by_term = gather()

        if term_filter:
            entries = by_term.get(term_filter)
            if not entries:
                print(f'term not found: {term_filter!r}')
                return
            print(f'--- {term_filter!r}: {len(entries)} gloss row(s) ---')
            groups = defaultdict(list)
            for entry, occ in entries:
                groups[canon_gloss(entry.gloss)].append((entry, occ))
            print(f'  collapses to {len(groups)} distinct reading(s)')
            print('')
            for canon, members in sorted(
                groups.items(), key=lambda kv: -sum(m[1] for m in kv[1])
            ):
                total = sum(m[1] for m in members)
                print(f'  reading ({total} occurrences, {len(members)} row(s)):')
                for entry, occ in members:
                    print(f'    id={entry.id} [{occ} occ] {entry.gloss}')
            return

        repeated = {t: e for t, e in by_term.items() if len(e) > 1}

        total_pairs = sum(len(e) for e in by_term.values())
        print('--- 1. term-level repetition ---')
        print(f'  distinct terms:            {len(by_term)}')
        print(f'  terms with one gloss:      {len(by_term) - len(repeated)}')
        print(f'  terms with several:        {len(repeated)}')
        print(f'  pairs held by those:       '
              f'{sum(len(e) for e in repeated.values())}')
        print(f'  total pairs:               {total_pairs}')

        # --- near-duplicate collapse -----------------------------------
        collapsible = {}
        saved = 0
        for term, entries in repeated.items():
            groups = defaultdict(list)
            for entry, occ in entries:
                groups[canon_gloss(entry.gloss)].append((entry, occ))
            if len(groups) < len(entries):
                collapsible[term] = (len(entries), len(groups))
                saved += len(entries) - len(groups)

        print('')
        print('--- 3. near-duplicate glosses ---')
        print(f'  terms with collapsible glosses: {len(collapsible)}')
        print(f'  rows that are punctuation-only variants: {saved}')
        print(f'  pairs after collapsing: {total_pairs - saved}')
        if total_pairs:
            print(f'  share of glossary that is noise: '
                  f'{100.0 * saved / total_pairs:.1f}%')

        # --- the actual list -------------------------------------------
        print('')
        print(f'--- every term with {min_count}+ glosses ---')
        ranked = sorted(
            repeated.items(), key=lambda kv: (-len(kv[1]), kv[0])
        )
        shown = 0
        for term, entries in ranked:
            if len(entries) < min_count:
                continue
            shown += 1
            groups = defaultdict(list)
            for entry, occ in entries:
                groups[canon_gloss(entry.gloss)].append((entry, occ))
            occ_total = sum(o for _, o in entries)
            flag = '' if len(groups) == len(entries) else \
                f'  -> collapses to {len(groups)}'
            is_phrase = entries[0][0].is_phrase
            kind = 'phrase' if is_phrase else 'word'
            print(f'  {term!r}  {len(entries)} glosses, '
                  f'{occ_total} occurrences  [{kind}]{flag}')
        print('')
        print(f'  {shown} term(s) listed')

        # --- occurrence-level ------------------------------------------
        print('')
        print('--- 2. one pair spanning several strophes ---')
        multi = 0
        multi_phrase = 0
        for entries in by_term.values():
            for entry, _ in entries:
                n = (
                    db.session.query(GlossOccurrence.strophe_global)
                    .filter_by(term_id=entry.id)
                    .distinct()
                    .count()
                )
                if n > 1:
                    multi += 1
                    if entry.is_phrase:
                        multi_phrase += 1
        print(f'  pairs on >1 strophe:  {multi}')
        print(f'    of which phrases:   {multi_phrase}')
        print('  (normal for words; a phrase paraphrases one specific line,')
        print('   so phrases here are worth a look)')


def export_csv():
    with app.app_context():
        by_term = gather()

        path = os.path.join(PROJECT_ROOT, 'gloss_repeats.csv')
        with open(path, 'w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow([
                'term', 'is_phrase', 'n_glosses', 'n_distinct_readings',
                'n_occurrences', 'glosses',
            ])
            for term, entries in sorted(
                by_term.items(), key=lambda kv: (-len(kv[1]), kv[0])
            ):
                if len(entries) < 2:
                    continue
                readings = {canon_gloss(e.gloss) for e, _ in entries}
                writer.writerow([
                    term,
                    'phrase' if entries[0][0].is_phrase else 'word',
                    len(entries),
                    len(readings),
                    sum(o for _, o in entries),
                    ' | '.join(e.gloss for e, _ in entries),
                ])
        print(f'wrote {path}')

        path2 = os.path.join(PROJECT_ROOT, 'gloss_near_duplicates.csv')
        with open(path2, 'w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow([
                'term', 'canonical_reading', 'variant_ids', 'variants',
            ])
            rows = 0
            for term, entries in by_term.items():
                groups = defaultdict(list)
                for entry, occ in entries:
                    groups[canon_gloss(entry.gloss)].append(entry)
                for canon, members in groups.items():
                    if len(members) < 2:
                        continue
                    writer.writerow([
                        term,
                        canon,
                        ';'.join(str(m.id) for m in members),
                        ' | '.join(m.gloss for m in members),
                    ])
                    rows += 1
        print(f'wrote {path2} ({rows} collapsible group(s))')
        print('')
        print('Open both in Excel. They are UTF-8 with BOM so Georgian')
        print('renders correctly without an import step.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', action='store_true',
                        help='export full lists to CSV')
    parser.add_argument('--term', help='drill into one specific term')
    parser.add_argument('--min', type=int, default=2,
                        help='minimum gloss count to list (default 2)')
    args = parser.parse_args()

    if args.csv:
        export_csv()
    else:
        report(args.min, args.term)


if __name__ == '__main__':
    main()
