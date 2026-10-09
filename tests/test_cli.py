"""The `grappoli read` command.

The command has no settings file: defaults live in `build_map`, driven by
the structure benchmark, and per-run flags override them. `read` runs
both stages — the map, then one model call per region — and keeps their
working files under `NOTES/.grappoli/`, out of the reader's way. The
model is injected, so these pin the wiring (which stage wrote what, the
flags, the exit code) without Ollama, and the stage behaviour itself is
pinned in test_characterise.py.
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


@pytest.fixture
def branch(tmp_path):
    """A private copy of the corpus, so a run cannot mark the fixture."""
    target = tmp_path / "notes"
    shutil.copytree(NOTES, target)
    return target


def _artefacts(branch):
    return branch / ".grappoli"


def test_read_builds_map_and_characterisations_with_decided_defaults(branch):
    """A bare `grappoli read` runs both stages with the decided rule.

    The defaults are the point: measurement (benchmarks/structure.md)
    re-makes them, and the command exists to apply them. The map records
    the rule it used, so which defaults ran is visible in the artefact
    itself; the characterisations then satisfy the map's regions without
    the user being shown either working file.
    """
    rc = main(["read", str(branch)], llm=_answer)
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
    """The flags are the escape hatch for a single run at Stage 1.

    The TF-IDF control exists precisely so a map can be built without
    the encoder; the flags must reach the same knobs the defaults
    occupy, or they are decoration. The characterisations follow the
    regions the flags produced.
    """
    rc = main(["read", str(branch), "--similarity", "tfidf", "-k", "2", "--target", "3"],
              llm=_answer)
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
    main(["read", str(branch)], llm=_answer)
    assert not (branch / "map.json").exists()
    assert not (branch / "characterisations").exists()
    assert (_artefacts(branch) / "map.json").exists()
    assert (_artefacts(branch) / "characterisations").exists()


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

    assert main(["read", str(branch)], llm=counting) == 0
    first = len(calls)
    assert first > 0
    assert main(["read", str(branch)], llm=counting) == 0
    assert len(calls) == first, "a rerun regenerates nothing"


def test_read_exits_nonzero_when_a_region_cannot_be_characterised(branch):
    """Exhaustion is reported, not swallowed: the run exits non-zero.

    A map that is missing a characterisation is not a finished read; a
    zero exit would let a shell pipeline treat it as one. The map itself
    is still written, so the next run resumes against it.
    """

    def always_malformed(prompt, schema):
        raise ModelError("nope")

    rc = main(["read", str(branch)], llm=always_malformed)
    assert rc == 1
    assert (_artefacts(branch) / "map.json").exists()
