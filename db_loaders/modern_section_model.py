# ---------------------------------------------------------------------------
# Paste into models.py, below Work and TextUnit.
#
# The modernised counterpart of text_units. One row per (work, section), so the
# reader can put original and modern side by side.
# ---------------------------------------------------------------------------


class ModernSection(db.Model):
    """Modernised Georgian for one section of one work.

    Scoped by work_id for the same reason text_units is: a NOT NULL foreign key
    cannot be forgotten in a query the way an optional source string can.
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

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
