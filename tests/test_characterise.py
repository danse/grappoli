"""Characterising one region at a time: validated, retried, and resumable.

The model is a stub, so these pin the behaviour around generation — the
prompt holds only the representatives, an answer is validated
structurally, a malformed one is retried up to the cap and no further, a
failed region is logged with its cost and skipped, and a completed
region is never regenerated. What the real model gets wrong is captured
separately from live runs (benchmarks/characterisation.md); here every
failure is controlled so the mechanism is what is under test.
"""

import json

import pytest

from grappoli.characterise import (
    MAX_ATTEMPTS,
    SECONDS_PER_REGION,
    CharacterisationFailed,
    InvalidCharacterisation,
    build_prompt,
    characterise_region,
    characterise_regions,
    read_characterisations,
    validate,
)
from grappoli.model import ModelError

VALID = {"about": "salt and brine", "topics": ["salt", "brine"], "key_claims": ["salt preserves"]}


class StubLLM:
    """Returns canned answers in order; an Exception is raised instead."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []

    def __call__(self, prompt, schema):
        self.calls.append(prompt)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


class Clock:
    """Monotonic-ish clock advancing a fixed step per reading."""

    def __init__(self, step=10.0):
        self.step = step
        self.now = 0.0

    def __call__(self):
        self.now += self.step
        return self.now


def mapping_of(*ids):
    return {
        "regions": [
            {"id": i, "members": [f"n{i}"], "representatives": [f"n{i}"]}
            for i in ids
        ]
    }


NOTES = {"n0": "alpha body", "n1": "bravo body", "n2": "charlie body"}


# --- validation -----------------------------------------------------------

def test_valid_characterisation_passes_through():
    assert validate(VALID) == {
        "about": "salt and brine", "topics": ["salt", "brine"], "key_claims": ["salt preserves"],
    }


def test_six_topics_are_accepted():
    """No count bound: the prompt asks 3-5, but a retry costs four minutes.

    The decision (architecture.md, Model interface) is structural
    validation only; bounding the list would spend a whole generation to
    reject an answer that is not wrong.
    """
    six = {**VALID, "topics": ["a", "b", "c", "d", "e", "f"]}
    assert validate(six)["topics"] == ["a", "b", "c", "d", "e", "f"]


@pytest.mark.parametrize("candidate", [
    "not a dict",
    {"topics": ["a"], "key_claims": ["b"]},
    {"about": "  ", "topics": ["a"], "key_claims": ["b"]},
    {"about": "a", "topics": [], "key_claims": ["b"]},
    {"about": "a", "topics": ["a"], "key_claims": []},
    {"about": "a", "topics": ["a", " "], "key_claims": ["b"]},
    {"about": "a", "topics": [1], "key_claims": ["b"]},
    {"about": "a", "topics": ["a"], "key_claims": "b"},
])
def test_malformed_shapes_are_rejected(candidate):
    with pytest.raises(InvalidCharacterisation):
        validate(candidate)


# --- one region -----------------------------------------------------------

def test_prompt_carries_only_the_representatives():
    """The region is characterised from five notes, never the corpus."""
    prompt = build_prompt(["n1"], NOTES)
    assert "bravo body" in prompt
    assert "alpha body" not in prompt
    assert "charlie body" not in prompt


def test_region_is_retried_up_to_the_cap_then_fails():
    """Three attempts total (architecture.md, Model interface): 1 plus 2 retries, no further."""
    llm = StubLLM(ModelError("bad"), ModelError("bad"), ModelError("bad"))
    with pytest.raises(CharacterisationFailed) as caught:
        characterise_region(0, ["n0"], NOTES, llm)
    assert caught.value.attempts == MAX_ATTEMPTS == 3
    assert len(llm.calls) == MAX_ATTEMPTS


def test_region_recovers_when_a_retry_succeeds():
    """A second answer that validates is the characterisation."""
    llm = StubLLM(ModelError("bad"), VALID)
    assert characterise_region(0, ["n0"], NOTES, llm) == VALID
    assert len(llm.calls) == 2


def test_only_malformed_answers_are_retried():
    """A non-ModelError is a bug in our code, not the model; it propagates.

    Swallowing an unexpected exception as a retry would spend three
    generations hiding a traceback.
    """
    llm = StubLLM(RuntimeError("boom"))
    with pytest.raises(RuntimeError):
        characterise_region(0, ["n0"], NOTES, llm)
    assert len(llm.calls) == 1


# --- the run --------------------------------------------------------------

def test_each_region_is_appended_as_a_line(tmp_path):
    path = tmp_path / "characterisations"
    llm = StubLLM(VALID, VALID)
    failed = characterise_regions(mapping_of(0, 1), NOTES, path, llm)
    assert failed == []
    lines = path.read_text().splitlines()
    assert [json.loads(line)["region"] for line in lines] == [0, 1]
    assert json.loads(lines[0]) == {"region": 0, **VALID}


def test_completed_regions_are_not_regenerated(tmp_path):
    """An interrupted run resumes; a finished region is never re-sent.

    The line file is the resume state (architecture.md). Re-calling the
    model for region 0 would cost four minutes to overwrite a line that
    is already right.
    """
    path = tmp_path / "characterisations"
    characterise_regions(mapping_of(0), NOTES, path, StubLLM(VALID))
    second = StubLLM(VALID)
    characterise_regions(mapping_of(0, 1), NOTES, path, second)
    assert len(second.calls) == 1, "only region 1 should reach the model"
    assert [json.loads(l)["region"] for l in path.read_text().splitlines()] == [0, 1]


def test_existing_lines_are_left_byte_for_byte(tmp_path):
    """Append-only means exactly that; a rerun must not rewrite history."""
    path = tmp_path / "characterisations"
    path.write_text('{"region": 0, "about": "old", "topics": ["x"], "key_claims": ["y"]}\n')
    characterise_regions(mapping_of(0, 1), NOTES, path, StubLLM(VALID))
    first = path.read_text().splitlines()[0]
    assert json.loads(first)["about"] == "old"


def test_a_failed_region_is_skipped_and_the_run_continues(tmp_path):
    """Exhaustion logs, skips, continues; later regions still land."""
    path = tmp_path / "characterisations"
    logs = []
    llm = StubLLM(ModelError("x"), ModelError("x"), ModelError("x"), VALID)
    failed = characterise_regions(mapping_of(0, 1), NOTES, path, llm,
                                  clock=Clock(), log=logs.append)
    assert failed == [0]
    assert [json.loads(l)["region"] for l in path.read_text().splitlines()] == [1]
    assert any("gave up after 3 attempts (10s)" in line for line in logs)


def test_failed_regions_are_the_only_ones_retried_next_run(tmp_path):
    """The resume state is the file, so a failure is exactly the gap.

    Region 1 exhausts its attempts while region 0 lands, so the file
    holds 0 and not 1. The next run re-sends only 1 — not 0, which is
    already right.
    """
    path = tmp_path / "characterisations"
    first = StubLLM(VALID, ModelError("x"), ModelError("x"), ModelError("x"))
    assert characterise_regions(mapping_of(0, 1), NOTES, path, first) == [1]
    second = StubLLM(VALID)
    assert characterise_regions(mapping_of(0, 1), NOTES, path, second) == []
    assert len(second.calls) == 1, "only region 1 should be retried"
    assert [json.loads(l)["region"] for l in path.read_text().splitlines()] == [0, 1]


def test_progress_is_reported_per_region_with_an_eta(tmp_path):
    """Region 3 of 16, with the estimate falling as regions finish.

    The figure is the shipped model's cost for one region, so the first
    estimate is the regions left times that figure; the run's own
    measurements replace it as regions finish.
    """
    path = tmp_path / "characterisations"
    events = []
    characterise_regions(mapping_of(0, 1, 2), NOTES, path, StubLLM(VALID, VALID, VALID),
                         clock=Clock(step=30.0),
                         progress=lambda *event: events.append(event))
    assert [(e[1], e[2]) for e in events] == [(1, 3), (2, 3), (3, 3)]
    assert all(e[0] == "region" for e in events)
    etas = [e[3] for e in events]
    assert etas[0] == pytest.approx(3 * SECONDS_PER_REGION)
    assert etas[0] > etas[-1] >= 0


def test_read_characterisations_ignores_blank_lines(tmp_path):
    path = tmp_path / "characterisations"
    path.write_text(json.dumps({"region": 0, **VALID}) + "\n\n")
    assert set(read_characterisations(path)) == {0}


def test_a_line_torn_by_an_interrupt_is_regenerated(tmp_path):
    """A half-written last line is skipped, so its region is re-done.

    The file is flushed per line but not written atomically; a hard kill
    can leave a partial line. Treating it as done would silently drop a
    characterisation, so the region it held must read as missing.
    """
    path = tmp_path / "characterisations"
    good = json.dumps({"region": 0, **VALID}) + "\n"
    path.write_text(good + '{"region": 1, "about": "tru')
    done = read_characterisations(path)
    assert set(done) == {0}

    llm = StubLLM(VALID)
    assert characterise_regions(mapping_of(0, 1), NOTES, path, llm) == []
    assert len(llm.calls) == 1, "only the torn region should be regenerated"
    # The fragment was dropped, not glued to the new record: every line
    # now parses as one region.
    assert [json.loads(l)["region"] for l in path.read_text().splitlines()] == [0, 1]
