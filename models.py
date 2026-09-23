from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def _utcnow() -> datetime:
    """Timezone-aware UTC default. datetime.utcnow() is deprecated in 3.12+."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """Registered Litera scholar account."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    grade = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    # Set (and advanced) whenever the password changes so open sessions die.
    password_reset_at = db.Column(db.DateTime, nullable=True)
    session_version = db.Column(db.Integer, nullable=False, default=0)

    def set_password(self, password: str) -> None:
        # Werkzeug 3 defaults to scrypt; pin method explicitly for audits.
        self.password_hash = generate_password_hash(password, method="scrypt")
        self.invalidate_sessions()

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def invalidate_sessions(self) -> None:
        """Bump the session version so every existing login cookie stops working."""
        self.session_version = int(self.session_version or 0) + 1
        self.password_reset_at = _utcnow()

    def get_id(self) -> str:
        # Flask-Login stores this string; changing session_version logs everyone out.
        return f"{self.id}.{int(self.session_version or 0)}"

    def __repr__(self):
        return f'<User {self.id}: {self.email}>'


class Aphorism(db.Model):
    """Model for Georgian aphorisms (aforizmebi)."""
    __tablename__ = 'aphorisms'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def __repr__(self):
        return f'<Aphorism {self.id}: {self.text[:50]}...>'


class VefxistyaosaniLine(db.Model):
    """Model for storing lines from Vefxistyaosani (The Knight in the Panther's Skin)."""
    __tablename__ = 'vefxistyaosani_lines'

    id = db.Column(db.Integer, primary_key=True)
    line = db.Column(db.Text, nullable=False)
    chapter = db.Column(db.String(255), nullable=True)
    chapter_id = db.Column(db.Integer, nullable=True, index=True)
    strophe_id = db.Column(db.Integer, nullable=True, index=True)
    line_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def __repr__(self):
        return f'<VefxistyaosaniLine {self.id}: {self.line[:50]}...>'


class ShushanikiText(db.Model):
    """Model for storing Shushaniki literature."""
    __tablename__ = 'shushaniki_main'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    chapter = db.Column(db.Integer, nullable=True, index=True)

    def __repr__(self):
        return f'<ShushanikiText {self.id}: chapter {self.chapter}>'


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
    created_at = db.Column(db.DateTime, default=_utcnow)

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
    created_at = db.Column(db.DateTime, default=_utcnow)

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


class ModernChapter(db.Model):
    """Modernised Georgian prose for one chapter of the poem."""

    __tablename__ = "modern_chapters"

    id = db.Column(db.Integer, primary_key=True)

    # Chapter number as used by VefxistyaosaniLine.chapter_id and by
    # utvalavi's saxelosno.php?t=<N>. Verified identical for t=1, t=2, t=6.
    chapter_id = db.Column(db.Integer, nullable=False, index=True)

    # Chapter heading in Georgian, e.g. "ამბავი როსტევან არაბთა მეფისა".
    title = db.Column(db.String(255), nullable=True)

    # Optional, for a "strophes 33-73" caption in the UI. Not used for
    # alignment, so leaving these NULL is harmless.
    strophe_start = db.Column(db.Integer, nullable=True, index=True)
    strophe_end = db.Column(db.Integer, nullable=True, index=True)

    # The full modernised chapter. Paragraphs are separated by a blank line
    # so the template can split on "\n\n" and emit one <p> each.
    text = db.Column(db.Text, nullable=False)

    # Provenance. 'utvalavi' for scraped/derived prose, 'manual' for your own.
    source = db.Column(db.String(64), nullable=False, default="utvalavi", index=True)

    # 'draft' | 'reviewed' | 'final'
    review_status = db.Column(db.String(16), nullable=False, default="draft")

    created_at = db.Column(db.DateTime, default=_utcnow)

    __table_args__ = (
        db.UniqueConstraint("source", "chapter_id", name="uq_modern_chapter"),
    )

    @property
    def paragraphs(self):
        """The chapter split back into paragraphs, for templating."""
        return [p.strip() for p in self.text.split("\n\n") if p.strip()]

    @property
    def paragraph_count(self):
        return len(self.paragraphs)

    @property
    def strophe_label(self):
        if self.strophe_start and self.strophe_end:
            return "%d-%d" % (self.strophe_start, self.strophe_end)
        return ""

    def __repr__(self):
        return "<ModernChapter ch%s %s %d para>" % (
            self.chapter_id,
            self.source,
            self.paragraph_count,
        )


