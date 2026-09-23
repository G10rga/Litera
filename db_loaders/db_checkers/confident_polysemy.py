"""Separate real polysemy from synonym over-splitting.

compare_meanings.py clusters glosses by shared content words. That fails in
two opposite ways:

  over-split:  6 short glosses using 6 different synonyms for ONE meaning
               land in 6 clusters, because they share no vocabulary.
  under-split: transitive linking fuses senses via a bridging gloss.

This script grades each polysemous term by how much the evidence supports
the split, using one simple test: a sense cluster is CORROBORATED when at
least two independently written glosses fell into it. Two editors reaching
for overlapping vocabulary is evidence the sense is real; a lone one-word
gloss sitting by itself is not.

Tiers:
  strong    2+ corroborated clusters      -- trust the split
  moderate  1 corroborated + singletons   -- probably real, verify
  weak      all clusters are singletons   -- likely synonym over-splitting

Usage:
    python db_loaders/confident_polysemy.py
    python db_loaders/confident_polysemy.py --tier strong
    python db_loaders/confident_polysemy.py --tier weak
    python db_loaders/confident_polysemy.py --csv
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

NON_GEORGIAN = re.compile('[^\u10a0-\u10ff]+')

STOPWORDS = {
    '\u10d3\u10d0',
    '\u10d0\u10dc',
    '\u10d0\u10e0\u10d8\u10e1',
    '\u10d0\u10e5',
    '\u10d8\u10e1',
    '\u10e0\u10dd\u10db',
    '\u10d7\u10e3',
    '\u10d0\u10e0',
    '\u10d4\u10e1',
    '\u10d8\u10e1\u10d8\u10dc\u10d8',
    '\u10d5\u10d8\u10e0\u10d4',
    '\u10ec\u10d8\u10dc',
}

MIN_TOKEN_LEN = 2


def tokens(gloss):
    if not gloss:
        return set()
    parts = NON_GEORGIAN.sub(' ', gloss).split()
    return {p for p in parts if len(p) >= MIN_TOKEN_LEN and p not in STOPWORDS}


def cluster(entries):
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

    sets = [tokens(e.gloss) for e in entries]
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            if sets[i] & sets[j]:
                union(i, j)

    groups = defaultdict(list)
    for i, entry in enumerate(entries):
        groups[find(i)].append(entry)
    return list(groups.values())


def grade(clusters):
    """Return (tier, n_corroborated, n_singleton)."""
    corroborated = sum(1 for c in clusters if len(c) >= 2)
    singleton = sum(1 for c in clusters if len(c) == 1)
    if len(clusters) < 2:
        return 'single', corroborated, singleton
    if corroborated >= 2:
        return 'strong', corroborated, singleton
    if corroborated == 1:
        return 'moderate', corroborated, singleton
    return 'weak', corroborated, singleton


def mean_gloss_len(entries):
    lengths = [len(tokens(e.gloss)) for e in entries]
    if not lengths:
        return 0.0
    return sum(lengths) / len(lengths)


def occ_counts(term_ids):
    result = defaultdict(int)
    rows = (
        db.session.query(GlossOccurrence.term_id)
        .filter(GlossOccurrence.term_id.in_(list(term_ids)))
        .all()
    )
    for (term_id,) in rows:
        result[term_id] += 1
    return result


def analyse():
    by_term = defaultdict(list)
    for entry in GlossTerm.query.order_by(GlossTerm.id).all():
        by_term[entry.term].append(entry)
    by_term = {t: e for t, e in by_term.items() if len(e) > 1}

    all_ids = {e.id for entries in by_term.values() for e in entries}
    counts = occ_counts(all_ids)

    records = []
    for term, entries in by_term.items():
        clusters = cluster(entries)
        tier, corroborated, singleton = grade(clusters)
        records.append({
            'term': term,
            'kind': 'phrase' if entries[0].is_phrase else 'word',
            'n_glosses': len(entries),
            'n_senses': len(clusters),
            'tier': tier,
            'corroborated': corroborated,
            'singleton': singleton,
            'occurrences': sum(counts.get(e.id, 0) for e in entries),
            'avg_gloss_words': mean_gloss_len(entries),
            'clusters': clusters,
        })
    return records


def report(tier_filter):
    with app.app_context():
        records = analyse()

        tiers = defaultdict(list)
        for record in records:
            tiers[record['tier']].append(record)

        total_poly = sum(
            len(tiers[t]) for t in ('strong', 'moderate', 'weak')
        )

        print('--- how much to trust the polysemy split ---')
        print('')
        print('  single sense:              ' + str(len(tiers['single'])))
        print('  strong  (2+ corroborated): ' + str(len(tiers['strong'])))
        print('  moderate (1 corroborated): ' + str(len(tiers['moderate'])))
        print('  weak (all singletons):     ' + str(len(tiers['weak'])))
        print('')
        print('  reported polysemous:       ' + str(total_poly))
        print('  defensible (strong+mod):   '
              + str(len(tiers['strong']) + len(tiers['moderate'])))
        print('  suspect (weak):            ' + str(len(tiers['weak'])))

        weak = tiers['weak']
        if weak:
            avg_weak = sum(r['avg_gloss_words'] for r in weak) / len(weak)
            print('')
            print('  avg words per gloss, weak tier:   '
                  + format(avg_weak, '.2f'))
        strong = tiers['strong']
        if strong:
            avg_strong = sum(
                r['avg_gloss_words'] for r in strong
            ) / len(strong)
            print('  avg words per gloss, strong tier: '
                  + format(avg_strong, '.2f'))
            print('')
            print('  (if weak glosses are much shorter, that confirms')
            print('   short synonym lists are driving the over-split)')

        for name in (['strong', 'moderate', 'weak']
                     if not tier_filter else [tier_filter]):
            group = sorted(
                tiers[name],
                key=lambda r: (-r['n_senses'], -r['occurrences']),
            )
            if not group:
                continue
            print('')
            print('=' * 60)
            print('--- ' + name + ' tier: ' + str(len(group)) + ' term(s) ---')
            limit = 40 if tier_filter else 15
            for record in group[:limit]:
                print('')
                print('  ' + repr(record['term']) + '  '
                      + str(record['n_senses']) + ' senses / '
                      + str(record['n_glosses']) + ' glosses, '
                      + str(record['occurrences']) + ' occ  ['
                      + record['kind'] + ']')
                for n, group_c in enumerate(record['clusters'], start=1):
                    mark = '*' if len(group_c) >= 2 else ' '
                    joined = ' / '.join(e.gloss for e in group_c[:3])
                    if len(joined) > 90:
                        joined = joined[:90] + '...'
                    print('   ' + mark + ' sense ' + str(n) + ': ' + joined)
            if len(group) > limit:
                print('')
                print('  ... and ' + str(len(group) - limit) + ' more')

        print('')
        print('  (* marks a corroborated cluster: 2+ glosses agreed)')


def export_csv():
    with app.app_context():
        records = analyse()
        path = os.path.join(PROJECT_ROOT, 'gloss_polysemy_tiers.csv')
        with open(path, 'w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow([
                'term', 'kind', 'tier', 'n_glosses', 'n_senses',
                'corroborated_clusters', 'singleton_clusters',
                'occurrences', 'avg_gloss_words', 'senses',
            ])
            for record in sorted(
                records,
                key=lambda r: (r['tier'], -r['n_senses']),
            ):
                senses = ' || '.join(
                    ' / '.join(e.gloss for e in c)
                    for c in record['clusters']
                )
                writer.writerow([
                    record['term'], record['kind'], record['tier'],
                    record['n_glosses'], record['n_senses'],
                    record['corroborated'], record['singleton'],
                    record['occurrences'],
                    format(record['avg_gloss_words'], '.2f'),
                    senses,
                ])
        print('wrote ' + path)
        print('Filter tier=weak to review the suspected over-splits.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tier', choices=['strong', 'moderate', 'weak'],
                        help='show only one tier, in more depth')
    parser.add_argument('--csv', action='store_true',
                        help='export tiers to CSV')
    args = parser.parse_args()

    if args.csv:
        export_csv()
    else:
        report(args.tier)


if __name__ == '__main__':
    main()
