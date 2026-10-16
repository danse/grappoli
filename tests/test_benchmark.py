"""The structure sweep script: its reference handling and how it scores.

`scripts/benchmark_structure.py` is where a reference map meets the
corpus it is scored against. The check there is the only gate between
a well-formed ground truth and the defaults `build_map` derives from
it, so it is pinned here like any other code behaviour: every shaped
corpus pays this validation when the sweep is run, without a per-corpus
test (fixtures/README.md). The scoring is pinned too, because the sweep
chooses the defaults and `measure` scores the map they build — the two
must read a partition the same way or they report two numbers for one
rule (`benchmarks/structure.md`).
"""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from grappoli.measure import STANDALONE

SCRIPT = Path(__file__).parent.parent / "scripts" / "benchmark_structure.py"


@pytest.fixture(scope="module")
def sweep_script():
    spec = importlib.util.spec_from_file_location("benchmark_structure", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_labels_and_coverage_are_the_contract(sweep_script, tmp_path):
    """A valid reference becomes labels in corpus order, with strays as one set.

    The returned array is what adjusted Rand index scores against; its
    order must follow the corpus's note order or every score is wrong.
    The 'standalone' set is the same label for all its members — the
    reference's shape, mirrored by the map's flat standalone list.
    """
    reference = tmp_path / "ref.json"
    reference.write_text(json.dumps({
        "regions": {"a": ["n1", "n2"], "b": ["n3"]},
        "standalone": ["n4", "n5"],
    }))
    labels = sweep_script._reference_labels(reference, ["n1", "n2", "n3", "n4", "n5"])
    assert list(labels) == ["a", "a", "b", "standalone", "standalone"]


def test_double_listed_note_is_rejected(sweep_script, tmp_path):
    """A note in two regions is a double count, not a decision input."""
    reference = tmp_path / "ref.json"
    reference.write_text(json.dumps({
        "regions": {"a": ["n1", "n2"], "b": ["n2", "n3"]},
        "standalone": [],
    }))
    with pytest.raises(ValueError, match="n2"):
        sweep_script._reference_labels(reference, ["n1", "n2", "n3"])


def test_note_in_region_and_standalone_is_rejected(sweep_script, tmp_path):
    """The two sets must be disjoint; standalone is not a tiebreaker."""
    reference = tmp_path / "ref.json"
    reference.write_text(json.dumps({
        "regions": {"a": ["n1", "n2"]},
        "standalone": ["n2"],
    }))
    with pytest.raises(ValueError, match="n2"):
        sweep_script._reference_labels(reference, ["n1", "n2"])


def test_unknown_note_in_reference_is_rejected(sweep_script, tmp_path):
    """A label for a file the corpus does not hold is a typo, scored silently.

    This is the failure mode a test cannot see coming (the fixture
    would pass it): a reference that names a note that was renamed or
    never written scores like a map of a smaller corpus.
    """
    reference = tmp_path / "ref.json"
    reference.write_text(json.dumps({
        "regions": {"a": ["n1", "typo.md"]},
        "standalone": [],
    }))
    with pytest.raises(ValueError, match="typo.md"):
        sweep_script._reference_labels(reference, ["n1"])


def test_incomplete_reference_is_rejected(sweep_script, tmp_path):
    """A note the reference omits is invisible to structure match."""
    reference = tmp_path / "ref.json"
    reference.write_text(json.dumps({
        "regions": {"a": ["n1"]},
        "standalone": [],
    }))
    with pytest.raises(ValueError, match="n2"):
        sweep_script._reference_labels(reference, ["n1", "n2"])


def test_sweep_drops_edge_less_singletons_like_build_map(sweep_script):
    """A note with no mutual edge is a stray, not a one-note region.

    Louvain hands every node a community, so an isolated note comes back
    as a singleton; `build_map` drops it and reports it standalone. The
    sweep must drop it too, or it scores a partition the map would never
    build — each stray its own region, counting as agreement against a
    reference that folds its own strays. ``c`` has no reciprocal edge
    (its nearest neighbour does not point back), so only ``a``/``b`` are
    a region here.
    """
    vectors = np.array([[1.0, 0.0], [0.9, 0.1], [-1.0, 0.0]])
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)  # unit, as build_vectors returns
    names = ["a.md", "b.md", "c.md"]
    parts, stray = sweep_script._parts_at(vectors, names, 1, True, 1.0, False)
    assert parts == [["a.md", "b.md"]]
    assert stray == ["c.md"]


def test_sweep_labels_read_like_map_labels(sweep_script):
    """The candidate side is labelled by the same rule as a built map.

    Region members take their region id and every stray takes the one
    `STANDALONE` label — the reference's shape — so the two instruments
    score one partition with one number, not two.
    """
    names = ["a.md", "b.md", "c.md"]
    labels = sweep_script._map_labels([["a.md", "b.md"]], ["c.md"], names)
    assert list(labels) == ["0", "0", STANDALONE]