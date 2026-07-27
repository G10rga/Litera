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

