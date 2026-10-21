"""The batch driver's record shape and its resume.

`scripts/benchmark_all.py` runs every pipeline-step benchmark and writes
one JSON. The model-backed steps need Ollama and hours, so they cannot
run under pytest; what is pinned here is the engine around them — the
record is keyed by step, corpus and model, a completed entry is not run
again, an interrupt leaves the finished entries on disk, and the next
run resumes at the first missing one. Substituting the instruments is
what makes the record's shape a test rather than an accident of one run.
"""

import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "benchmark_all.py"

MAP = {
    "regions": [
        {"id": 0, "members": ["a.md"], "representatives": ["a.md"]},
        {"id": 1, "members": ["b.md"], "representatives": ["b.md"]},
    ],
    "edges": [{"source": 0, "target": 1}],
    "standalone": [],
}

CHARACTERS = {
    0: {"about": "the first note", "topics": ["one"], "key_claims": ["it is one"]},
    1: {"about": "the second note", "topics": ["two"], "key_claims": ["it is two"]},
}


@pytest.fixture(scope="module")
def suite():
    spec = importlib.util.spec_from_file_location("benchmark_all", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def corpus(suite, tmp_path):
    notes = tmp_path / "c1" / "notes"
    notes.mkdir(parents=True)
    (notes / "a.md").write_text("one note")
    return suite.Corpus.discover(notes)


def _runners(suite, calls, fail=None):
    """A runner per step that records the call and answers a canned value."""

    def make(step):
        def run(**kwargs):
            calls.append((step, kwargs))
            if fail == step:
                raise RuntimeError(f"{step} failed")
            return {step: True}
        return run

    return {step: make(step) for step in suite.STEPS}


def test_the_record_is_keyed_by_step_corpus_and_model(suite, corpus, tmp_path):
    out = tmp_path / "run.json"
    report = suite.run([corpus], ["m1"], ["m1"], out,
                       runners=_runners(suite, []), log=lambda *a: None)

    assert report["structure"]["c1"] == {"structure": True}
    assert report["throughput"]["m1"] == {"throughput": True}
    assert report["characterisation"]["c1"]["m1"] == {"characterisation": True}
    assert report["read"]["c1"]["m1"] == {"read": True}
    assert report["relations"]["c1"]["m1"] == {"relations": True}
    assert report["relation_loop"]["c1"]["m1"]["m1"] == {"relation_loop": True}
    assert report["measure"]["c1"]["m1"]["m1"] == {"measure": True}
    assert json.loads(out.read_text()) == report


def test_a_completed_entry_is_not_run_again(suite, corpus, tmp_path):
    calls = []
    out = tmp_path / "run.json"
    runners = _runners(suite, calls)
    suite.run([corpus], ["m1"], ["m1"], out, runners=runners, log=lambda *a: None)

    calls.clear()
    suite.run([corpus], ["m1"], ["m1"], out, runners=runners, log=lambda *a: None)

    assert calls == []


def test_force_runs_every_entry_again(suite, corpus, tmp_path):
    calls = []
    out = tmp_path / "run.json"
    runners = _runners(suite, calls)
    suite.run([corpus], ["m1"], ["m1"], out, runners=runners, log=lambda *a: None)

    calls.clear()
    suite.run([corpus], ["m1"], ["m1"], out, runners=runners, log=lambda *a: None,
              force=True)

    assert len(calls) == len(suite.STEPS)


def test_an_interrupt_keeps_finished_steps_and_the_next_run_resumes(suite, corpus, tmp_path):
    """Writing after every entry is what makes an overnight run resumable."""
    out = tmp_path / "run.json"
    runners = _runners(suite, [], fail="throughput")

    with pytest.raises(RuntimeError):
        suite.run([corpus], ["m1"], ["m1"], out, runners=runners, log=lambda *a: None)

    saved = json.loads(out.read_text())
    assert saved["structure"]["c1"] == {"structure": True}
    assert "m1" not in saved["throughput"]

    calls = []
    report = suite.run([corpus], ["m1"], ["m1"], out,
                       runners=_runners(suite, calls), log=lambda *a: None)

    assert "structure" not in [step for step, _ in calls]
    assert report["throughput"]["m1"] == {"throughput": True}
    assert report["measure"]["c1"]["m1"]["m1"] == {"measure": True}


def test_a_resumed_run_keeps_the_meta_it_began_with(suite, corpus, tmp_path):
    """A run that spans midnight keeps the date and command it began with.

    `meta` describes the run, not the invocation, so a rerun that skips
    completed entries must not re-date yesterday's record as today's.
    """
    out = tmp_path / "run.json"
    begun = {"date": "2026-10-13", "command": "benchmark_all.py --out x"}
    with pytest.raises(RuntimeError):
        suite.run([corpus], ["m1"], ["m1"], out,
                  runners=_runners(suite, [], fail="throughput"),
                  log=lambda *a: None, meta=begun)

    resumed = suite.run([corpus], ["m1"], ["m1"], out,
                        runners=_runners(suite, []), log=lambda *a: None,
                        meta={"date": "2026-10-14", "command": "benchmark_all.py --out x"})

    assert resumed["meta"] == begun


def test_measure_runs_once_per_judge(suite, corpus, tmp_path):
    calls = []
    out = tmp_path / "run.json"
    suite.run([corpus], ["m1"], ["m1", "j1"], out,
              runners=_runners(suite, calls), log=lambda *a: None)

    assert [kwargs["judge"] for step, kwargs in calls if step == "measure"] == ["m1", "j1"]


def test_the_relation_step_runs_once_per_judge(suite, corpus, tmp_path):
    """The statements are judged by each judge named, as the claims are.

    A relation statement is a claim about two regions, so the batch
    scores it with the judge it scores a characterisation's claims with.
    """
    calls = []
    out = tmp_path / "run.json"
    suite.run([corpus], ["m1"], ["m1", "j1"], out,
              runners=_runners(suite, calls), log=lambda *a: None)

    assert [kwargs["judge"] for step, kwargs in calls
            if step == "relation_loop"] == ["m1", "j1"]


def test_the_relation_step_keeps_its_relations_to_itself(suite, corpus, tmp_path,
                                                          monkeypatch):
    """The loop writes to a file of its own, and reads the cell's own map.

    The file the `read` step left is what that step recorded; the loop's
    statements are this step's measurement, so they are kept apart from
    it rather than written over it.
    """
    work_root = tmp_path / "work"
    work = work_root / f"{corpus.name}--{suite._slug('m1')}"
    shutil.copytree(corpus.path, work)
    (work / ".grappoli").mkdir()
    (work / ".grappoli" / "map.json").write_text(json.dumps({"regions": [], "edges": []}))
    (work / ".grappoli" / "characterisations").write_text("")

    seen = {}

    class FakeScript:
        @staticmethod
        def run(notes, characters, model, *, mapping=None, relations_path=None,
                judge=None, log=None):
            seen.update(notes=notes, characters=characters, model=model,
                        mapping=mapping, relations_path=relations_path, judge=judge)
            return {"written": 0}

    monkeypatch.setattr(suite, "_script", lambda name: FakeScript)

    record = suite.runners(work_root)["relation_loop"](corpus=corpus, model="m1",
                                                       judge="m1")

    assert record == {"written": 0}
    assert seen["relations_path"] == work / ".grappoli" / "relations-loop"
    assert seen["mapping"] == {"regions": [], "edges": []}
    assert seen["model"] == "m1"
    assert callable(seen["judge"])


def test_the_relation_step_runs_the_shipped_loop_over_the_cell(suite, corpus, tmp_path,
                                                               monkeypatch):
    """The stage runs the shipped loop, and the record says what it wrote.

    The model and the judge are stubbed — the loop, the file it writes
    and the page it renders are the shipped ones — so what is pinned is
    the stage's wiring, not the model's answers.
    """
    instrument = suite._script("benchmark_relation_loop")

    def canned(prompt, schema, **kwargs):
        regions = [int(number) for number in re.findall(r"^Region (\d+):", prompt, re.M)]
        return {"source": regions[0], "target": regions[1],
                "statement": f"regions {regions[0]} and {regions[1]} touch"}

    monkeypatch.setattr(instrument, "structured", canned)
    monkeypatch.setattr(suite, "_claim_judge_for",
                        lambda name: lambda claim, evidence: {"supported": True,
                                                              "reason": "stubbed"})

    work_root = tmp_path / "work"
    work = work_root / f"{corpus.name}--{suite._slug('m1')}"
    shutil.copytree(corpus.path, work)
    (work / "b.md").write_text("another note")
    (work / ".grappoli").mkdir()
    (work / ".grappoli" / "map.json").write_text(json.dumps(MAP))
    (work / ".grappoli" / "characterisations").write_text(
        "".join(json.dumps({"region": region, **characterisation}) + "\n"
                for region, characterisation in CHARACTERS.items()))

    record = suite.runners(work_root)["relation_loop"](corpus=corpus, model="m1",
                                                       judge="m1")

    assert record["written"] == 1
    assert record["supported"] == 1
    assert record["relations"][0]["statement"] == "regions 0 and 1 touch"
    assert record["relations"][0]["seconds"] is not None
    assert "Relations" in record["page"]
    assert (work / ".grappoli" / "relations-loop").is_file()
    assert not (work / ".grappoli" / "relations").exists()


def test_the_measure_step_records_what_it_cost(suite, corpus, tmp_path, monkeypatch):
    """The record carries the seconds the measurement took.

    The decoupled judge is the default, and what a measurement costs is a
    number the batch should carry rather than a question left to a live
    run (`benchmarks/measurement.md`). The judge and the redundancy
    encoder are stubbed: what is pinned is the step's wiring and what it
    writes down, not the numbers themselves.
    """
    import grappoli.measure as measure_module

    monkeypatch.setattr(suite, "_judge_for",
                        lambda name: {"judge": lambda claim, evidence: {"supported": True,
                                                                       "reason": "stubbed"}})
    monkeypatch.setattr(measure_module, "cross_encoder",
                        lambda *args, **kwargs: lambda left, right: -1.0)

    work_root = tmp_path / "work"
    work = work_root / f"{corpus.name}--{suite._slug('m1')}"
    shutil.copytree(corpus.path, work)
    (work / "b.md").write_text("another note")
    (work / ".grappoli").mkdir()
    (work / ".grappoli" / "map.json").write_text(json.dumps(MAP))
    (work / ".grappoli" / "characterisations").write_text(
        "".join(json.dumps({"region": region, **characterisation}) + "\n"
                for region, characterisation in CHARACTERS.items()))

    record = suite.runners(work_root)["measure"](corpus=corpus, model="m1", judge="m1")

    assert record["seconds"] >= 0
    assert record["faithfulness"] == 1.0
    assert record["redundancy"] == 0.0


def test_the_record_is_pretty_printed(suite, corpus, tmp_path):
    out = tmp_path / "run.json"
    suite.run([corpus], ["m1"], ["m1"], out,
              runners=_runners(suite, []), log=lambda *a: None)

    text = out.read_text()
    assert text.endswith("\n")
    assert '\n  "structure": {' in text


def test_a_corpus_takes_its_name_and_reference_from_its_directory(suite, tmp_path):
    """`<corpus>/notes/` with the reference beside `notes/` is the fixture shape."""
    root = tmp_path / "c2"
    notes = root / "notes"
    notes.mkdir(parents=True)
    (notes / "a.md").write_text("a note")
    reference = root / "reference-regions.json"
    reference.write_text("{}")

    found = suite.Corpus.discover(notes)

    assert found.name == "c2"
    assert found.reference == reference


def test_a_corpus_without_a_reference_is_not_scored(suite, tmp_path):
    notes = tmp_path / "c3" / "notes"
    notes.mkdir(parents=True)

    assert suite.Corpus.discover(notes).reference is None


def test_models_and_judges_are_separate_defaults(suite):
    """A model run by the batch is not thereby made the judge of it.

    The defaults are the pruned comparison: the two models that characterise
    every region and relate every touching pair, scored by the decoupled NLI
    judge rather than by each other. The two lists stay independent —
    `--judges` names the judge outright, and no model is a judge unless it
    is named.
    """
    models, judges = suite._selection(",".join(suite.DEFAULT_MODELS))

    assert models == list(suite.DEFAULT_MODELS)
    assert judges == list(suite.DEFAULT_JUDGES)
    assert suite.NLI_JUDGE in judges
    assert not set(models) & set(judges)


def test_an_explicit_judges_list_replaces_the_default(suite):
    _, judges = suite._selection("m1", "j1,j2")

    assert judges == ["j1", "j2"]


def test_the_nli_judge_is_a_decoupled_judge(monkeypatch, suite):
    """`nli` names the NLI judge; any other name is a generation model.

    The judge the batch injects is one place, and pinning it here keeps the
    `nli` token from silently falling through to a model judge.
    """
    monkeypatch.setattr(suite, "nli_judge", lambda: "the NLI judge")

    assert suite._judge_for("nli") == {"judge": "the NLI judge"}
    assert "judge" not in suite._judge_for("qwen2.5:0.5b")
    assert set(suite._judge_for("qwen2.5:0.5b")) == {"llm"}
