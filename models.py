from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Aphorism(db.Model):
    """Model for Georgian aphorisms (aforizmebi)."""
    __tablename__ = 'aphorisms'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Aphorism {self.id}: {self.text[:50]}...>'


class VefxistyaosaniLine(db.Model):
    """Model for storing lines from Vefxistyaosani (The Knight in the Panther's Skin)."""
    __tablename__ = 'vefxistyaosani_lines'

    id = db.Column(db.Integer, primary_key=True)
    line = db.Column(db.Text, nullable=False)
    chapter = db.Column(db.String(255), nullable=True)
    chapter_id = db.Column(db.Integer, nullable=True)
    strophe_id = db.Column(db.Integer, nullable=True)
    line_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<VefxistyaosaniLine {self.id}: {self.line[:50]}...>'


