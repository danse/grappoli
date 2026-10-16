"""The four measurements, each pinned on a corpus whose answer is known.

A metric that cannot fail on a bad input is not measuring, so each one
here is given a case where the right answer is known and, beside it, an
input built to be wrong — a map that leaves the corpus homeless, one
whose regions are unrelated to the reference, a deliberately redundant
map, and a characterisation the notes do not support. The model-backed
measures take their model as an argument, so the real cross-encoder and
the real judge are exercised only in live runs
(`benchmarks/measurement.md`); what is pinned here is the rule, on
stubs, the same way characterisation and the relation loop are.
"""

import json
import shutil
from pathlib import Path

import pytest

from grappoli.cli import main
from grappoli.measure import (
    MAX_JUDGE_ATTEMPTS,
    UNMAPPED,
    characterisation_text,
    comprehensiveness,
    faithfulness,
    judge_claim,
    map_labels,
    measure,
    redundancy,
    reference_labels,
    region_evidence,
    structure_match,
    validate_verdict,
)
from grappoli.model import ModelError

NOTES = Path(__file__).parent / "fixtures" / "in-domain" / "notes"
REFERENCE = Path(__file__).parent / "fixtures" / "in-domain" / "reference-regions.json"


def _map(regions: list[list[str]], standalone: list[str]) -> dict:
    return {
        "notes": sum(len(members) for members in regions) + len(standalone),
        "regions": [
            {"id": i, "members": members, "representatives": members[:1]}
            for i, members in enumerate(regions)
        ],
        "standalone": list(standalone),
        "edges": [],
    }


def _characterisation(about: str) -> dict:
    return {"about": about, "topics": [about], "key_claims": [f"claim about {about}"]}