class ShushanikiGloss(db.Model):
    """An archaic word or phrase from შუშანიკის წამება, with its gloss.

    Unlike the utvalavi glossary these are not positional. NPLG publishes one
    global word list applied by string match wherever a word occurs, so there
    is no strophe or paragraph anchor to record and nothing that can drift out
    of alignment with the text.
    """
    __tablename__ = 'shushaniki_glosses'

    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(256), nullable=False, index=True)
    gloss = db.Column(db.Text, nullable=False)

    # True only when the term contains whitespace. A hyphenated compound such
    # as ზრახვა-ყო is a single token in the running text, so treating it as a
    # phrase would stop it ever matching.
    is_phrase = db.Column(db.Boolean, default=False, index=True)

    source = db.Column(db.String(64), default='nplg', index=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    __table_args__ = (
        db.UniqueConstraint('term', 'gloss', name='uq_shushaniki_term_gloss'),
    )

    def __repr__(self):
        return f'<ShushanikiGloss {self.id}: {self.term}>'


class ShushanikiModern(db.Model):
    """Modernised Georgian text of შუშანიკის წამება, by section.

    chapter_id matches the roman section number of the original (I = 1 ...
    XX = 20), which is the same key the left-hand column uses after
    renumber_shushaniki.py has run.
    """
    __tablename__ = 'shushaniki_modern'

    id = db.Column(db.Integer, primary_key=True)

    chapter_id = db.Column(db.Integer, nullable=False, unique=True, index=True)

    title = db.Column(db.String(255), nullable=True)
    text = db.Column(db.Text, nullable=False)

    # draft | reviewed | final
    review_status = db.Column(db.String(16), nullable=False, default='draft')

    created_at = db.Column(db.DateTime, default=_utcnow)

    @property
    def paragraphs(self):
        """The stored text split back into display paragraphs."""
        return [p for p in self.text.split('\n\n') if p.strip()]

    @property
    def paragraph_count(self):
        return len(self.paragraphs)

    def __repr__(self):
        return f'<ShushanikiModern chapter {self.chapter_id}>'


class Work(db.Model):
    """One literary work, with its provenance.

    Provenance lives here rather than in a separate table because it is 1:1
    with the work, and because the Wikisource transcriptions are CC BY-SA 4.0 --
    attribution has to be available wherever the text is displayed.
    """
    __tablename__ = 'works'

    id = db.Column(db.Integer, primary_key=True)

    # Stable identifier, matching the manifest and the static folder name,
    # e.g. 'aluda-qetelauri'.
    slug = db.Column(db.String(64), nullable=False, unique=True, index=True)

    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=True)
    subtitle = db.Column(db.String(255), nullable=True)

    # 'verse' or 'prose'. Decides whether the reader renders one unit per line
    # or one unit per paragraph, and it is detected from the text rather than
    # guessed from the genre.
    kind = db.Column(db.String(16), nullable=False, default='prose')

    composed = db.Column(db.String(64), nullable=True)
    death_year = db.Column(db.Integer, nullable=True)

    # Provenance.
    source = db.Column(db.String(128), nullable=True)
    url = db.Column(db.Text, nullable=True)
    revision = db.Column(db.String(64), nullable=True)
    retrieved = db.Column(db.String(32), nullable=True)
    license = db.Column(db.String(64), nullable=True)
    sha256 = db.Column(db.String(64), nullable=True)

    # Set at load time so the reader does not have to COUNT on every request.
    unit_count = db.Column(db.Integer, nullable=False, default=0)
    section_count = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, default=_utcnow)

    units = db.relationship(
        'TextUnit',
        backref='work',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    def __repr__(self):
        return f'<Work {self.slug}>'


class TextUnit(db.Model):
    """One addressable piece of a work: a verse line, or a prose paragraph.

    Deliberately not called a strophe. Vefkhistkaosani has quatrains, Aluda has
    couplet sections that do not divide by four, and the prose works have
    paragraphs. The one thing they share is an ordered sequence of numbered
    pieces, so that is what this models.
    """
    __tablename__ = 'text_units'

    id = db.Column(db.Integer, primary_key=True)

    work_id = db.Column(
        db.Integer,
        db.ForeignKey('works.id'),
        nullable=False,
        index=True,
    )

    # Section number, 1-based. NULL for works with no divisions at all
    # (Memento Mori, Tano Tatano).
    section = db.Column(db.Integer, nullable=True, index=True)

    # The section marker as actually printed: 'II', 'I თავი'. Kept because the
    # source files disagree about marker style and the reader should be able to
    # show what the edition shows.
    section_label = db.Column(db.String(32), nullable=True)

    # Position within the section, 1-based.
    unit_index = db.Column(db.Integer, nullable=False)

    # Position within the whole work, 1-based and gapless. This is the stable
    # anchor for future glosses: it does not shift when a section boundary is
    # corrected, which is exactly what went wrong with the utvalavi glossary.
    unit_global = db.Column(db.Integer, nullable=False)

    # 'line' for verse, 'paragraph' for prose.
    kind = db.Column(db.String(16), nullable=False, default='line')

    text = db.Column(db.Text, nullable=False)

    # Opens with a dash. Georgian prose marks speech this way, and the prose
    # works here are dialogue-heavy (58 of 111 paragraphs in Gogia Uishvili).
    is_dialogue = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=_utcnow)

    __table_args__ = (
        # Scoped by work_id, so two works cannot fight over the same number.
        db.UniqueConstraint('work_id', 'unit_global', name='uq_text_unit_global'),
        db.Index('ix_text_unit_work_section', 'work_id', 'section'),
    )

    def __repr__(self):
        return f'<TextUnit w{self.work_id} #{self.unit_global}>'


