"""Stage 0: the environment and the fixture corpus hold together.

These are the first tests and the base for everything after: Stage 1
clusters these notes, Stage 4 scores candidate maps against the
reference regions. A failure here means the ground is wrong, not the
pipeline.

The corpus-level pins run on both fixture corpora (`in-domain/` and
`heterogeneous/`, see fixtures/README.md). The two are the same shape
on purpose — 14 notes, four regions of three, two strays — so one
parametrized body pins both grounds instead of two copies of the same
test. What is pinned here is the ground itself, not the code; the
code's own handling of references is pinned in test_benchmark.py, at
the place references are consumed.
"""

import json
import os
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import numpy as np
import pytest

FIXTURES = Path(__file__).parent / "fixtures"
CORPORA = [
    pytest.param(FIXTURES / "in-domain", id="in-domain"),
    pytest.param(FIXTURES / "heterogeneous", id="heterogeneous"),
]
IN_DOMAIN = FIXTURES / "in-domain"


def _notes(corpus_dir: Path) -> dict[str, str]:
    """The corpus notes, keyed by filename, body text only."""
    return {
        path.name: path.read_text()
        for path in sorted((corpus_dir / "notes").glob("*.md"))
    }


def _reference(corpus_dir: Path) -> dict:
    return json.loads((corpus_dir / "reference-regions.json").read_text())


@pytest.fixture(scope="session")
def corpus() -> dict[str, str]:
    return _notes(IN_DOMAIN)


@pytest.fixture(scope="session")
def embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("BAAI/bge-small-en-v1.5")


@pytest.mark.parametrize("corpus_dir", CORPORA)
def test_corpus_has_fourteen_notes(corpus_dir):
    """Fourteen notes: twelve across four intended regions, two strays.

    More notes than that and the fixture becomes a corpus in its own
    right; fewer and the regions are not worth separating. Both shapes
    are built to this count so they differ on one axis only.
    """
    notes = _notes(corpus_dir)
    assert len(notes) == 14
    assert all(text.strip() for text in notes.values()), "every note has body text"


@pytest.mark.parametrize("corpus_dir", CORPORA)
def test_notes_carry_no_headings(corpus_dir):
    """No line begins with '#'. A heading is a region label in disguise —
    the fixture must not plant structure that real corpora cannot supply.
    """
    for name, text in _notes(corpus_dir).items():
        assert not any(line.lstrip().startswith("#") for line in text.splitlines()), name


@pytest.mark.parametrize("corpus_dir", CORPORA)
def test_reference_covers_corpus_exactly(corpus_dir):
    """The reference is total and disjoint: every note in exactly one set.

    Structure match needs a ground truth to score against; if the
    reference omits a note or double-counts one, the metric measures
    the reference's mistakes rather than the map's. Pinned on both
    shapes — a broken ground on either corpus would poison every
    measurement taken on it.
    """
    reference = _reference(corpus_dir)
    listed = [*sum(reference["regions"].values(), []), *reference["standalone"]]
    notes = _notes(corpus_dir)
    assert sorted(listed) == sorted(notes)
    assert len(listed) == len(set(listed)), "no note appears in two sets"


@pytest.mark.parametrize("corpus_dir", CORPORA)
def test_reference_has_the_intended_shape(corpus_dir):
    """Four regions of three notes each, plus two strays.

    This is the design recorded in tests/fixtures/README.md. The map
    can err in both directions — merging regions or absorbing strays —
    which is what structure match is for.
    """
    reference = _reference(corpus_dir)
    assert len(reference["regions"]) == 4
    assert all(len(members) == 3 for members in reference["regions"].values())
    assert len(reference["standalone"]) == 2


def test_bge_small_embeds_every_note(corpus, embedder):
    """bge-small returns vectors of its known dimension for the whole corpus.

    Stage 1 builds its graph on these vectors; a loader failure here
    would surface downstream as a clustering artifact and be blamed on
    the wrong component.
    """
    vectors = embedder.encode(list(corpus.values()), normalize_embeddings=True)
    assert vectors.shape == (len(corpus), 384)


def test_embeddings_are_deterministic_and_distinct(corpus, embedder):
    """Same note, same vector; different notes, different vectors.

    Without determinism the graph is unstable run to run; without
    distinct vectors there is nothing for the graph to separate.
    """
    text = list(corpus.values())
    v1 = embedder.encode(text, normalize_embeddings=True)
    v2 = embedder.encode(text, normalize_embeddings=True)
    np.testing.assert_allclose(v1, v2, atol=1e-6)
    similarities = v1 @ v1.T
    off_diagonal = similarities - np.eye(len(text))
    assert off_diagonal.max() < 1.0, "a note embeds identically to another"