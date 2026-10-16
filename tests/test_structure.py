"""The map holds together with no model involved.

These tests pin the behaviour the roadmap requires of the structure
step — coverage, determinism, provenance of edges from the graph, no
generation calls, and observable progress. What the regions *ought* to
be is what structure match answers; here we pin that the structure step
is honest, not that it is correct.
"""

import json
import sys
from pathlib import Path

import pytest

from grappoli import graph as _graph
from grappoli.corpus import load_corpus
from grappoli.map import build_map
from grappoli.similarity import build_vectors

NOTES = Path(__file__).parent / "fixtures" / "in-domain" / "notes"
CORPORA = [
    pytest.param(Path(__file__).parent / "fixtures" / "in-domain" / "notes", id="in-domain"),
    pytest.param(Path(__file__).parent / "fixtures" / "heterogeneous" / "notes", id="heterogeneous"),
]


@pytest.fixture(scope="module")
def corpus() -> dict[str, str]:
    return load_corpus(NOTES)


def _names(mapping) -> set[str]:
    members = [m for region in mapping["regions"] for m in region["members"]]
    return set(members) | set(mapping["standalone"])


@pytest.mark.parametrize("notes_dir", CORPORA)
def test_map_covers_corpus_exactly_with_e5(notes_dir):
    """Every note has a home or is flagged standalone, and only once.

    The two figures the map promises are 'which regions are worth
    opening' and 'which notes stand alone'. A note that is neither
    listed nor flagged is invisible; one listed twice is counted twice.
    Both failures make the map a lie before any model gets near it.
    Pinned on both fixture shapes (fixtures/README.md).
    """
    corpus = load_corpus(notes_dir)
    mapping = build_map(corpus, provider="e5")
    assert len(_names(mapping)) == len(corpus) == 14
    region_count = sum(len(r["members"]) for r in mapping["regions"])
    assert region_count + len(mapping["standalone"]) == len(corpus)


@pytest.mark.parametrize("notes_dir", CORPORA)
def test_map_covers_corpus_exactly_with_tfidf(notes_dir):
    """The control provider obeys the same contract.

    TF-IDF is the baseline that embeddings must beat on structure
    match; it cannot beat anything if it is not held to the same rules
    in the first place. Pinned on both fixture shapes.
    """
    corpus = load_corpus(notes_dir)
    mapping = build_map(corpus, provider="tfidf")
    assert len(_names(mapping)) == len(corpus) == 14
    region_count = sum(len(r["members"]) for r in mapping["regions"])
    assert region_count + len(mapping["standalone"]) == len(corpus)


def test_region_rule_is_deterministic(corpus):
    """Same corpus, same map.

    Structure match compares maps against a reference across runs. If
    the structure step were nondeterministic, structure match would be
    measuring the shuffle, and no metric could be trusted from it.
    """
    first = build_map(corpus, provider="e5")
    second = build_map(corpus, provider="e5")
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_edges_are_derived_from_the_graph(corpus):
    """Every stated relation names two regions that actually touch.

    The map's relations are the cross-community edges of the
    neighbourhood graph — product.md: 'stated rather than implied' but
    still *derived*. A relation between two regions with no note-level
    edge between them would be invented, not derived, which is exactly
    what the map step must not do.
    """
    mapping = build_map(corpus, provider="e5")
    names = list(corpus)
    vectors = build_vectors(list(corpus.values()), "e5")
    base_edges = _graph.mutual_edges(vectors, mapping["k"]) if mapping["mutual"] else _graph.knn_edges(vectors, mapping["k"])
    base = {(a, b) for a, b, _ in base_edges}
    index_of = {name: i for i, name in enumerate(names)}

    region_of = {}
    for region in mapping["regions"]:
        for member in region["members"]:
            region_of[index_of[member]] = region["id"]

    for edge in mapping["edges"]:
        left = [n for n, r in region_of.items() if r == edge["source"]]
        right = [n for n, r in region_of.items() if r == edge["target"]]
        assert any(tuple(sorted((a, b))) in base for a in left for b in right), edge


def test_selection_takes_no_generation_calls(corpus):
    """Selection is a computation over the corpus, before any model.

    The spec (product.md, Approach) is explicit: representatives are
    selected without consulting a model. The test pins it at the
    observable boundary — building a map must not pull generation
    machinery into the process at all.
    """
    assert "ollama" not in sys.modules
    mapping = build_map(corpus, provider="e5")
    assert "ollama" not in sys.modules
    for region in mapping["regions"]:
        assert set(region["representatives"]) <= set(region["members"])
        assert len(region["representatives"]) <= 5


def test_progress_is_reported_per_item(corpus):
    """The map step reports where it is, per embedding batch and per cluster.

    Characterisation runs four minutes a region; structure runs fast on
    this fixture but slowly on a real corpus. The user must be able to
    see which item a step is on (architecture.md, Progress and
    logging), so the callback is part of the behaviour, not an option.
    """
    events = []
    build_map(corpus, provider="e5", progress=lambda label, done, total: events.append((label, done, total)))
    embedding = [e for e in events if e[0] == "embed"]
    assert embedding and embedding[-1][1] == embedding[-1][2] == len(corpus)
    clusters = [e for e in events if e[0] == "clusters"]
    assert clusters == [("clusters", 0, 1), ("clusters", 1, 1)]