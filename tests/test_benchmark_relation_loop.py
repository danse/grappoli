"""The pair loop's record: what it wrote, and what the judge said.

`scripts/benchmark_relation_loop.py` runs the relation loop over every
touching pair of a map and judges each statement against the notes of the
two regions it names. The model call and the map are substituted, so no
Ollama and no encoder: what is pinned is which pairs are asked, what the
record says about them, and that the evidence the judge reads is the two
regions' notes rather than one region's.
"""

import importlib.util
import json
import re
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "benchmark_relation_loop.py"

NOTES = {
    "a.md": "Salt and brine keep the cucumber from spoiling.",
    "b.md": "Brine strength decides how sour the pickle is.",
    "c.md": "Vinegar sours the vegetables outright.",
}

MAPPING = {
    "regions": [
        {"id": 0, "members": ["a.md"], "representatives": ["a.md"]},
        {"id": 1, "members": ["b.md"], "representatives": ["b.md"]},
        {"id": 2, "members": ["c.md"], "representatives": ["c.md"]},
    ],
    "edges": [{"source": 0, "target": 1}, {"source": 1, "target": 2}],
}

CHARACTERS = {
    0: {"about": "salt and brine", "topics": ["salt"], "key_claims": ["salt preserves"]},
    1: {"about": "brine strength", "topics": ["brine"], "key_claims": ["brine sours"]},
    2: {"about": "vinegar", "topics": ["vinegar"], "key_claims": ["vinegar sours"]},
}


def _canned(prompt, schema, **kwargs):
    """Answer with the pair the prompt names, in their own words."""
    regions = [int(number) for number in re.findall(r"^Region (\d+):", prompt, re.M)]
    abouts = re.findall(r"^Region \d+: (.+)$", prompt, re.M)
    words = [about.split()[0] for about in abouts]
    return {"source": regions[0], "target": regions[1],
            "statement": f"regions {regions[0]} and {regions[1]} share "
                         f"{words[0]} and {words[1]}"}


def _judge(claim, evidence):
    return {"supported": "brine" in evidence, "reason": f"evidence {len(evidence)} chars"}


def _load():
    spec = importlib.util.spec_from_file_location("benchmark_relation_loop", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_loop_asks_every_touching_pair(tmp_path, monkeypatch):
    """One call a pair: the pairs are the map's edges, not a sample."""
    script = _load()
    monkeypatch.setattr(script, "structured", _canned)

    record = script.run(NOTES, CHARACTERS, "m", mapping=MAPPING,
                        relations_path=tmp_path / "relations", judge=_judge)

    assert record["pairs"] == 2
    assert record["written"] == 2
    assert record["missing"] == []
    assert len(record["relations"]) == 2


def test_each_statement_is_judged_against_both_regions_notes(tmp_path, monkeypatch):
    """The evidence is the notes of the two regions the pair names.

    A relation is a claim about two regions, so it is checked against the
    notes of both — the notes that would have to bear it out, the same
    evidence the faithfulness judge uses for a claim.
    """
    script = _load()
    monkeypatch.setattr(script, "structured", _canned)
    seen = []

    def judge(claim, evidence):
        seen.append(evidence)
        return {"supported": True, "reason": "ok"}

    script.run(NOTES, CHARACTERS, "m", mapping=MAPPING,
               relations_path=tmp_path / "relations", judge=judge)

    assert "cucumber" in seen[0] and "sour the pickle" in seen[0]
    assert "sour the pickle" in seen[1] and "Vinegar sours" in seen[1]


def test_the_record_counts_the_verdicts_and_the_regions_named(tmp_path, monkeypatch):
    """The record says what the judge said, and what each statement names."""
    script = _load()
    monkeypatch.setattr(script, "structured", _canned)

    record = script.run(NOTES, CHARACTERS, "m", mapping=MAPPING,
                        relations_path=tmp_path / "relations", judge=_judge)

    assert record["supported"] + record["unsupported"] == 2
    assert record["relations"][0]["mentions"]["0"]
    assert record["relations"][0]["mentions"]["1"]
    assert record["relations"][0]["seconds"] >= 0


def test_a_pair_already_on_disk_is_not_asked_again(tmp_path, monkeypatch):
    """The file is history: a pair it holds is not asked a second time."""
    script = _load()
    calls = []

    def canned(prompt, schema, **kwargs):
        calls.append(prompt)
        return _canned(prompt, schema)

    monkeypatch.setattr(script, "structured", canned)
    path = tmp_path / "relations"
    path.write_text(json.dumps({"source": 0, "target": 1,
                                 "statement": "already written"}) + "\n")

    record = script.run(NOTES, CHARACTERS, "m", mapping=MAPPING,
                        relations_path=path, judge=_judge)

    assert len(calls) == 1
    assert record["written"] == 2
    assert record["relations"][0]["statement"] == "already written"


def test_the_cost_of_a_pair_survives_a_resume(tmp_path, monkeypatch):
    """A second run over the same file reports what the pairs cost.

    The loop asks only the pairs still missing, so the cost of the ones
    already written is read from beside the file rather than guessed at:
    a resumed run that reported its own second of work would say the
    relations were free.
    """
    script = _load()
    monkeypatch.setattr(script, "structured", _canned)
    path = tmp_path / "relations"

    first = script.run(NOTES, CHARACTERS, "m", mapping=MAPPING,
                       relations_path=path, judge=_judge)
    second = script.run(NOTES, CHARACTERS, "m", mapping=MAPPING,
                        relations_path=path, judge=_judge)

    assert [v["seconds"] for v in second["relations"]] == \
           [v["seconds"] for v in first["relations"]]
    assert all(v["seconds"] is not None for v in second["relations"])
    assert second["seconds"] == first["seconds"]


def test_the_record_carries_the_page_the_reader_would_see(tmp_path, monkeypatch):
    """The page is in the record, so what the loop wrote can be read."""
    script = _load()
    monkeypatch.setattr(script, "structured", _canned)

    record = script.run(NOTES, CHARACTERS, "m", mapping=MAPPING,
                        relations_path=tmp_path / "relations", judge=_judge)

    assert "Relations" in record["page"]
    assert "0 ↔ 1" in record["page"]


def test_the_characters_are_read_from_the_line_file(tmp_path):
    """The characterisations come from the file a read wrote, keyed by region.

    The instrument reads the file the way the pipeline writes it, so the
    two cannot disagree about what a read left behind.
    """
    script = _load()
    path = tmp_path / "characterisations"
    path.write_text("".join(
        json.dumps({"region": region, **characterisation}) + "\n"
        for region, characterisation in CHARACTERS.items()))

    characters = script.read_characters(path)

    assert set(characters) == {0, 1, 2}
    assert characters[1]["about"] == "brine strength"
