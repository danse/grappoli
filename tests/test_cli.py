"""The `grappoli read` command.

The command has no settings file: defaults live in `build_map`, driven by
the structure benchmark, and per-run flags override them. `read` runs the
whole pipeline — the map, one model call per region, then one agent loop
over the touching pairs — and keeps the working files under
`NOTES/.grappoli/`, out of the reader's way. Both model interfaces are
injected (`structured` for characterisation, `converse` for the relation
loop), so these pin the wiring — which step wrote what, the flags, the
exit code — without Ollama, and the step behaviour itself is pinned in
test_characterise.py and test_relations.py.
"""

import json
import shutil
from pathlib import Path

import pytest

from grappoli.cli import main
from grappoli.model import ModelError

NOTES = Path(__file__).parent / "fixtures" / "in-domain" / "notes"

VALID = {"about": "a region", "topics": ["a"], "key_claims": ["b"]}


def _answer(prompt, schema):
    return dict(VALID)


def _call(name, **arguments):
    return {"role": "assistant", "content": "",
            "tool_calls": [{"function": {"name": name, "arguments": arguments}}]}


def _relating_agent():
    """A scripted relation loop: list the map, write each pair once, stop.

    It reads the pairs out of its own `list_regions` result, so the test
    drives the shipped tool surface rather than being handed the map.
    """
    state = {"edges": None, "next": 0}

    def agent(messages, tools):
        if state["edges"] is None:
            for message in messages:
                if message["role"] != "tool":
                    continue
                result = json.loads(message["content"])
                if "edges" in result:
                    state["edges"] = [(e["source"], e["target"])
                                      for e in result["edges"] if not e["related"]]
                    break
            if state["edges"] is None:
                return _call("list_regions")
        if state["next"] < len(state["edges"]):
            source, target = state["edges"][state["next"]]
            state["next"] += 1
            return _call("write_relation", source=source, target=target,
                         statement=f"region {source} touches region {target}")
        return {"role": "assistant", "content": ""}

    return agent


@pytest.fixture
def branch(tmp_path):
    """A private copy of the corpus, so a run cannot mark the fixture."""
    target = tmp_path / "notes"
    shutil.copytree(NOTES, target)
    return target


def _artefacts(branch):
    return branch / ".grappoli"


def test_read_with_no_notes_says_so(tmp_path, capsys):
    """An empty branch is a mistake to report, not an empty map to build.

    The loader decides what a note is (`tests/test_corpus.py`), so a
    branch it finds nothing in stops before any model is asked.
    """
    empty = tmp_path / "empty"
    empty.mkdir()
    assert main(["read", str(empty)]) == 1
    assert "no notes under" in capsys.readouterr().err


def test_read_builds_map_and_characterisations_with_decided_defaults(branch):
    """A bare `grappoli read` runs the pipeline with the decided rule.

    The defaults are the point: measurement (benchmarks/structure.md)
    re-makes them, and the command exists to apply them. The map records
    the rule it used, so which defaults ran is visible in the artefact
    itself; the characterisations then satisfy the map's regions without
    the user being shown either working file.
    """
    rc = main(["read", str(branch)], llm=_answer, agent_llm=_relating_agent())
    assert rc == 0
    mapping = json.loads((_artefacts(branch) / "map.json").read_text())
    assert mapping["similarity"] == "bge"
    assert mapping["k"] == 5
    assert mapping["mutual"] is True
    assert mapping["resolution"] == 2.0
    assert mapping["weighted"] is True

    lines = (_artefacts(branch) / "characterisations").read_text().splitlines()
    assert len(lines) == len(mapping["regions"])
    assert all(json.loads(line)["region"] == r["id"] for line, r in zip(lines, mapping["regions"]))


def test_read_flags_override_defaults(branch):
    """The flags are the escape hatch for a single run's map.

    The TF-IDF control exists precisely so a map can be built without
    the encoder; the flags must reach the same knobs the defaults
    occupy, or they are decoration. The characterisations follow the
    regions the flags produced.
    """
    rc = main(["read", str(branch), "--similarity", "tfidf", "-k", "2", "--target", "3"],
              llm=_answer, agent_llm=_relating_agent())
    assert rc == 0
    mapping = json.loads((_artefacts(branch) / "map.json").read_text())
    assert mapping["similarity"] == "tfidf"
    assert mapping["k"] == 2
    assert all(len(r["representatives"]) <= 3 for r in mapping["regions"])
    lines = (_artefacts(branch) / "characterisations").read_text().splitlines()
    assert len(lines) == len(mapping["regions"])


