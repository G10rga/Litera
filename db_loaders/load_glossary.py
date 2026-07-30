"""Load scraped utvalavi glosses into the Litera database.

Reads gloss_occurrences.csv (produced by scrape_glossary.py) and populates
the gloss_terms and gloss_occurrences tables.

This loader is idempotent. It never deletes existing rows, unlike
load_vefxistyaosani.py which wipes its table on every run. Re-running it
after a partial scrape only inserts what is missing.

Usage:
    python db_loaders/load_glossary.py
    python db_loaders/load_glossary.py --csv path/to/gloss_occurrences.csv
    python db_loaders/load_glossary.py --dry-run
    python db_loaders/load_glossary.py --backfill-local
    python db_loaders/load_glossary.py --verify
"""

import argparse
import csv
import os
import sys

# Allow running this file directly from db_loaders/ or from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402
from models import (  # noqa: E402
    GlossOccurrence,
    GlossTerm,
    VefxistyaosaniLine,
    db,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CSV = os.path.join(PROJECT_ROOT, 'gloss_occurrences.csv')

REQUIRED_COLUMNS = {'ganm_id', 'term', 'gloss', 'chapter_id', 'strophe_id'}


def as_bool(value):
    """Parse the many spellings of truth that survive a CSV round trip."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ('1', 'true', 't', 'yes', 'y')


def as_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def read_rows(csv_path):
    """Read and validate the CSV, returning a list of clean dicts."""
    if not os.path.exists(csv_path):
        sys.exit(f'ERROR: CSV not found at {csv_path}')

    rows = []
    skipped = 0

    with open(csv_path, encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)

        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            sys.exit(
                f'ERROR: CSV is missing required columns: {sorted(missing)}\n'
                f'       found: {reader.fieldnames}'
            )

        for line_no, raw in enumerate(reader, start=2):
            term = (raw.get('term') or '').strip()
            gloss = (raw.get('gloss') or '').strip()
            chapter_id = as_int(raw.get('chapter_id'))
            strophe_global = as_int(raw.get('strophe_id'))

            if not term or not gloss:
                skipped += 1
                continue
            if chapter_id is None or strophe_global is None:
                print(f'  line {line_no}: unusable chapter/strophe, skipped')
                skipped += 1
                continue

            rows.append({
                'ganm_id': (raw.get('ganm_id') or '').strip() or None,
                'term': term,
                'gloss': gloss,
                'chapter_id': chapter_id,
                'strophe_global': strophe_global,
                'is_phrase': as_bool(raw.get('is_phrase')),
            })

    if skipped:
        print(f'  skipped {skipped} unusable row(s)')

    return rows


def load(csv_path, dry_run=False):
    rows = read_rows(csv_path)
    print(f'read {len(rows)} rows from {csv_path}')

    if not rows:
        sys.exit('ERROR: nothing to load.')

    unique_pairs = {(r['term'], r['gloss']) for r in rows}
    print(f'  {len(unique_pairs)} unique term+gloss pairs')

    if dry_run:
        phrases = sum(1 for r in rows if r['is_phrase'])
        print(f'  {phrases} phrase rows, {len(rows) - phrases} single-word rows')
        print('dry run: nothing written')
        return

    with app.app_context():
        # --- terms -----------------------------------------------------
        term_cache = {
            (t.term, t.gloss): t.id
            for t in GlossTerm.query.with_entities(
                GlossTerm.id, GlossTerm.term, GlossTerm.gloss
            ).all()
        }
        print(f'existing gloss_terms: {len(term_cache)}')

        is_phrase_by_pair = {}
        for row in rows:
            is_phrase_by_pair[(row['term'], row['gloss'])] = row['is_phrase']

        new_terms = 0
        for pair in unique_pairs:
            if pair in term_cache:
                continue
            term, gloss = pair
            db.session.add(GlossTerm(
                term=term,
                gloss=gloss,
                is_phrase=is_phrase_by_pair[pair],
                source='utvalavi',
            ))
            new_terms += 1

        db.session.flush()

        # Re-read so newly flushed rows have their ids.
        term_cache = {
            (t.term, t.gloss): t.id
            for t in GlossTerm.query.with_entities(
                GlossTerm.id, GlossTerm.term, GlossTerm.gloss
            ).all()
        }
        print(f'  inserted {new_terms} new term(s)')

        # --- occurrences -----------------------------------------------
        seen = {
            (o.ganm_id, o.strophe_global, o.term_id)
            for o in GlossOccurrence.query.with_entities(
                GlossOccurrence.ganm_id,
                GlossOccurrence.strophe_global,
                GlossOccurrence.term_id,
            ).all()
        }
        print(f'existing gloss_occurrences: {len(seen)}')

        new_occurrences = 0
        for row in rows:
            term_id = term_cache[(row['term'], row['gloss'])]
            key = (row['ganm_id'], row['strophe_global'], term_id)
            if key in seen:
                continue
            seen.add(key)
            db.session.add(GlossOccurrence(
                term_id=term_id,
                chapter_id=row['chapter_id'],
                strophe_global=row['strophe_global'],
                ganm_id=row['ganm_id'],
            ))
            new_occurrences += 1

        db.session.commit()
        print(f'  inserted {new_occurrences} new occurrence(s)')

    verify()


def backfill_local():
    """Populate strophe_local from the poem's own chapter boundaries.

    Only meaningful if vefxistyaosani_lines numbers strophes per chapter.
    Chapter offsets are derived from the number of distinct strophes in each
    preceding chapter, so this requires vefxistyaosani_lines to be fully
    seeded first.
    """
    with app.app_context():
        counts = {}
        rows = (
            VefxistyaosaniLine.query
            .with_entities(
                VefxistyaosaniLine.chapter_id,
                VefxistyaosaniLine.strophe_id,
            )
            .distinct()
            .all()
        )
        for chapter_id, strophe_id in rows:
            if chapter_id is None or strophe_id is None:
                continue
            counts.setdefault(chapter_id, set()).add(strophe_id)

        if not counts:
            sys.exit('ERROR: vefxistyaosani_lines is empty; seed it first.')

        offsets = {}
        running = 0
        for chapter_id in sorted(counts):
            offsets[chapter_id] = running
            running += len(counts[chapter_id])

        print(f'derived offsets for {len(offsets)} chapters, {running} strophes total')

        updated = 0
        unmatched = 0
        for occurrence in GlossOccurrence.query.all():
            offset = offsets.get(occurrence.chapter_id)
            if offset is None:
                unmatched += 1
                continue
            local = occurrence.strophe_global - offset
            if local < 1 or local not in counts[occurrence.chapter_id]:
                unmatched += 1
                continue
            occurrence.strophe_local = local
            updated += 1

        db.session.commit()
        print(f'  strophe_local set on {updated} occurrence(s)')
        if unmatched:
            print(
                f'  WARNING: {unmatched} occurrence(s) did not map cleanly.\n'
                f'  That usually means vefxistyaosani_lines is incomplete or\n'
                f'  its chapter numbering differs from utvalavi. Investigate\n'
                f'  before trusting strophe_local.'
            )


def verify():
    with app.app_context():
        terms = GlossTerm.query.count()
        phrases = GlossTerm.query.filter_by(is_phrase=True).count()
        occurrences = GlossOccurrence.query.count()
        localised = GlossOccurrence.query.filter(
            GlossOccurrence.strophe_local.isnot(None)
        ).count()

        print('')
        print(f'gloss_terms:       {terms}')
        print(f'  single words:    {terms - phrases}')
        print(f'  phrases:         {phrases}')
        print(f'gloss_occurrences: {occurrences}')
        print(f'  with strophe_local: {localised}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', default=DEFAULT_CSV, help='path to gloss_occurrences.csv')
    parser.add_argument('--dry-run', action='store_true', help='parse and report, write nothing')
    parser.add_argument('--backfill-local', action='store_true', help='populate strophe_local only')
    parser.add_argument('--verify', action='store_true', help='print table counts only')
    args = parser.parse_args()

    if args.verify:
        verify()
    elif args.backfill_local:
        backfill_local()
    else:
        load(args.csv, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
