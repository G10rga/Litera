from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Registered Litera scholar account."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    grade = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.id}: {self.email}>'


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


class ShushanikiText(db.Model):
    """ Model for storing Shushaniki literature """
    __tablename__ = 'shushaniki_main'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chapter = db.Column(db.Integer, nullable=True)




class GlossTerm(db.Model):
    """An archaic word or phrase from the original text, with its modern gloss.

    One term may carry several different glosses. utvalavi re-glosses words per
    passage, so a word such as 'khams' has a distinct reading in each place it
    appears. Uniqueness is therefore on (term, gloss), never on term alone.
    """
    __tablename__ = 'gloss_terms'

    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(256), nullable=False, index=True)
    gloss = db.Column(db.Text, nullable=False)
    is_phrase = db.Column(db.Boolean, default=False, index=True)
    source = db.Column(db.String(64), default='utvalavi')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    occurrences = db.relationship(
        'GlossOccurrence',
        backref='term_ref',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    __table_args__ = (
        db.UniqueConstraint('term', 'gloss', name='uq_gloss_term_gloss'),
    )

    def __repr__(self):
        return f'<GlossTerm {self.id}: {self.term}>'


class GlossOccurrence(db.Model):
    """Where a given gloss appears in the poem.

    strophe_global is utvalavi's continuous numbering across the whole poem.
    strophe_local is the within-chapter number, populated only once the
    numbering scheme of vefxistyaosani_lines has been confirmed.
    """
    __tablename__ = 'gloss_occurrences'

    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(
        db.Integer,
        db.ForeignKey('gloss_terms.id'),
        nullable=False,
        index=True,
    )
    chapter_id = db.Column(db.Integer, nullable=False, index=True)
    strophe_global = db.Column(db.Integer, nullable=False, index=True)
    strophe_local = db.Column(db.Integer, nullable=True, index=True)
    ganm_id = db.Column(db.String(32), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            'ganm_id',
            'strophe_global',
            'term_id',
            name='uq_gloss_occurrence',
        ),
    )

    def __repr__(self):
        return (
            f'<GlossOccurrence {self.id}: ch={self.chapter_id} '
            f'str={self.strophe_global}>'
        )