def test_read_keeps_working_files_out_of_the_branch(branch):
    """`map.json` and `characterisations` are under `.grappoli/`, not loose.

    The reader's output is not the machine's intermediate; the working
    files are hidden in a dot-directory so a branch is not littered with
    them, and `.gitignore` keeps them out of commits.
    """
    main(["read", str(branch)], llm=_answer, agent_llm=_relating_agent())
    assert not (branch / "map.json").exists()
    assert not (branch / "characterisations").exists()
    assert not (branch / "relations").exists()
    assert (_artefacts(branch) / "map.json").exists()
    assert (_artefacts(branch) / "characterisations").exists()
    assert (_artefacts(branch) / "relations").exists()


def test_read_resumes_without_regenerating_completed_regions(branch):
    """A second `read` of the same branch spends no generation.

    The command rebuilds the map cheaply, but the characterisations are
    already on disk; re-sending a region would cost minutes to overwrite
    a line that is right (architecture.md, Progress and logging).
    """
    calls = []

    def counting(prompt, schema):
        calls.append(prompt)
        return dict(VALID)

    assert main(["read", str(branch)], llm=counting, agent_llm=_relating_agent()) == 0
    first = len(calls)
    assert first > 0
    assert main(["read", str(branch)], llm=counting, agent_llm=_relating_agent()) == 0
    assert len(calls) == first, "a rerun regenerates nothing"


def test_read_exits_nonzero_when_a_region_cannot_be_characterised(branch):
    """Exhaustion is reported, not swallowed: the run exits non-zero.

    A map that is missing a characterisation is not a finished read; a
    zero exit would let a shell pipeline treat it as one. The map itself
    is still written, so the next run resumes against it.
    """

    def always_malformed(prompt, schema):
        raise ModelError("nope")

    rc = main(["read", str(branch)], llm=always_malformed, agent_llm=_relating_agent())
    assert rc == 1
    assert (_artefacts(branch) / "map.json").exists()


def test_read_relates_every_touching_pair(branch):
    """The relation loop runs after characterisation and writes one line per edge.

    The pairs come from the map the run just built, so the relations
    file's pairs are exactly the map's edges; the run is a finished read
    only when every one is there.
    """
    assert main(["read", str(branch)], llm=_answer, agent_llm=_relating_agent()) == 0
    mapping = json.loads((_artefacts(branch) / "map.json").read_text())
    edges = {(min(e["source"], e["target"]), max(e["source"], e["target"]))
             for e in mapping["edges"]}
    lines = (_artefacts(branch) / "relations").read_text().splitlines()
    written = {(json.loads(line)["source"], json.loads(line)["target"]) for line in lines}
    assert written == edges


def test_read_exits_nonzero_when_a_pair_is_left_unrelated(branch):
    """A loop that stops early leaves the map partial, and the run says so."""

    def silent(messages, tools):
        return {"role": "assistant", "content": ""}

    rc = main(["read", str(branch)], llm=_answer, agent_llm=silent)
    assert rc == 1
    assert not (_artefacts(branch) / "relations").exists()


def test_read_resumes_relations_without_regenerating_them(branch):
    """A rerun writes no relation that is already on disk.

    The second run's agent lists the map and finds every pair related, so
    it writes nothing and the file is exactly as it was; the map is still
    rebuilt, which is why this is not a no-op.
    """
    assert main(["read", str(branch)], llm=_answer, agent_llm=_relating_agent()) == 0
    before = (_artefacts(branch) / "relations").read_bytes()
    assert main(["read", str(branch)], llm=_answer, agent_llm=_relating_agent()) == 0
    assert (_artefacts(branch) / "relations").read_bytes() == before


def test_read_model_flag_reaches_both_interfaces(branch):
    """`--model` binds both `structured` and `converse`, not just one step.

    The model is an open decision (architecture.md, Provisional); the
    flag exists so a run can pick one now, and it would be a trap if it
    moved only the characteriser.
    """
    seen = []

    def structure_llm(prompt, schema, model=None):
        seen.append(("structure", model))
        return dict(VALID)

    def relation_llm(messages, tools, model=None):
        seen.append(("relation", model))
        return {"role": "assistant", "content": ""}

    main(["read", str(branch), "--model", "llama3.2:latest"],
         llm=structure_llm, agent_llm=relation_llm)
    assert ("structure", "llama3.2:latest") in seen
    assert ("relation", "llama3.2:latest") in seen
