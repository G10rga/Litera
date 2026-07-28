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