class ModernSection(db.Model):
    """Modernised Georgian for one section of one work.

    Scoped by work_id for the same reason text_units is: a NOT NULL foreign key
    cannot be forgotten in a query the way an optional source string can.

    NOTE: this class used to be nested inside TextUnit, which made it
    unreachable as models.ModernSection and forced every blueprint to guard its
    import in a try/except. It is now a module-level model.
    """
    __tablename__ = 'modern_sections'

    id = db.Column(db.Integer, primary_key=True)

    work_id = db.Column(
        db.Integer,
        db.ForeignKey('works.id'),
        nullable=False,
        index=True,
    )

    # 0 means "the whole work", used by works with no sections at all
    # (Memento Mori, Tano Tatano).
    #
    # NOT NULL with a sentinel rather than nullable, deliberately. SQLite (and
    # the SQL standard) treat NULLs as distinct in a UNIQUE constraint, so a
    # nullable section column would happily accept ten "whole work" rows for
    # the same work and the reader would pick one at random.
    section = db.Column(db.Integer, nullable=False, default=0, index=True)

    title = db.Column(db.String(255), nullable=True)
    text = db.Column(db.Text, nullable=False)

    review_status = db.Column(db.String(16), nullable=False, default='draft')

    created_at = db.Column(db.DateTime, default=_utcnow)

    work = db.relationship('Work', backref=db.backref(
        'modern_sections', lazy='dynamic', cascade='all, delete-orphan'))

    __table_args__ = (
        db.UniqueConstraint('work_id', 'section', name='uq_modern_section'),
    )

    @property
    def paragraphs(self):
        """Split the stored blob back into display paragraphs."""
        return [p.strip() for p in (self.text or '').split('\n\n') if p.strip()]

    @property
    def paragraph_count(self):
        return len(self.paragraphs)

    def __repr__(self):
        return f'<ModernSection w{self.work_id} s{self.section}>'


class ContactMessage(db.Model):
    """A message submitted through /contact.

    Stored rather than emailed so that the confirmation shown to the user is
    truthful: the message really has been persisted and can be read back with
    `flask messages`.
    """
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    subject = db.Column(db.String(160), nullable=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)
    handled = db.Column(db.Boolean, default=False, index=True)

    def __repr__(self):
        return f'<ContactMessage {self.id} from {self.email}>'
