#!/usr/bin/env python
"""Script to load Vefxistyaosani lines from CSV into the database."""

from app import app, db
from models import VefxistyaosaniLine
import pandas as pd


def load_vefxistyaosani():
    """Load vefxistyaosani lines from CSV into the database."""
    with app.app_context():
        try:
            # Read the CSV file
            csv_path = 'static/literature/vefxistyaosani.csv'
            print(f"Reading {csv_path}...")
            df = pd.read_csv(csv_path)

            print(f"Found {len(df)} lines in the file")
            print(f"Columns: {list(df.columns)}")

            # Verify required columns
            expected_columns = {'id', 'line', 'chapter', 'chapter_id', 'strophe_id', 'line_id'}
            actual_columns = set(df.columns)

            if not expected_columns.issubset(actual_columns):
                print(f"Error: CSV must contain columns: {', '.join(expected_columns)}")
                print(f"Found columns: {', '.join(actual_columns)}")
                return

            # Clear existing data
            VefxistyaosaniLine.query.delete()
            print("Cleared existing lines from database")

            # Add rows to database
            count = 0
            for _, row in df.iterrows():
                line_obj = VefxistyaosaniLine(
                    line=str(row['line']) if pd.notna(row['line']) else '',
                    chapter=str(row['chapter']) if pd.notna(row['chapter']) else None,
                    chapter_id=int(row['chapter_id']) if pd.notna(row['chapter_id']) else None,
                    strophe_id=int(row['strophe_id']) if pd.notna(row['strophe_id']) else None,
                    line_id=int(row['line_id']) if pd.notna(row['line_id']) else None
                )
                db.session.add(line_obj)
                count += 1

                # Commit in batches to avoid memory issues
                if count % 1000 == 0:
                    db.session.commit()
                    print(f"  Processed {count} lines...")

            # Final commit
            db.session.commit()
            print(f"\nSuccessfully added {count} lines to the database")

            # Display total lines in database
            total = VefxistyaosaniLine.query.count()
            print(f"Total lines in database: {total}")

        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    load_vefxistyaosani()

