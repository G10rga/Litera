"""Reconcile the loaded glossary against the scraper's summary line.

The scraper printed:
    8858 unique term+gloss pairs (4912 single words)

Those two numbers count different things. 8858 is a count of (term, gloss)
pairs; 4912 is a count of distinct terms. This script reports both units
side by side so the reconciliation is explicit rather than assumed.

Usage:
    python db_loaders/verify_glossary.py
"""

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402
from models import GlossOccurrence, GlossTerm, db  # noqa: E402


def main():
    with app.app_context():
        rows = GlossTerm.query.with_entities(
            GlossTerm.id, GlossTerm.term, GlossTerm.is_phrase
        ).all()

        if not rows:
            sys.exit('ERROR: gloss_terms is empty. Run load_glossary.py first.')

        word_pairs = [r for r in rows if not r.is_phrase]
        phrase_pairs = [r for r in rows if r.is_phrase]

        distinct_words = {r.term for r in word_pairs}
        distinct_phrases = {r.term for r in phrase_pairs}
        distinct_all = {r.term for r in rows}

        print('--- counted as (term, gloss) pairs ---')
        print(f'  total pairs:        {len(rows)}')
        print(f'    single-word:      {len(word_pairs)}')
        print(f'    phrase:           {len(phrase_pairs)}')

        print('')
        print('--- counted as distinct terms ---')
        print(f'  distinct terms:     {len(distinct_all)}')
        print(f'    single-word:      {len(distinct_words)}')
        print(f'    phrase:           {len(distinct_phrases)}')

        print('')
        print('--- reconciliation with scraper output ---')
        print(f'  scraper said 8858 pairs;        db has {len(rows)}')
        print(f'  scraper said 4912 single words; db has {len(distinct_words)} distinct')
        if len(distinct_words) == 4912:
            print('  MATCH: 4912 was a distinct-term count, as suspected.')
        else:
            print('  NO MATCH: 4912 means something else. Investigate.')

        # How often is one term given several different readings?
        per_term = Counter(r.term for r in rows)
        multi = {t: n for t, n in per_term.items() if n > 1}
        total_glosses_on_multi = sum(multi.values())

        print('')
        print('--- re-glossing (same term, different readings) ---')
        print(f'  terms with exactly one gloss:  {len(per_term) - len(multi)}')
        print(f'  terms with several glosses:    {len(multi)}')
        print(f'  pairs held by those terms:     {total_glosses_on_multi}')
        if word_pairs:
            ratio = len(word_pairs) / max(len(distinct_words), 1)
            print(f'  glosses per distinct word:     {ratio:.2f}')

        print('')
        print('  most re-glossed terms:')
        for term, count in per_term.most_common(10):
            print(f'    {term}  x{count}')

        # Spot-check a known case.
        print('')
        print('--- spot check: khams ---')
        target = '\u10ee\u10d0\u10db\u10e1'  # ხამს
        entries = GlossTerm.query.filter_by(term=target).all()
        if entries:
            for entry in entries:
                n = GlossOccurrence.query.filter_by(term_id=entry.id).count()
                print(f'  id={entry.id} occurrences={n}')
                print(f'    {entry.gloss}')
        else:
            print('  not found')

        print('')
        print('--- occurrences ---')
        print(f'  gloss_occurrences:  {GlossOccurrence.query.count()}')
        print(f'  distinct chapters:  '
              f'{db.session.query(GlossOccurrence.chapter_id).distinct().count()}')
        print(f'  distinct strophes:  '
              f'{db.session.query(GlossOccurrence.strophe_global).distinct().count()}')


if __name__ == '__main__':
    main()
