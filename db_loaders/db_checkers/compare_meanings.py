"""Do the repeated terms actually mean different things?

A term with several glosses might be:

  (a) one meaning written several ways    -- rewording, no real polysemy
  (b) several genuinely different senses  -- real polysemy

This script separates the two. Glosses for a term are tokenised into
Georgian content words, then linked into clusters: two glosses join the
same cluster if they share at least one content word. One cluster means
one sense written variously. Several disjoint clusters means the term
carries genuinely unrelated meanings in different places.

Usage:
    python db_loaders/compare_meanings.py
    python db_loaders/compare_meanings.py --term KVLA
    python db_loaders/compare_meanings.py --min 5
    python db_loaders/compare_meanings.py --csv
"""

import argparse
import csv
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402
from models import GlossOccurrence, GlossTerm, db  # noqa: E402

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Keep Georgian letters only; everything else becomes a separator.
NON_GEORGIAN = re.compile('[^\u10a0-\u10ff]+')

# Function words that appear in many unrelated glosses. Linking on these
# would fuse senses that have nothing to do with each other.
STOPWORDS = {
    '\u10d3\u10d0',                              # and
    '\u10d0\u10dc',                              # or
    '\u10d0\u10e0\u10d8\u10e1',                  # is
    '\u10d0\u10e5',                              # here
    '\u10d8\u10e1',                              # that
    '\u10e0\u10dd\u10db',                        # that (conj)
    '\u10d7\u10e3',                              # if
    '\u10d0\u10e0',                              # not
    '\u10d4\u10e1',                              # this
    '\u10d8\u10e1\u10d8\u10dc\u10d8',            # they
    '\u10d5\u10d8\u10e0\u10d4',                  # until
    '\u10ec\u10d8\u10dc',                        # before
}

MIN_TOKEN_LEN = 2


def tokens(gloss):
    """Georgian content words in a gloss, as a set."""
    if not gloss:
        return set()
    parts = NON_GEORGIAN.sub(' ', gloss).split()
    return {
        p for p in parts
        if len(p) >= MIN_TOKEN_LEN and p not in STOPWORDS
    }


