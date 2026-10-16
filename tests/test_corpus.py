"""The loader decides what a note is.

A branch is a directory of text files, and these pin which files become
notes. Any extension (or none) counts, nested notes are keyed by their
path relative to the root, and the body is loaded as-is. Two paths are
not notes: a hidden one — a leading dot, which is what keeps the build
directory `.grappoli/` out of its own map — and a file that is not UTF-8
text, so an image left in the tree is not read as prose.
"""

from grappoli.corpus import load_corpus


def _write(root, name, text="body"):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_loads_notes_of_any_extension(tmp_path):
    _write(tmp_path, "a.md", "alpha")
    _write(tmp_path, "b.txt", "beta")
    _write(tmp_path, "c.org", "gamma")
    _write(tmp_path, "no-extension", "delta")
    assert load_corpus(tmp_path) == {
        "a.md": "alpha", "b.txt": "beta", "c.org": "gamma", "no-extension": "delta"}


def test_keys_are_paths_relative_to_the_root(tmp_path):
    _write(tmp_path, "top.txt", "t")
    _write(tmp_path, "sub/deep/note.txt", "d")
    assert load_corpus(tmp_path) == {"top.txt": "t", "sub/deep/note.txt": "d"}


def test_the_body_text_is_loaded_as_is(tmp_path):
    text = "first line\n\nsecond — with punctuation and a # hash\n"
    _write(tmp_path, "note.txt", text)
    assert load_corpus(tmp_path)["note.txt"] == text


def test_the_build_directory_is_not_a_note(tmp_path):
    _write(tmp_path, "note.md", "a note")
    _write(tmp_path, ".grappoli/map.json", "{}")
    _write(tmp_path, ".grappoli/characterisations", "")
    assert load_corpus(tmp_path) == {"note.md": "a note"}


def test_hidden_files_and_directories_are_not_notes(tmp_path):
    _write(tmp_path, "note.md", "a note")
    _write(tmp_path, ".hidden.md", "hidden file")
    _write(tmp_path, ".git/config", "[core]")
    _write(tmp_path, "sub/.hidden", "hidden inside")
    assert load_corpus(tmp_path) == {"note.md": "a note"}


def test_a_file_that_is_not_utf8_text_is_skipped(tmp_path):
    _write(tmp_path, "note.md", "a note")
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe")
    assert load_corpus(tmp_path) == {"note.md": "a note"}


def test_an_empty_branch_loads_nothing(tmp_path):
    assert load_corpus(tmp_path) == {}


def test_the_order_is_deterministic(tmp_path):
    for name in ("c.txt", "a.txt", "b.txt"):
        _write(tmp_path, name)
    assert list(load_corpus(tmp_path)) == ["a.txt", "b.txt", "c.txt"]
