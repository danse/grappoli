"""Load a branch of notes.

A branch is a directory of text files, possibly nested. Every text file
under it is a note, whatever its extension or lack of one: an `.org`, a
`.txt` and a `.md` map the same. Notes are keyed by path relative to the
branch root, so a file's identity is stable however deep it sits; the
body text is loaded as-is — headings are not assumed to exist
(tests/fixtures/README.md).

Two paths are not notes and are skipped. A path with a hidden component —
a leading dot, as in `.git/` or the build directory `.grappoli/` — is
left out; skipping hidden paths as a class is also what keeps the build
directory out of its own map. And a file that does not decode as UTF-8 is
left out, so an image or a document left in the tree is not read as
prose. `tests/test_corpus.py` pins the rule.
"""

from pathlib import Path


def load_corpus(root: str | Path) -> dict[str, str]:
    root = Path(root)
    notes = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        notes[str(relative)] = text
    return notes