def cluster(entries):
    """Group gloss entries into sense clusters by shared content words.

    Union-find over entries; two entries are joined when their token sets
    intersect. Returns a list of lists.
    """
    parent = list(range(len(entries)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)

    token_sets = [tokens(e.gloss) for e in entries]
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            if token_sets[i] & token_sets[j]:
                union(i, j)

    groups = defaultdict(list)
    for i, entry in enumerate(entries):
        groups[find(i)].append(entry)
    return list(groups.values())


def occ_map(term_ids):
    """term_id -> sorted list of strophe numbers."""
    result = defaultdict(list)
    rows = (
        db.session.query(
            GlossOccurrence.term_id,
            GlossOccurrence.chapter_id,
            GlossOccurrence.strophe_global,
        )
        .filter(GlossOccurrence.term_id.in_(list(term_ids)))
        .all()
    )
    for term_id, chapter_id, strophe in rows:
        result[term_id].append((chapter_id, strophe))
    for key in result:
        result[key].sort()
    return result


def gather():
    by_term = defaultdict(list)
    for entry in GlossTerm.query.order_by(GlossTerm.id).all():
        by_term[entry.term].append(entry)
    return {t: e for t, e in by_term.items() if len(e) > 1}


def drill(term):
    with app.app_context():
        entries = GlossTerm.query.filter_by(term=term).order_by(
            GlossTerm.id
        ).all()
        if not entries:
            print('term not found: ' + repr(term))
            return

        occs = occ_map({e.id for e in entries})
        clusters = cluster(entries)
        clusters.sort(key=lambda c: -sum(len(occs.get(e.id, [])) for e in c))

        total_occ = sum(len(occs.get(e.id, [])) for e in entries)
        print('term: ' + repr(term))
        print('  gloss rows:      ' + str(len(entries)))
        print('  occurrences:     ' + str(total_occ))
        print('  distinct senses: ' + str(len(clusters)))
        print('')

        for n, group in enumerate(clusters, start=1):
            group_occ = sum(len(occs.get(e.id, [])) for e in group)
            print('  --- sense ' + str(n) + ' (' + str(group_occ)
                  + ' occurrences, ' + str(len(group)) + ' wording(s)) ---')
            for entry in group:
                places = occs.get(entry.id, [])
                shown = ', '.join(
                    'ch' + str(c) + '/s' + str(s) for c, s in places[:6]
                )
                if len(places) > 6:
                    shown += ', +' + str(len(places) - 6) + ' more'
                print('    ' + entry.gloss)
                print('      id=' + str(entry.id) + '  [' + shown + ']')
            print('')

        if len(clusters) > 1:
            print('  VERDICT: genuinely polysemous. The tooltip must resolve')
            print('  per strophe, not by looking the word up.')
        else:
            print('  VERDICT: one sense, written several ways.')


def survey(min_glosses):
    with app.app_context():
        by_term = gather()
        all_ids = {e.id for entries in by_term.values() for e in entries}
        occs = occ_map(all_ids)

        polysemous = []
        single_sense = []

        for term, entries in by_term.items():
            clusters = cluster(entries)
            total_occ = sum(len(occs.get(e.id, [])) for e in entries)
            record = (term, len(entries), len(clusters), total_occ,
                      entries[0].is_phrase)
            if len(clusters) > 1:
                polysemous.append(record)
            else:
                single_sense.append(record)

        print('--- terms with more than one gloss: '
              + str(len(by_term)) + ' ---')
        print('')
        print('  one sense, several wordings:  ' + str(len(single_sense)))
        print('  genuinely several senses:     ' + str(len(polysemous)))
        if by_term:
            pct = 100.0 * len(polysemous) / len(by_term)
            print('  share truly polysemous:       '
                  + format(pct, '.1f') + '%')

        poly_words = [r for r in polysemous if not r[4]]
        poly_phrases = [r for r in polysemous if r[4]]
        print('')
        print('  polysemous words:   ' + str(len(poly_words)))
        print('  polysemous phrases: ' + str(len(poly_phrases)))

        print('')
        print('--- most polysemous terms (by distinct senses) ---')
        polysemous.sort(key=lambda r: (-r[2], -r[3]))
        for term, n_gloss, n_sense, n_occ, is_phrase in polysemous[:40]:
            if n_gloss < min_glosses:
                continue
            kind = 'phrase' if is_phrase else 'word'
            print('  ' + repr(term) + '  ' + str(n_sense) + ' senses from '
                  + str(n_gloss) + ' glosses, ' + str(n_occ)
                  + ' occurrences  [' + kind + ']')

        print('')
        print('--- repeated terms that are NOT polysemous ---')
        single_sense.sort(key=lambda r: -r[1])
        for term, n_gloss, _, n_occ, is_phrase in single_sense[:15]:
            kind = 'phrase' if is_phrase else 'word'
            print('  ' + repr(term) + '  ' + str(n_gloss)
                  + ' wordings of one sense, ' + str(n_occ)
                  + ' occurrences  [' + kind + ']')

        print('')
        print('Run with --term to see any single term broken out by sense.')


def export_csv():
    with app.app_context():
        by_term = gather()
        all_ids = {e.id for entries in by_term.values() for e in entries}
        occs = occ_map(all_ids)

        path = os.path.join(PROJECT_ROOT, 'gloss_senses.csv')
        with open(path, 'w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow([
                'term', 'kind', 'n_glosses', 'n_senses', 'n_occurrences',
                'sense_index', 'gloss', 'gloss_id', 'strophes',
            ])
            for term, entries in sorted(by_term.items()):
                clusters = cluster(entries)
                clusters.sort(
                    key=lambda c: -sum(len(occs.get(e.id, [])) for e in c)
                )
                total_occ = sum(len(occs.get(e.id, [])) for e in entries)
                kind = 'phrase' if entries[0].is_phrase else 'word'
                for index, group in enumerate(clusters, start=1):
                    for entry in group:
                        places = occs.get(entry.id, [])
                        writer.writerow([
                            term, kind, len(entries), len(clusters),
                            total_occ, index, entry.gloss, entry.id,
                            ' '.join(
                                'ch' + str(c) + '/s' + str(s)
                                for c, s in places
                            ),
                        ])
        print('wrote ' + path)
        print('Sort by n_senses descending to see the worst offenders.')
        print('UTF-8 with BOM, so Georgian renders in Excel directly.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--term', help='drill into one term')
    parser.add_argument('--min', type=int, default=2,
                        help='minimum gloss count when listing')
    parser.add_argument('--csv', action='store_true',
                        help='export every sense cluster to CSV')
    args = parser.parse_args()

    if args.csv:
        export_csv()
    elif args.term:
        drill(args.term)
    else:
        survey(args.min)


if __name__ == '__main__':
    main()
