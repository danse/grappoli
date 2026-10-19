"""The granularity probe's prompts and the pairs it will ask about.

`scripts/benchmark_relations.py` sends the relation task at three sizes.
`sweep` builds the map itself and reads the line file a `grappoli read`
wrote, so a region that read left uncharacterised — a model that gave up
on it — is absent from the file. A relation is written between
characterisations only, so the probe must ask about the pairs that have
one at both ends and no others; naming an empty region is the `KeyError`
an overnight batch died on, and this pins it out.

The map and the model call are substituted, so no encoder and no Ollama:
what is pinned is which pairs `sweep` chooses and what it puts in the
prompts.
"""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "benchmark_relations.py"


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("benchmark_relations", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Two edges, one of them to a region the read will leave uncharacterised.
MAPPING = {
    "regions": [{"id": 0, "members": ["a"]},
                {"id": 1, "members": ["b"]},
                {"id": 2, "members": ["c"]}],
    "edges": [{"source": 0, "target": 1}, {"source": 0, "target": 2}],
}


def _write_chars(path, regions):
    path.write_text("".join(
        json.dumps({"region": region, "about": f"about {region}",
                    "topics": [f"t{region}"], "key_claims": [f"claim {region}"]}) + "\n"
        for region in regions))


def _canned(prompt, model):
    return {"prompt_tokens": 1, "gen_tokens": 1, "seconds": 0.0, "tool_calls": 0,
            "valid": False, "detail": "- none", "content": ""}


def test_sweep_probes_only_pairs_whose_regions_are_characterised(script, monkeypatch, tmp_path):
    """A region the read left uncharacterised is named in no prompt.

    Region 2 has no characterisation, so its edge is not a pair the probe
    can ask about: every prompt names regions 0 and 1 only.
    """
    monkeypatch.setattr(script, "build_map", lambda notes, **kw: MAPPING)
    prompts = []

    def ask(prompt, model):
        prompts.append(prompt)
        return _canned(prompt, model)

    monkeypatch.setattr(script, "probe", ask)
    characters = tmp_path / "characterisations"
    _write_chars(characters, [0, 1])

    results = script.sweep({"a.md": "a note"}, characters, "m")

    assert [result["approach"] for result in results] == ["per edge", "per region", "whole map"]
    prompt_text = "\n".join(prompts)
    assert "Region 2" not in prompt_text
    assert "Region 1" in prompt_text


def test_sweep_probes_nothing_when_no_pair_is_characterised(script, monkeypatch, tmp_path):
    """With no pair at both ends characterised there is nothing to ask."""
    mapping = {"regions": MAPPING["regions"], "edges": [{"source": 0, "target": 2}]}
    monkeypatch.setattr(script, "build_map", lambda notes, **kw: mapping)
    calls = []
    monkeypatch.setattr(script, "probe", lambda *a: calls.append(a) or {})
    characters = tmp_path / "characterisations"
    _write_chars(characters, [0, 1])

    assert script.sweep({"a.md": "a note"}, characters, "m") == []
    assert calls == []


def test_sweep_rejects_an_edge_to_an_uncharacterised_region(script, monkeypatch, tmp_path):
    """An explicit `--edge` naming an empty region is an error, not a crash."""
    monkeypatch.setattr(script, "build_map", lambda notes, **kw: MAPPING)
    characters = tmp_path / "characterisations"
    _write_chars(characters, [0, 1])

    with pytest.raises(ValueError, match="no characterisation"):
        script.sweep({"a.md": "a note"}, characters, "m", edge="0,2")
