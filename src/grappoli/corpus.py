"""Load a branch of notes.

A branch is a directory of markdown files, possibly nested. Notes are
keyed by path relative to the branch root, so a file's identity is
stable however deep it sits; the body text is loaded as-is — headings
are not assumed to exist (tests/fixtures/README.md).
"""

from pathlib import Path


def load_corpus(root: str | Path) -> dict[str, str]:
    root = Path(root)
    files = sorted(p for p in root.rglob("*.md") if p.is_file())
    return {str(p.relative_to(root)): p.read_text() for p in files}