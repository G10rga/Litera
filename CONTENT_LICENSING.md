# Content provenance and licensing

Litera splits **code** and **content** licences. See `LICENSE` (software) and
this file (literary text, glosses, modern renderings).

## Rule of thumb

| Material | Status on Litera | Action before public launch |
| --- | --- | --- |
| Classical originals (Rustaveli, *Martyrdom of Shushanik*, 19th-c. authors past copyright) | Public domain in Georgia and most jurisdictions | Keep attribution for the *transcription* |
| Wikisource / NPLG transcriptions | Usually CC BY-SA or similar — check each `source.json` | Keep licence + revision on every reader page |
| Modern Georgian renderings | **Not** public domain by default | Only ship text you wrote, commissioned, or cleared |
| Scholarly glosses (utvalavi, NPLG word lists) | Third-party; educational reuse may not equal redistribution rights | Verify terms; replace or remove if unclear |

## Datasets under `db_loaders/` / `static/Literature/`

| Loader / path | What it loads | Provenance notes |
| --- | --- | --- |
| `load_vefxistyaosani.py` | Poem lines | Classical text PD; confirm CSV edition licence |
| `load_glossary.py` | utvalavi glosses | Third-party scholarly glosses — **verify before public** |
| `load_modern_chapters.py` | Modern prose for ვეფხისტყაოსანი | Modern Georgian — **not PD**; verify authorship |
| `load_shushaniki.py` | Original sections | Classical PD |
| `load_shushaniki_glossary.py` | NPLG word list | National library glossary — check reuse terms |
| `load_shushaniki_modern.py` | Modernised შუშანიკი | Modern Georgian — **verify** |
| `load_literature.py` | Works under `static/Literature/*/text.txt` | Each folder’s `source.json` is authoritative |
| `load_aphorisms.py` | Aphorism list | Confirm compilation copyright |

Each `static/Literature/<slug>/source.json` should record: `source`, `url`,
`revision`, `retrieved`, `license`, `sha256`.

## Before going public

1. Walk every `source.json` and tick that the printed licence matches the file.
2. Decide ownership of every modern rendering (`draft` / `reviewed` / `final`).
3. If a modern text or gloss cannot be cleared, remove it from production DB
   and keep the original-only column.
4. Keep takedown contact live on Terms / Privacy (`CONTACT_EMAIL`).

This file is the living register; update it when a new loader or corpus is added.
