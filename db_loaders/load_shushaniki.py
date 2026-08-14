#!/usr/bin/env python
"""Script to load Shushaniki texts from CSV into the database."""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
from app import app, db
from models import ShushanikiText

CSV_PATH = os.path.join(PROJECT_ROOT, "static", "Literature", "shushaniki-Sheet1.csv")


def load_shushaniki():
    """Load Shushaniki texts from CSV into the database."""
    with app.app_context():
        try:
            # Read the CSV file
            csv_path = CSV_PATH
            print(f"Reading {csv_path}...")
            df = pd.read_csv(csv_path)

            print(f"Found {len(df)} lines in the file")
            print(f"Columns: {list(df.columns)}")

            # Verify required columns
            expected_columns = {'text', 'chapter'}
            actual_columns = set(df.columns)

            if not expected_columns.issubset(actual_columns):
                print(f"Error: CSV must contain columns: {', '.join(expected_columns)}")
                print(f"Found columns: {', '.join(actual_columns)}")
                return

            # Clear existing data
            ShushanikiText.query.delete()
            print("Cleared existing lines from database")

            # Add rows to database
            count = 0
            for _, row in df.iterrows():
                line_obj = ShushanikiText(
                    text=str(row["text"]) if pd.notna(row["text"]) else "",
                    chapter=int(row["chapter"]) if pd.notna(row["chapter"]) else None,
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
            total = ShushanikiText.query.count()
            print(f"Total lines in Shushaniki table: {total}")

        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    load_shushaniki()