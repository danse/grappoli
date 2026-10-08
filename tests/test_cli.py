"""The `grappoli map` command.

The command has no settings file: defaults live in `build_map`, driven
by the structure benchmark, and per-run flags override them. These
tests pin that the CLI surface reaches the artefact — defaults when
nothing is given, the flags when they are.
"""

import json
from pathlib import Path

import pytest

from grappoli.cli import main
from grappoli.corpus import load_corpus

NOTES = Path(__file__).parent / "fixtures" / "in-domain" / "notes"


@pytest.fixture(scope="module")
def corpus():
    return load_corpus(NOTES)


def test_map_builds_artefact_with_decided_defaults(corpus, tmp_path):
    """A bare `grappoli map` maps with the rule the benchmark decided.

    The defaults are the point: measurement (benchmarks/structure.md)
    re-makes them, and the command exists to apply them. The artefact
    records the rule it used, so which defaults ran is visible in the
    artefact itself.
    """
    out = tmp_path / "map.json"
    rc = main(["map", str(NOTES), "-o", str(out)])
    assert rc == 0
    mapping = json.loads(out.read_text())
    assert mapping["similarity"] == "bge"
    assert mapping["k"] == 5
    assert mapping["mutual"] is True
    assert mapping["resolution"] == 2.0
    assert mapping["weighted"] is True


def test_map_flags_override_defaults(corpus, tmp_path):
    """The flags are the escape hatch for a single run.

    The TF-IDF control exists precisely so a map can be built without
    the encoder; the flags must reach the same knobs the defaults
    occupy, or they are decoration.
    """
    out = tmp_path / "map.json"
    rc = main(["map", str(NOTES), "--similarity", "tfidf", "-k", "2", "--target", "3",
               "-o", str(out)])
    assert rc == 0
    mapping = json.loads(out.read_text())
    assert mapping["similarity"] == "tfidf"
    assert mapping["k"] == 2
    assert all(len(r["representatives"]) <= 3 for r in mapping["regions"])