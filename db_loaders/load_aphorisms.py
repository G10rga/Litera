#!/usr/bin/env python
"""Script to load Georgian aphorisms from aforizmebi.txt into the database."""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app import app, db
from models import Aphorism

APHORISMS_PATH = os.path.join(PROJECT_ROOT, "static", "Literature", "aforizmebi.txt")


def load_aphorisms():
    """Load aphorisms from aforizmebi.txt into the database."""
    with app.app_context():
        # Read the file
        with open(APHORISMS_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Filter out empty lines and whitespace-only lines
        aphorisms = [line.strip() for line in lines if line.strip()]

        print(f"Found {len(aphorisms)} aphorisms in the file")

        # Add aphorisms to database
        count = 0
        for aphorism_text in aphorisms:
            # Check if aphorism already exists
            existing = Aphorism.query.filter_by(text=aphorism_text).first()
            if not existing:
                aphorism = Aphorism(text=aphorism_text)
                db.session.add(aphorism)
                count += 1

        # Commit all changes
        db.session.commit()
        print(f"Successfully added {count} new aphorisms to the database")

        # Display total aphorisms in database
        total = Aphorism.query.count()
        print(f"Total aphorisms in database: {total}")


if __name__ == '__main__':
    load_aphorisms()

