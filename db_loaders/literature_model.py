# ---------------------------------------------------------------------------
# Paste both classes into models.py.
#
# These SUPERSEDE AludaLine and TextSource from the previous turn. If you have
# not yet run the aluda migration, delete those two classes before pasting
# these. If you have, see the note at the bottom of this file.
#
# Why a shared table this time, having argued for separate tables twice:
#
#   The glossary bug was not caused by sharing a table. It was caused by a
#   shared table whose discriminator was an OPTIONAL string. GLOSS_SOURCES was
#   a tuple I could get wrong, source had a default, and a query that forgot to
#   filter still returned rows -- just the wrong ones. Failure was silent.
#
#   work_id is a NOT NULL foreign key. Unique constraints are scoped by it, so
#   two works cannot collide on unit numbering. A query that forgets to scope
#   by work returns every work at once, which is obvious immediately rather
#   than subtly wrong.
#
#   The manifest lists 20 works. Twenty models, twenty loaders and twenty
#   migrations to express "a numbered piece of text belonging to a work" is
#   worse, not safer.
# ---------------------------------------------------------------------------


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

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        # Scoped by work_id, so two works cannot fight over the same number.
        db.UniqueConstraint('work_id', 'unit_global', name='uq_text_unit_global'),
        db.Index('ix_text_unit_work_section', 'work_id', 'section'),
    )

    def __repr__(self):
        return f'<TextUnit w{self.work_id} #{self.unit_global}>'


# ---------------------------------------------------------------------------
# If you ALREADY created aluda_lines and text_sources:
#
# Delete the AludaLine and TextSource classes, paste these two, then generate a
# migration. Alembic will drop the old tables. Aluda is reloaded from
# static/literature/aluda-qetelauri/ by load_literature.py, so nothing is lost.
#
#   flask db migrate -m "works and text_units, replacing per-work tables"
#   flask db upgrade
#
# Read the generated migration before upgrading. Autogenerate cannot tell a
# rename from a drop-plus-add, and a drop discards the rows.
# ---------------------------------------------------------------------------
