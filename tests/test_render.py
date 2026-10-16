"""The page `grappoli show` prints.

`render` is the last arrow of the pipeline and has no model behind it, so
what is pinned here is the contract rather than any behaviour of a model:
the page is a function of the three working files, every region and every
standalone note appear, each stored relation appears once however its pair
is keyed, the model's words are carried verbatim, and a build missing a
characterisation or a relation reads as partial instead of being filled
in. The command is exercised on a branch built by hand, the way `measure`'s
is, so that what is under test is `show`.
"""

import json

import pytest

from grappoli.cli import main
from grappoli.render import render


def _region(region_id, members, representatives=None):
    return {
        "id": region_id,
        "members": list(members),
        "representatives": list(members if representatives is None else representatives),
    }


def _characterisation(about="a region", topics=("t",), claims=("c",)):
    return {"about": about, "topics": list(topics), "key_claims": list(claims)}


def _map(regions, edges=(), standalone=()):
    return {
        "similarity": "bge",
        "k": 5,
        "mutual": True,
        "resolution": 2.0,
        "weighted": True,
        "notes": sum(len(region["members"]) for region in regions) + len(standalone),
        "regions": list(regions),
        "edges": list(edges),
        "standalone": list(standalone),
    }


# --- the content contract --------------------------------------------------


def test_the_page_is_a_function_of_the_three_inputs():
    """Same three inputs, same page; each one alone changes it.

    The page is the corpus's rather than the model's because nothing but
    the map, the characterisations and the relations goes in — not a
    clock, not a file, not a call (`architecture.md`, The document).
    """
    mapping = _map([_region(0, ["a.md"])])
    characterisations = {0: _characterisation("about zero")}
    relations = {}
    page = render(mapping, characterisations, relations)
    assert render(mapping, characterisations, relations) == page
    assert render(_map([_region(0, ["a.md"]), _region(1, ["b.md"])]),
                  characterisations, relations) != page
    assert render(mapping, {0: _characterisation("different")}, relations) != page
    assert render(mapping, {0: _characterisation("about zero")},
                  {(0, 1): {"source": 0, "target": 1, "statement": "s"}}) != page


def test_every_region_appears_exactly_once():
    mapping = _map([_region(0, ["a.md"]), _region(1, ["b.md"]), _region(2, ["c.md"])])
    page = render(mapping, {}, {})
    for region in mapping["regions"]:
        assert page.count(f"Region {region['id']}") == 1


def test_each_stored_relation_appears_once_however_its_pair_is_keyed():
    mapping = _map(
        [_region(0, ["a.md"]), _region(1, ["b.md"])],
        edges=[{"source": 1, "target": 0, "weight": 1}],
    )
    characterisations = {0: _characterisation(), 1: _characterisation()}
    low = {(0, 1): {"source": 0, "target": 1, "statement": "they touch"}}
    high = {(1, 0): {"source": 0, "target": 1, "statement": "they touch"}}
    for relations in (low, high):
        page = render(mapping, characterisations, relations)
        assert page.count("0 ↔ 1") == 1
        assert "they touch" in page


def test_relation_statements_are_verbatim():
    statement = "Both name brine — pH, not strength."
    mapping = _map([_region(0, ["a.md"]), _region(1, ["b.md"])],
                   edges=[{"source": 0, "target": 1, "weight": 1}])
    characterisations = {0: _characterisation(), 1: _characterisation()}
    page = render(mapping, characterisations,
                  {(0, 1): {"source": 0, "target": 1, "statement": statement}})
    assert statement in page


def test_the_characterisation_is_carried_verbatim():
    about = "Preserves vegetables by salt and acid."
    topics = ["pickling", "brine"]
    claims = ["Brine strength is a matter of taste.", "Salt pulls water out of cells."]
    mapping = _map([_region(0, ["a.md"])])
    page = render(mapping, {0: _characterisation(about, topics, claims)}, {})
    assert about in page
    for topic in topics:
        assert topic in page
    for claim in claims:
        assert claim in page


