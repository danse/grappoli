"""Stage 0: the environment and the fixture corpus hold together.

These are the first tests and the base for everything after: Stage 1
clusters these notes, Stage 4 scores candidate maps against the
reference regions. A failure here means the ground is wrong, not the
pipeline.
"""

import json
import os
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import numpy as np
import pytest

NOTES_DIR = Path(__file__).parent / "fixtures" / "notes"
REFERENCE = Path(__file__).parent / "fixtures" / "reference-regions.json"


@pytest.fixture(scope="session")
def corpus() -> dict[str, str]:
    """The fixture notes, keyed by filename, body text only."""
    return {
        path.name: path.read_text()
        for path in sorted(NOTES_DIR.glob("*.md"))
    }


@pytest.fixture(scope="session")
def reference() -> dict:
    return json.loads(REFERENCE.read_text())


@pytest.fixture(scope="session")
def embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("BAAI/bge-small-en-v1.5")


def test_corpus_has_fourteen_notes(corpus):
    """Fourteen notes: twelve across four intended regions, two strays.

    More notes than that and the fixture becomes a corpus in its own
    right; fewer and the regions are not worth separating.
    """
    assert len(corpus) == 14
    assert all(text.strip() for text in corpus.values()), "every note has body text"


def test_notes_carry_no_headings(corpus):
    """No line begins with '#'. A heading is a region label in disguise —
    the fixture must not plant structure that real corpora cannot supply.
    """
    for name, text in corpus.items():
        assert not any(line.lstrip().startswith("#") for line in text.splitlines()), name


def test_reference_covers_corpus_exactly(corpus, reference):
    """The reference is total and disjoint: every note in exactly one set.

    Structure match needs a ground truth to score against; if the
    reference omits a note or double-counts one, the metric measures
    the reference's mistakes rather than the map's.
    """
    listed = [*sum(reference["regions"].values(), []), *reference["standalone"]]
    assert sorted(listed) == sorted(corpus)
    assert len(listed) == len(set(listed)), "no note appears in two sets"


def test_reference_has_the_intended_shape(reference):
    """Four regions of three notes each, plus two strays.

    This is the design recorded in tests/fixtures/README.md. The map
    can err in both directions — merging regions or absorbing strays —
    which is what structure match is for.
    """
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