"""Inspect phrase repetition and flag suspicious short terms.

Answers two questions:
  1. Are phrases repeated in the database, and how badly?
  2. Are the very short terms real glossary entries, or scraper fragments?

Usage:
    python db_loaders/inspect_phrases.py
    python db_loaders/inspect_phrases.py --phrases
    python db_loaders/inspect_phrases.py --suspicious
    python db_loaders/inspect_phrases.py --ganm ganm_6872
"""

import argparse
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402
from models import GlossOccurrence, GlossTerm, db  # noqa: E402

# Ordinary Georgian function words. A glossary has no reason to annotate
# these, so their presence points at extraction problems.
FUNCTION_WORDS = {
    'da', 'ra', 'man', 'ar', 'is', 'mas', 'me', 'shen', 'chven',
}
GEORGIAN_FUNCTION_WORDS = {
    '\u10d3\u10d0',          # da   (and)
    '\u10e0\u10d0',          # ra   (what)
    '\u10db\u10d0\u10dc',    # man  (he/she, erg.)
    '\u10d0\u10e0',          # ar   (not)
    '\u10d2\u10d0',          # ga   (not a word)
    '\u10d5\u10d0',          # va   (interjection at best)
    '\u10d0\u10e0\u10d4',    # are
}


def phrase_report():
    with app.app_context():
        phrases = GlossTerm.query.filter_by(is_phrase=True).all()
        words = GlossTerm.query.filter_by(is_phrase=False).all()

        phrase_terms = Counter(p.term for p in phrases)
        word_terms = Counter(w.term for w in words)

        repeated = {t: n for t, n in phrase_terms.items() if n > 1}

        print('--- phrase repetition ---')
        print(f'  phrase pairs:            {len(phrases)}')
        print(f'  distinct phrases:        {len(phrase_terms)}')
        print(f'  phrases with >1 gloss:   {len(repeated)}')
        if phrase_terms:
            print(f'  glosses per phrase:      '
                  f'{len(phrases) / len(phrase_terms):.3f}')

        print('')
        print('--- word repetition, for contrast ---')
        print(f'  word pairs:              {len(words)}')
        print(f'  distinct words:          {len(word_terms)}')
        print(f'  words with >1 gloss:     '
              f'{sum(1 for n in word_terms.values() if n > 1)}')
        if word_terms:
            print(f'  glosses per word:        '
                  f'{len(words) / len(word_terms):.3f}')

        if repeated:
            print('')
            print('--- most re-glossed phrases ---')
            for term, count in sorted(
                repeated.items(), key=lambda kv: -kv[1]
            )[:15]:
                print(f'  {term}  x{count}')
                for entry in GlossTerm.query.filter_by(
                    term=term, is_phrase=True
                ).all():
                    n = GlossOccurrence.query.filter_by(
                        term_id=entry.id
                    ).count()
                    print(f'      [{n} occ] {entry.gloss}')

        # Repetition at the occurrence level is a different question:
        # one phrase+gloss pair can still be attached to many strophes.
        print('')
        print('--- phrase pairs attached to more than one strophe ---')
        multi_strophe = 0
        for phrase in phrases:
            n = (
                db.session.query(GlossOccurrence.strophe_global)
                .filter_by(term_id=phrase.id)
                .distinct()
                .count()
            )
            if n > 1:
                multi_strophe += 1
        print(f'  {multi_strophe} of {len(phrases)} phrase pairs span '
              f'multiple strophes')
        print('  (a paraphrase of one line should normally appear once,')
        print('   so a high number here would suggest mis-assignment)')


def suspicious_report():
    with app.app_context():
        rows = GlossTerm.query.all()

        short = [r for r in rows if len(r.term) <= 2]
        function = [r for r in rows if r.term in GEORGIAN_FUNCTION_WORDS]

        print('--- very short terms (2 characters or fewer) ---')
        print(f'  count: {len(short)}')
        by_term = defaultdict(list)
        for row in short:
            by_term[row.term].append(row)
        for term, entries in sorted(
            by_term.items(), key=lambda kv: -len(kv[1])
        )[:20]:
            total_occ = sum(
                GlossOccurrence.query.filter_by(term_id=e.id).count()
                for e in entries
            )
            print(f'  {term!r}  {len(entries)} gloss(es), {total_occ} occurrence(s)')
            for entry in entries[:3]:
                print(f'      {entry.gloss[:80]}')

        print('')
        print('--- ordinary function words that should not be glossed ---')
        print(f'  count: {len(function)}')
        for row in function:
            n = GlossOccurrence.query.filter_by(term_id=row.id).count()
            print(f'  {row.term!r}  [{n} occ]  {row.gloss[:70]}')

        print('')
        print('--- interpretation ---')
        print('  If the glosses attached to these look like definitions of a')
        print('  LONGER phrase that merely contains the short term, then the')
        print('  scraper captured a text-node fragment instead of the whole')
        print('  span, and those rows should be re-scraped, not kept.')


def ganm_report(ganm_id):
    with app.app_context():
        occurrences = GlossOccurrence.query.filter_by(ganm_id=ganm_id).all()
        if not occurrences:
            print(f'no occurrences with ganm_id={ganm_id}')
            return

        print(f'--- {ganm_id}: {len(occurrences)} occurrence(s) ---')
        for occurrence in occurrences:
            term = db.session.get(GlossTerm, occurrence.term_id)
            print(f'  chapter={occurrence.chapter_id} '
                  f'strophe={occurrence.strophe_global}')
            print(f'    term:  {term.term!r} (is_phrase={term.is_phrase})')
            print(f'    gloss: {term.gloss}')

        print('')
        print('  A single definition div serving several different terms in')
        print('  one strophe means the term text was split incorrectly.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phrases', action='store_true',
                        help='phrase repetition only')
    parser.add_argument('--suspicious', action='store_true',
                        help='short and function-word terms only')
    parser.add_argument('--ganm', metavar='ID',
                        help='dump every occurrence sharing one ganm id')
    args = parser.parse_args()

    if args.ganm:
        ganm_report(args.ganm)
    elif args.suspicious:
        suspicious_report()
    elif args.phrases:
        phrase_report()
    else:
        phrase_report()
        print('')
        print('=' * 60)
        print('')
        suspicious_report()


if __name__ == '__main__':
    main()