def test_every_standalone_note_appears():
    mapping = _map([_region(0, ["a.md"])], standalone=["x.md", "y.md"])
    page = render(mapping, {}, {})
    assert "Standalone" in page
    assert "  - x.md" in page
    assert "  - y.md" in page


def test_the_regions_come_before_the_relations_before_the_standalone():
    mapping = _map([_region(0, ["a.md"]), _region(1, ["b.md"])],
                   edges=[{"source": 0, "target": 1, "weight": 1}],
                   standalone=["x.md"])
    characterisations = {0: _characterisation(), 1: _characterisation()}
    page = render(mapping, characterisations, {})
    assert page.index("Region 0") < page.index("Relations") < page.index("Standalone")


def test_the_page_says_which_rule_produced_the_map():
    page = render(_map([_region(0, ["a.md"])]), {}, {})
    assert "rule: bge, k=5, mutual=true, weighted=true, resolution=2.0" in page


def test_the_header_counts_the_corpus():
    mapping = _map([_region(0, ["a.md", "b.md"]), _region(1, ["c.md"])],
                   standalone=["x.md"])
    assert render(mapping, {}, {}).splitlines()[0] == \
        "grappoli — 4 notes, 2 regions, 1 standalone"


def test_representatives_are_named_only_when_they_are_a_subset():
    full = _map([_region(0, ["a.md", "b.md"], representatives=["a.md", "b.md"])])
    subset = _map([_region(0, ["a.md", "b.md"], representatives=["a.md"])])
    assert "representatives" not in render(full, {}, {})
    assert "representatives: a.md" in render(subset, {}, {})


# --- what a partial build reads like ---------------------------------------


def test_a_region_without_a_characterisation_reads_as_a_gap():
    mapping = _map([_region(0, ["a.md"]), _region(1, ["b.md"])])
    page = render(mapping, {0: _characterisation("about zero")}, {})
    assert "Region 1" in page
    assert "no characterisation" in page
    assert "about zero" in page


def test_a_touching_pair_without_a_relation_reads_as_a_gap():
    mapping = _map([_region(0, ["a.md"]), _region(1, ["b.md"])],
                   edges=[{"source": 0, "target": 1, "weight": 1}])
    characterisations = {0: _characterisation(), 1: _characterisation()}
    page = render(mapping, characterisations, {})
    assert "0 ↔ 1" in page
    assert "no relation recorded" in page


# --- the command -----------------------------------------------------------


@pytest.fixture
def branch(tmp_path):
    """A branch holding the three working files and nothing else.

    `show` reads the working files and no note, so the notes need not
    exist for the command to run.
    """
    target = tmp_path / "notes"
    work = target / ".grappoli"
    work.mkdir(parents=True)
    mapping = _map(
        [_region(0, ["a.md"]), _region(1, ["b.md"])],
        edges=[{"source": 0, "target": 1, "weight": 1}],
        standalone=["x.md"],
    )
    (work / "map.json").write_text(json.dumps(mapping))
    (work / "characterisations").write_text(
        json.dumps({"region": 0, **_characterisation("about zero")}) + "\n")
    (work / "relations").write_text(
        json.dumps({"source": 0, "target": 1, "statement": "they touch"}) + "\n")
    return target


def test_show_prints_the_page(branch, capsys):
    rc = main(["show", str(branch)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Region 0" in out
    assert "Region 1" in out
    assert "0 ↔ 1 — they touch" in out
    assert "  - x.md" in out


def test_show_makes_no_model_call(branch, capsys):
    def boom(*args, **kwargs):
        raise AssertionError("show must not call a model")

    assert main(["show", str(branch)], llm=boom, agent_llm=boom) == 0


def test_show_writes_nothing_into_the_branch(branch, capsys):
    def snapshot():
        return {path.name: path.read_bytes() for path in (branch / ".grappoli").iterdir()}

    before = snapshot()
    main(["show", str(branch)])
    assert snapshot() == before


def test_show_needs_a_map(tmp_path, capsys):
    rc = main(["show", str(tmp_path / "notes")])
    assert rc == 1
    assert "no map" in capsys.readouterr().err