class Judge:
    """A judge that answers from a script; an Exception is raised instead."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.prompts = []

    def __call__(self, prompt, schema):
        self.prompts.append(prompt)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


VERDICT = {"supported": True, "reason": "the notes say it"}


# --- comprehensiveness ----------------------------------------------------


def test_comprehensiveness_is_the_share_with_a_home():
    """A region is a home; a standalone note is accounted for but not homed.

    The map states 'which notes stand alone' as one of its two figures,
    so a stray is placed, not missed. Counting it as covered would make
    the metric 1.0 for every map that places every note, which is every
    map; the corpus with two strays is where the known answer lives.
    """
    notes = {"a.md": "salt", "b.md": "brine", "c.md": "alone"}
    mapping = _map([["a.md", "b.md"]], ["c.md"])
    assert comprehensiveness(mapping, notes) == pytest.approx(2 / 3)


def test_comprehensiveness_denominator_is_the_corpus_measured():
    """A map scored against a changed branch is not flattered by ghosts.

    A member the corpus no longer holds cannot be a home for anything,
    and a note the map never saw still counts against coverage. The
    denominator is the corpus, not the count the map recorded.
    """
    notes = {"a.md": "salt", "b.md": "alone"}
    mapping = _map([["a.md", "ghost.md"]], ["b.md"])
    assert comprehensiveness(mapping, notes) == pytest.approx(1 / 2)


def test_comprehensiveness_is_one_when_nothing_stands_alone():
    notes = {"a.md": "x", "b.md": "y"}
    assert comprehensiveness(_map([["a.md", "b.md"]], []), notes) == pytest.approx(1.0)


# --- structure match ------------------------------------------------------


def test_structure_match_is_one_against_its_own_partition(tmp_path):
    """A map that partitions the corpus as the reference does scores 1.

    Region ids and reference names are different label spaces; adjusted
    Rand index is invariant to relabelling, which is what lets a rebuilt
    map be scored against a fixed reference however its regions are
    numbered.
    """
    notes = {"a.md": "x", "b.md": "y", "c.md": "z", "d.md": "w"}
    mapping = _map([["a.md", "b.md"], ["c.md"]], ["d.md"])
    reference = tmp_path / "ref.json"
    reference.write_text(json.dumps({
        "regions": {"one": ["a.md", "b.md"], "two": ["c.md"]},
        "standalone": ["d.md"],
    }))
    assert structure_match(mapping, notes, reference) == pytest.approx(1.0)


def test_structure_match_separates_a_map_unrelated_to_the_reference(tmp_path):
    """Merging a region and absorbing a stray scores worse than chance.

    The map puts a and b together and c alone; the reference puts a and
    c together and b alone. Every pair but (b, c) disagrees, and the
    known answer is -0.5 — well below the 0 of a chance map, so the
    metric demonstrably fails a bad map rather than merely rising.
    """
    notes = {"a.md": "x", "b.md": "y", "c.md": "z"}
    mapping = _map([["a.md", "b.md"]], ["c.md"])
    reference = tmp_path / "ref.json"
    reference.write_text(json.dumps({
        "regions": {"one": ["a.md", "c.md"]},
        "standalone": ["b.md"],
    }))
    assert structure_match(mapping, notes, reference) == pytest.approx(-0.5)


def test_structure_match_scores_only_the_finest_partition(tmp_path):
    """A level added above the regions cannot move the score.

    This is why `architecture.md` settles the map flat on something other
    than structure match: adjusted Rand index compares two flat
    partitions, so a map's own hierarchy — a grouping of its regions —
    is invisible to it. If a future change makes the score hierarchy-aware,
    this test is the decision it has to overturn, not a bug.
    """
    notes = {"a.md": "x", "b.md": "y", "c.md": "z", "d.md": "w"}
    mapping = _map([["a.md", "b.md"], ["c.md"]], ["d.md"])
    nested = dict(mapping, groups=[{"id": 0, "members": [0, 1]}])
    reference = tmp_path / "ref.json"
    reference.write_text(json.dumps({
        "regions": {"one": ["a.md", "b.md"], "two": ["c.md"]},
        "standalone": ["d.md"],
    }))
    assert structure_match(nested, notes, reference) == structure_match(mapping, notes, reference)


def test_map_labels_mark_a_note_the_map_never_places(tmp_path):
    """An unplaced note is not the same as one deliberately left alone.

    The two label spaces name standalone separately; a candidate map
    that drops a note must not be scored as if it had homed it as a
    stray, or the score would flatter a map that is missing notes.
    """
    names = ["a.md", "b.md"]
    assert list(map_labels(_map([["a.md"]], []), names)) == ["0", UNMAPPED]


def test_structure_match_rejects_a_reference_that_misses_a_note(tmp_path):
    """The shared check gates both the score and the sweep."""
    reference = tmp_path / "ref.json"
    reference.write_text(json.dumps({"regions": {"one": ["a.md"]}, "standalone": []}))
    with pytest.raises(ValueError, match="b.md"):
        structure_match(_map([["a.md"], ["b.md"]], []), {"a.md": "x", "b.md": "y"}, reference)


def test_reference_labels_follow_corpus_order():
    """Labels must be in corpus order or every score is wrong."""
    reference = json.loads(REFERENCE.read_text())
    labels = reference_labels(REFERENCE, list(reference["standalone"]) + [
        note for members in reference["regions"].values() for note in members
    ])
    assert len(labels) == 14
    assert labels[0] == "standalone" and labels[1] == "standalone"


# --- redundancy -----------------------------------------------------------


def test_redundancy_is_zero_when_every_characterisation_differs():
    """Four regions saying four things is 0, the healthy answer."""
    characterisations = {i: _characterisation(f"region {i}") for i in range(4)}
    compare = lambda left, right: 1.0 if left == right else -1.0
    assert redundancy(characterisations, compare) == pytest.approx(0.0)


def test_redundancy_counts_a_repeated_characterisation():
    """A deliberately redundant map: three regions, two saying one thing.

    One pair repeats, so there are two groups and one region of the
    three is a repeat: 1/3. The metric moves off 0 exactly on the input
    it exists to catch.
    """
    characterisations = {
        0: _characterisation("same"),
        1: _characterisation("same"),
        2: _characterisation("other"),
    }
    compare = lambda left, right: 1.0 if left == right else -1.0
    assert redundancy(characterisations, compare) == pytest.approx(1 / 3)


def test_redundancy_groups_a_chain_of_repeats():
    """If a says what b says and b what c says, the map says one thing.

    Pairwise judgement is not transitive, so a chain must still collapse
    to one group; otherwise a long paraphrase drift would read as new
    content.
    """
    characterisations = {0: _characterisation("x"), 1: _characterisation("y"),
                         2: _characterisation("z")}
    texts = [characterisation_text(characterisations[i]) for i in range(3)]
    chain = {(texts[0], texts[1]), (texts[1], texts[2])}
    compare = lambda left, right: 1.0 if (left, right) in chain or (right, left) in chain else -1.0
    assert redundancy(characterisations, compare) == pytest.approx(2 / 3)


def test_redundancy_of_a_single_region_is_zero():
    """Nothing to repeat, and no model touched to find that out."""
    called = []

    def compare(left, right):
        called.append((left, right))
        return 1.0

    assert redundancy({0: _characterisation("only")}, compare) == 0.0
    assert called == []


# --- faithfulness ---------------------------------------------------------


def test_validate_verdict_reads_the_words_a_small_model_uses():
    assert validate_verdict({"supported": "yes", "reason": "r"})["supported"] is True
    assert validate_verdict({"supported": "No", "reason": "r"})["supported"] is False
    assert validate_verdict({"supported": True}) == {"supported": True, "reason": ""}


def test_validate_verdict_rejects_a_non_verdict():
    from grappoli.measure import InvalidVerdict

    with pytest.raises(InvalidVerdict):
        validate_verdict({"supported": "maybe", "reason": "r"})
    with pytest.raises(InvalidVerdict):
        validate_verdict("supported")


def test_faithfulness_is_the_share_of_claims_the_notes_support():
    """A deliberately unfaithful characterisation drags the number down.

    Two claims, one the judge supports and one it does not: the score is
    the share, not a whole-region pass, so an invented claim is visible
    in the number.
    """
    mapping = _map([["a.md", "b.md"]], [])
    notes = {"a.md": "salt preserves", "b.md": "brine ratios"}
    characterisations = {0: {"about": "x", "topics": ["t"],
                             "key_claims": ["salt preserves", "the jar is blue"]}}
    judge = Judge([{"supported": True, "reason": "stated"},
                   {"supported": False, "reason": "not in the notes"}])
    result = faithfulness(mapping, characterisations, notes, llm=judge)
    assert result["score"] == pytest.approx(0.5)
    assert (result["supported"], result["unsupported"]) == (1, 1)
    assert result["verdicts"][1]["supported"] is False


def test_faithfulness_checks_a_claim_against_all_the_regions_members():
    """The evidence is the region, not just the representatives it was written from.

    The claim is about the region, so every member is evidence; a claim
    true of a member the model never read is still faithful to the map.
    """
    mapping = _map([["a.md", "b.md"]], [])
    notes = {"a.md": "REPRESENTATIVE TEXT", "b.md": "MEMBER TEXT"}
    characterisations = {0: _characterisation("x")}
    judge = Judge([dict(VERDICT)])
    faithfulness(mapping, characterisations, notes, llm=judge)
    assert "REPRESENTATIVE TEXT" in judge.prompts[0]
    assert "MEMBER TEXT" in judge.prompts[0]


def test_judge_retries_a_malformed_answer_and_logs_it():
    """A malformed verdict is a retry, exactly as a malformed region is.

    Only a malformed answer counts against the cap; the first is thrown
    away and the second read, and the rejection is on the record.
    """
    log = []
    judge = Judge([ModelError("no JSON"), dict(VERDICT)])
    verdict = judge_claim("a claim", "the notes", llm=judge, log=log.append)
    assert verdict["supported"] is True
    assert any("rejected" in line for line in log)


def test_faithfulness_records_an_unanswered_claim_undecided():
    """A judge that never answers cannot move the number it reports.

    Every attempt fails, so the claim is undecided and out of the score;
    with no judged claim the score is None rather than 0, which would
    read as a map that contradicts its notes.
    """
    mapping = _map([["a.md"]], [])
    characterisations = {0: _characterisation("x")}
    judge = Judge([ModelError("no")] * MAX_JUDGE_ATTEMPTS)
    result = faithfulness(mapping, characterisations, {"a.md": "text"}, llm=judge)
    assert result["score"] is None
    assert result["undecided"] == 1
    assert result["verdicts"][0]["supported"] is None


def test_region_evidence_joins_the_members_in_map_order():
    region = {"id": 0, "members": ["b.md", "a.md"], "representatives": ["b.md"]}
    assert region_evidence(region, {"a.md": "A", "b.md": "B"}) == "B\n\nA"


# --- the whole measurement ------------------------------------------------


def test_measure_produces_all_four_numbers(tmp_path):
    """The answered-when of the measurements: four numbers for a candidate map.

    On demand means one call, so `measure` assembles them; structure
    match alone needs the reference, and faithfulness is read beside the
    verdicts it is made of.
    """
    notes = {"a.md": "x", "b.md": "y", "c.md": "z"}
    mapping = _map([["a.md", "b.md"]], ["c.md"])
    reference = tmp_path / "ref.json"
    reference.write_text(json.dumps({
        "regions": {"one": ["a.md", "b.md"]}, "standalone": ["c.md"],
    }))
    characterisations = {0: _characterisation("x"), 1: _characterisation("y")}
    judge = Judge([dict(VERDICT)] * 2)
    compare = lambda left, right: -1.0

    result = measure(mapping, characterisations, notes, reference,
                     llm=judge, compare=compare)
    assert result["comprehensiveness"] == pytest.approx(2 / 3)
    assert result["redundancy"] == pytest.approx(0.0)
    assert result["faithfulness"] == pytest.approx(1.0)
    assert result["structure_match"] == pytest.approx(1.0)


def test_measure_cannot_weigh_a_map_without_characterisations(tmp_path):
    """The selection-only arm changes only the prose, not any number.

    `roadmap.md` asked whether characterisation is worth its cost by
    "selection-only output against the full map": this is that arm, the
    same map with no characterisations. Comprehensiveness and structure
    match are properties of the map and are unchanged; redundancy is 0
    for want of anything to compare, faithfulness None for want of a
    claim. No number moves the way the question needs, which is why it is
    settled on the product premise, not by a measurement
    (`architecture.md`, Measurements). The no-model stubs pin that the
    arm touches neither the cross-encoder nor the judge.
    """
    notes = {"a.md": "x", "b.md": "y", "c.md": "z"}
    mapping = _map([["a.md", "b.md"]], ["c.md"])
    reference = tmp_path / "ref.json"
    reference.write_text(json.dumps({
        "regions": {"one": ["a.md", "b.md"]}, "standalone": ["c.md"],
    }))

    def no_model(*args, **kwargs):
        raise AssertionError("the selection-only arm consults no model")

    result = measure(mapping, {}, notes, reference, llm=no_model, compare=no_model)
    assert result["comprehensiveness"] == pytest.approx(2 / 3)
    assert result["structure_match"] == pytest.approx(1.0)
    assert result["redundancy"] == 0.0
    assert result["faithfulness"] is None


def test_measure_without_a_reference_reports_no_structure_match():
    """Nothing else reproduces structure match, so it is absent, not zero."""
    notes = {"a.md": "x"}
    mapping = _map([["a.md"]], [])
    result = measure(mapping, {0: _characterisation("x")}, notes,
                     llm=Judge([dict(VERDICT)]), compare=lambda left, right: 0.0)
    assert result["structure_match"] is None
    assert result["reference"] is None


# --- the command ----------------------------------------------------------


@pytest.fixture
def branch(tmp_path):
    """A private copy of the fixture with a built map and characterisations.

    Built by hand rather than by `read`, so the command under test is
    `measure`; the map is the reference itself, which makes structure
    match 1.0 and the other numbers known.
    """
    target = tmp_path / "notes"
    shutil.copytree(NOTES, target)
    reference = json.loads(REFERENCE.read_text())
    work = target / ".grappoli"
    work.mkdir()
    mapping = {
        "notes": 14,
        "regions": [
            {"id": i, "members": members, "representatives": members[:1]}
            for i, members in enumerate(reference["regions"].values())
        ],
        "standalone": reference["standalone"],
        "edges": [],
    }
    (work / "map.json").write_text(json.dumps(mapping))
    lines = [
        json.dumps({"region": region["id"], **_characterisation(f"region {region['id']}")})
        for region in mapping["regions"]
    ]
    (work / "characterisations").write_text("\n".join(lines) + "\n")
    return target


def _nonrepeating(left, right):
    return -1.0


def test_measure_command_reports_the_four_numbers(branch, capsys):
    rc = main(["measure", str(branch), "--reference", str(REFERENCE)],
              llm=Judge([dict(VERDICT)] * 8), compare=_nonrepeating)
    assert rc == 0
    out = capsys.readouterr().out
    assert "comprehensiveness: 0.857" in out
    assert "redundancy: 0.000" in out
    assert "faithfulness: 1.000" in out
    assert "structure match: 1.000" in out


def test_measure_command_without_a_reference_says_so(branch, capsys):
    main(["measure", str(branch)], llm=Judge([dict(VERDICT)] * 8), compare=_nonrepeating)
    assert "structure match: n/a (no reference given)" in capsys.readouterr().out


def test_measure_command_needs_a_map(tmp_path, capsys):
    """Measuring nothing is an error, not four zeroes."""
    target = tmp_path / "notes"
    shutil.copytree(NOTES, target)
    rc = main(["measure", str(target)], llm=Judge([]), compare=_nonrepeating)
    assert rc == 1
    assert "no map" in capsys.readouterr().err


def test_measure_command_reports_a_broken_reference(branch, tmp_path, capsys):
    """A reference that misses a note is refused with a message, not a traceback.

    Structure match is only as good as its ground; a reference that
    cannot be scored is a user error the command reports, the same way
    `read` reports a region it could not characterise.
    """
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps({"regions": {"one": ["salt-brine-basics.md"]},
                                  "standalone": []}))
    rc = main(["measure", str(branch), "--reference", str(broken)],
              llm=Judge([dict(VERDICT)] * 8), compare=_nonrepeating)
    assert rc == 1
    assert "reference has no label for" in capsys.readouterr().err
