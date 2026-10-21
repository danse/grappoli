"""The relation loop's tools, its relation file, and its orchestration.

The agent's tools are ordinary Python, so these pin what the agent can
reach without a model in the loop: the toolbox is built from the map and
the characterisations alone, so no call can return a note; a relation is
only written between two characterised regions; and the file resumes by
pair without rewriting history. The loop on top of them is exercised
separately, with a scripted model, and so is `relate_regions`, the
orchestration that bounds the loop and resumes a partial file.
"""

import json

import pytest

from grappoli.model import ModelError
from grappoli.relations import (
    HARD_CAP,
    InvalidRelation,
    MAX_PAIR_ATTEMPTS,
    Toolbox,
    WRITE_RELATION,
    build_prompt,
    pair_prompt,
    read_relations,
    relate_pairs,
    relate_regions,
    relatable_edges,
    round_budget,
    run_agent,
    validate_relation,
)

CHARS = {
    0: {"about": "salt and brine", "topics": ["salt", "brine"], "key_claims": ["salt preserves"]},
    1: {"about": "salt curing meat", "topics": ["salt", "curing"], "key_claims": ["curing dries"]},
}

# Distinctive names stand in for notes; a tool that leaks one is caught.
REGIONS = [
    {"id": 0, "members": ["NOTE-A", "NOTE-B"], "representatives": ["NOTE-A"]},
    {"id": 1, "members": ["NOTE-C"], "representatives": ["NOTE-C"]},
]
MAPPING = {"regions": REGIONS, "edges": [{"source": 0, "target": 1, "weight": 2}]}

# Three regions with two edges, so an orchestration test can have a pair
# written and a pair left over in the same run.
CHARS3 = {
    0: {"about": "salt", "topics": ["salt"], "key_claims": ["salt preserves"]},
    1: {"about": "brine", "topics": ["brine"], "key_claims": ["brine keeps"]},
    2: {"about": "vinegar", "topics": ["vinegar"], "key_claims": ["vinegar sours"]},
}
REGIONS3 = [
    {"id": 0, "members": ["N0"], "representatives": ["N0"]},
    {"id": 1, "members": ["N1"], "representatives": ["N1"]},
    {"id": 2, "members": ["N2"], "representatives": ["N2"]},
]
MAPPING3 = {
    "regions": REGIONS3,
    "edges": [{"source": 0, "target": 1, "weight": 2},
              {"source": 1, "target": 2, "weight": 1}],
}


def toolbox(path):
    return Toolbox(MAPPING, CHARS, path)


# --- validation -----------------------------------------------------------

def test_relation_is_stored_low_then_high():
    assert validate_relation(1, 0, "  they share salt  ", CHARS) == {
        "source": 0, "target": 1, "statement": "they share salt",
    }


@pytest.mark.parametrize("source,target,statement", [
    ("0", 1, "x"),            # id not an integer
    (True, 1, "x"),           # bool is not a region id
    (0, 0, "x"),              # a region cannot relate to itself
    (0, 2, "x"),              # region 2 has no characterisation
    (0, 1, ""),               # empty statement
    (0, 1, "   "),            # blank statement
    (0, 1, 7),                # statement not a string
])
def test_bad_relations_are_rejected(source, target, statement):
    with pytest.raises(InvalidRelation):
        validate_relation(source, target, statement, CHARS)


# --- the file -------------------------------------------------------------

def test_relations_are_keyed_by_unordered_pair(tmp_path):
    path = tmp_path / "relations"
    path.write_text(json.dumps({"source": 1, "target": 0, "statement": "x"}) + "\n")
    assert set(read_relations(path)) == {(0, 1)}


def test_relatable_edges_drop_an_uncharacterised_endpoint():
    """An edge to a region with no characterisation is not a pair to relate.

    A read can leave a region uncharacterised — a model that gave up on
    it — and there is nothing to characterise a relation from. Both the
    loop and the granularity probe start from this list rather than
    building a prompt around an empty region (architecture.md, Agent
    tools).
    """
    mapping = {"regions": REGIONS3, "edges": [
        {"source": 0, "target": 1}, {"source": 0, "target": 2}, {"source": 1, "target": 2}]}

    assert relatable_edges(mapping, {0: CHARS3[0], 1: CHARS3[1]}) == [(0, 1)]


def test_relatable_edges_are_normalised_and_deduplicated():
    """The pair key is low-then-high, so a line either way round is one pair."""
    mapping = {"regions": REGIONS3, "edges": [
        {"source": 1, "target": 0}, {"source": 0, "target": 1}]}

    assert relatable_edges(mapping, CHARS3) == [(0, 1)]


def test_a_torn_line_is_not_a_completed_pair(tmp_path):
    path = tmp_path / "relations"
    path.write_text(json.dumps({"source": 0, "target": 1, "statement": "x"}) + "\n"
                    + '{"source": 0, "target": 2, "stat')
    assert set(read_relations(path)) == {(0, 1)}


# --- the toolbox ----------------------------------------------------------

def test_toolbox_is_built_without_the_notes(tmp_path):
    """No argument accepts a note dictionary, so no call can return one.

    The constraint is structural rather than instructed (architecture.md,
    Agent tools): a corpus that is never handed in cannot leak out.
    """
    import inspect

    assert "notes" not in inspect.signature(Toolbox.__init__).parameters
    outputs = json.dumps([
        toolbox(tmp_path / "r").list_regions(),
        toolbox(tmp_path / "r").read_characterisation(0),
        toolbox(tmp_path / "r").compare_regions(0, 1),
    ])
    assert "NOTE-A" not in outputs and "NOTE-C" not in outputs


def test_list_regions_reports_size_and_whether_characterised(tmp_path):
    result = toolbox(tmp_path / "r").list_regions()
    assert result["regions"] == [
        {"id": 0, "members": 2, "characterised": True},
        {"id": 1, "members": 1, "characterised": True},
    ]
    assert result["edges"] == [{"source": 0, "target": 1, "related": False}]


def test_reading_an_uncharacterised_region_is_an_error_not_a_crash(tmp_path):
    box = Toolbox(MAPPING, {0: CHARS[0]}, tmp_path / "r")
    assert box.read_characterisation(1) == {"error": "region 1 has no characterisation"}
    assert "error" in box.compare_regions(0, 1)


def test_compare_regions_reports_what_they_share(tmp_path):
    result = toolbox(tmp_path / "r").compare_regions(0, 1)
    assert result["shared_topics"] == ["salt"]
    assert "salt" in result["shared_terms"]
    assert "brine" not in result["shared_terms"]


def test_compare_regions_drops_the_stopwords_it_is_given(tmp_path):
    """The words a corpus says nothing with are the corpus's, not a list
    in the code, so they are handed to the toolbox and honoured
    (`architecture.md`, Language)."""
    box = Toolbox(MAPPING, CHARS, tmp_path / "r", stop=frozenset({"salt"}))
    assert box.compare_regions(0, 1)["shared_terms"] == []


def test_write_relation_appends_one_normalised_line(tmp_path):
    path = tmp_path / "relations"
    result = toolbox(path).write_relation(1, 0, "they both preserve with salt")
    assert result == {"ok": True, "source": 0, "target": 1,
                      "statement": "they both preserve with salt"}
    assert read_relations(path) == {(0, 1): {
        "source": 0, "target": 1, "statement": "they both preserve with salt",
    }}


def test_write_relation_refuses_an_uncharacterised_endpoint(tmp_path):
    """A relation is written between characterisations only
    (architecture.md, Agent tools).

    Region 1 has no characterisation, so there is nothing to characterise
    a relation to it from; the call comes back an error, not a line.
    """
    path = tmp_path / "relations"
    result = Toolbox(MAPPING, {0: CHARS[0]}, path).write_relation(0, 1, "x")
    assert "error" in result
    assert not path.exists()


def test_write_relation_refuses_a_pair_already_on_disk(tmp_path):
    """A completed relation is never regenerated (architecture.md, Agent tools).

    The file is the resume state, so rewriting a pair would both spend
    generation and overwrite a line that is already right. The refusal is
    here rather than in the prompt, so a model that repeats itself cannot
    slip one past.
    """
    path = tmp_path / "relations"
    box = toolbox(path)
    assert box.write_relation(0, 1, "first").get("ok")
    second = box.write_relation(1, 0, "second")
    assert "error" in second
    assert len(path.read_text().splitlines()) == 1


def test_list_regions_marks_a_pair_that_already_has_a_relation(tmp_path):
    """The model can see what is done, which is what a resume needs."""
    path = tmp_path / "relations"
    assert toolbox(path).list_regions()["edges"] == [
        {"source": 0, "target": 1, "related": False}]
    toolbox(path).write_relation(0, 1, "s")
    assert Toolbox(MAPPING, CHARS, path).list_regions()["edges"] == [
        {"source": 0, "target": 1, "related": True}]


def test_unknown_or_malformed_calls_are_errors_not_exceptions(tmp_path):
    """A bad round is recoverable; it must not end the run."""
    box = toolbox(tmp_path / "r")
    assert "error" in box.call("read_note", {})
    assert "error" in box.call("read_characterisation", {"region": "zero"})
    assert "error" in box.call("write_relation", {"source": 0})


# --- the loop, against a scripted model -----------------------------------

class ScriptedModel:
    """Hands back canned assistant messages in order; records what it saw."""

    def __init__(self, *messages):
        self.messages = list(messages)
        self.calls = []

    def __call__(self, messages, tools):
        self.calls.append(list(messages))
        if not self.messages:
            return {"role": "assistant", "content": ""}
        return self.messages.pop(0)


def assistant(*calls, content=""):
    return {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {"function": {"name": name, "arguments": arguments}} for name, arguments in calls
        ],
    }


STOP = {"role": "assistant", "content": "done"}


def test_loop_stops_when_the_model_names_no_tool(tmp_path):
    model = ScriptedModel(STOP)
    run = run_agent("relate 0 and 1", toolbox(tmp_path / "r"), model, max_rounds=8)
    assert run.stopped is True
    assert run.rounds == 0
    assert run.written == []


def test_loop_runs_a_tool_then_stops(tmp_path):
    """A named tool is executed and its result fed back before stopping."""
    model = ScriptedModel(assistant(("read_characterisation", {"region": 0})), STOP)
    run = run_agent("relate 0 and 1", toolbox(tmp_path / "r"), model, max_rounds=8)
    assert run.stopped is True
    assert run.rounds == 1
    follow_up = model.calls[1]
    assert follow_up[-1]["role"] == "tool"
    assert "salt and brine" in follow_up[-1]["content"]


def test_loop_is_bounded_when_the_model_never_stops(tmp_path):
    """An adversarial model that keeps calling tools hits the cap, not run.

    The cap is the guarantee that an unbounded loop cannot hang the
    machine (architecture.md, Agent tools); running into it is a bounded
    result,
    not an exception.
    """
    model = ScriptedModel(*[assistant(("list_regions", {})) for _ in range(100)])
    run = run_agent("relate 0 and 1", toolbox(tmp_path / "r"), model, max_rounds=5)
    assert run.stopped is False
    assert run.rounds == 5
    assert len(model.calls) == 5


def test_loop_records_a_written_relation(tmp_path):
    path = tmp_path / "relations"
    model = ScriptedModel(
        assistant(("write_relation", {"source": 1, "target": 0, "statement": "they share salt"})),
        STOP,
    )
    run = run_agent("relate 0 and 1", toolbox(path), model, max_rounds=8)
    assert run.written == [(0, 1)]
    assert read_relations(path) == {(0, 1): {"source": 0, "target": 1,
                                             "statement": "they share salt"}}


def test_a_tool_error_costs_a_round_not_the_run(tmp_path):
    """A missing characterisation comes back an error; the loop carries on."""
    path = tmp_path / "relations"
    model = ScriptedModel(
        assistant(("read_characterisation", {"region": 9})),
        assistant(("write_relation", {"source": 0, "target": 1, "statement": "s"})),
        STOP,
    )
    run = run_agent("relate 0 and 1", toolbox(path), model, max_rounds=8)
    assert run.written == [(0, 1)]
    assert "no characterisation" in model.calls[1][-1]["content"]


def test_a_relation_to_an_uncharacterised_region_is_not_recorded(tmp_path):
    path = tmp_path / "relations"
    model = ScriptedModel(
        assistant(("write_relation", {"source": 0, "target": 9, "statement": "s"})),
        STOP,
    )
    run = run_agent("relate 0 and 9", toolbox(path), model, max_rounds=8)
    assert run.written == []
    assert not path.exists()


def test_a_malformed_call_is_recoverable(tmp_path):
    """Unknown names and unparseable arguments are errors, not crashes."""
    model = ScriptedModel(
        assistant(("read_note", {"note": "NOTE-A"})),
        assistant(("read_characterisation", "not json")),
        STOP,
    )
    run = run_agent("relate 0 and 1", toolbox(tmp_path / "r"), model, max_rounds=8)
    assert run.stopped is True
    assert "no tool named" in model.calls[1][-1]["content"]


def test_every_call_in_a_round_is_run(tmp_path):
    model = ScriptedModel(
        assistant(("read_characterisation", {"region": 0}),
                  ("read_characterisation", {"region": 1})),
        STOP,
    )
    run = run_agent("relate 0 and 1", toolbox(tmp_path / "r"), model, max_rounds=8)
    assert run.stopped is True
    tool_messages = [m for m in model.calls[1] if m["role"] == "tool"]
    assert len(tool_messages) == 2


def test_progress_is_reported_for_each_round_and_relation(tmp_path):
    rounds, relations = [], []
    model = ScriptedModel(
        assistant(("write_relation", {"source": 0, "target": 1, "statement": "s"})),
        STOP,
    )
    run_agent("relate 0 and 1", toolbox(tmp_path / "r"), model, max_rounds=8,
              on_round=lambda n, cap: rounds.append((n, cap)),
              on_relation=lambda a, b: relations.append((a, b)))
    assert rounds == [(1, 8), (2, 8)]
    assert relations == [(0, 1)]


def test_each_call_is_reported_with_its_arguments_and_outcome(tmp_path):
    """A stalled loop is readable: which tool, with what, and the answer.

    The model's choice is what the relation loop exists to produce, so
    the trace names the tool and its arguments and says when the tool
    refused — an error repeated across rounds is how a fixation shows up
    (architecture.md, Progress and logging).
    """
    calls = []
    model = ScriptedModel(
        assistant(("read_characterisation", {"region": 0})),
        assistant(("write_relation", {"source": 0, "target": 1, "statement": "s"})),
        STOP,
    )
    run_agent("relate", toolbox(tmp_path / "r"), model, max_rounds=8,
              on_call=lambda name, arguments, result: calls.append((name, arguments, result)))
    assert [name for name, _, _ in calls] == ["read_characterisation", "write_relation"]
    assert calls[0][1] == {"region": 0}
    assert calls[1][2].get("ok")


def test_the_message_that_stopped_the_loop_is_reported(tmp_path):
    """The stop is a message, and what it says explains the stall.

    A loop that ends in prose after one tool call is not the same failure
    as one that ends when every pair is related, so the caller can see
    the message that ended it (architecture.md, Progress and logging).
    """
    stops = []
    ending = {"role": "assistant", "content": "The regions are 0, 1, 2 and 3."}
    model = ScriptedModel(assistant(("list_regions", {})), ending)
    run_agent("relate", toolbox(tmp_path / "r"), model, max_rounds=8, on_stop=stops.append)
    assert stops == [ending]


# --- the orchestration, against a scripted model --------------------------

def test_round_budget_is_bounded_by_the_hard_cap():
    """A huge map still gets a bounded loop: hung machines are not bugs.

    The budget grows with the edges so a real map can be covered, but
    never past HARD_CAP (architecture.md, Agent tools).
    """
    assert round_budget(1000) == HARD_CAP
    assert 1 <= round_budget(1) < HARD_CAP


def test_prompt_asks_for_the_tools_and_a_silent_stop():
    """The prompt names the tools, no region, and the way to stop.

    The stop is a message naming no tool, so the prompt must ask for that
    rather than for a `done` tool the surface does not have; and it must
    name no region or note, because finding the map is `list_regions`'
    job (architecture.md, Agent tools).
    """
    prompt = build_prompt()
    for name in ("list_regions", "read_characterisation", "compare_regions", "write_relation"):
        assert name in prompt
    assert "without calling a tool" in prompt
    assert "NOTE-" not in prompt


def test_relate_regions_writes_every_relatable_edge(tmp_path):
    path = tmp_path / "relations"
    model = ScriptedModel(
        assistant(("write_relation", {"source": 0, "target": 1, "statement": "a"})),
        assistant(("write_relation", {"source": 2, "target": 1, "statement": "b"})),
        STOP,
    )
    assert relate_regions(MAPPING3, CHARS3, path, llm=model) == []
    assert set(read_relations(path)) == {(0, 1), (1, 2)}


def test_relate_regions_resumes_without_regenerating_a_completed_pair(tmp_path):
    """A rerun writes only the pair that is missing, not the whole map.

    The completed line is left exactly as it was and the run appends the
    missing one, so the file is history rather than a rewritten document.
    """
    path = tmp_path / "relations"
    path.write_text(json.dumps({"source": 0, "target": 1, "statement": "already"}) + "\n")
    model = ScriptedModel(
        assistant(("write_relation", {"source": 1, "target": 2, "statement": "b"})),
        STOP,
    )
    assert relate_regions(MAPPING3, CHARS3, path, llm=model) == []
    assert [json.loads(line) for line in path.read_text().splitlines()] == [
        {"source": 0, "target": 1, "statement": "already"},
        {"source": 1, "target": 2, "statement": "b"},
    ]


def test_relate_regions_refuses_to_regenerate_a_completed_pair(tmp_path):
    """A model that rewrites a done pair cannot overwrite the line."""
    path = tmp_path / "relations"
    path.write_text(json.dumps({"source": 0, "target": 1, "statement": "already"}) + "\n")
    model = ScriptedModel(
        assistant(("write_relation", {"source": 0, "target": 1, "statement": "again"})),
        STOP,
    )
    assert relate_regions(MAPPING3, CHARS3, path, llm=model) == [(1, 2)]
    assert read_relations(path)[(0, 1)]["statement"] == "already"
    assert len(path.read_text().splitlines()) == 1


def test_relate_regions_reports_a_pair_the_model_never_wrote(tmp_path):
    """A loop that stops early leaves the map partial, and says so."""
    path = tmp_path / "relations"
    assert relate_regions(MAPPING3, CHARS3, path, llm=ScriptedModel(STOP)) == [(0, 1), (1, 2)]
    assert not path.exists()


def test_relate_regions_ignores_edges_to_uncharacterised_regions(tmp_path):
    """An edge to a region with no characterisation has nothing to relate.

    It is not a missing relation to chase, so it never counts against the
    run: only pairs whose two regions are characterised are attempted.
    """
    mapping = {"regions": REGIONS3,
               "edges": [{"source": 0, "target": 1}, {"source": 0, "target": 2}]}
    model = ScriptedModel(
        assistant(("write_relation", {"source": 0, "target": 1, "statement": "a"})),
        STOP,
    )
    assert relate_regions(mapping, {0: CHARS3[0], 1: CHARS3[1]},
                          tmp_path / "r", llm=model) == []


def test_relate_regions_does_nothing_when_every_pair_is_done(tmp_path):
    """A finished map spends no generation on a rerun."""
    path = tmp_path / "relations"
    path.write_text(json.dumps({"source": 0, "target": 1, "statement": "a"}) + "\n"
                    + json.dumps({"source": 1, "target": 2, "statement": "b"}) + "\n")
    model = ScriptedModel(STOP)
    assert relate_regions(MAPPING3, CHARS3, path, llm=model) == []
    assert model.calls == []


def test_relate_regions_reports_progress_per_round_and_relation(tmp_path):
    """The relation loop's progress is its round and the relation in hand."""
    rounds, relations = [], []

    def progress(label, done, total, eta):
        (rounds if label == "round" else relations).append((label, done, total))

    model = ScriptedModel(
        assistant(("write_relation", {"source": 0, "target": 1, "statement": "a"})),
        STOP,
    )
    relate_regions(MAPPING3, CHARS3, tmp_path / "r", llm=model, progress=progress)
    assert rounds[-1] == ("round", 2, round_budget(2))
    assert relations == [("relation", 1, 2)]


def test_relate_regions_logs_the_tool_it_named(tmp_path):
    """The run's log shows the loop's choices, not only its totals.

    The summary counts relations; when a loop stalls, what is missing
    from it is the choice that stalled, so each executed call is logged
    with the tool it named (architecture.md, Progress and logging).
    """
    lines = []
    model = ScriptedModel(
        assistant(("list_regions", {})),
        assistant(("write_relation", {"source": 0, "target": 1, "statement": "a"})),
        STOP,
    )
    relate_regions(MAPPING3, CHARS3, tmp_path / "r", llm=model, log=lines.append)
    traced = "\n".join(lines)
    assert "list_regions" in traced
    assert "write_relation" in traced
    assert "stopped: done" in traced


def test_relate_regions_is_bounded_when_the_model_never_stops(tmp_path):
    """The cap is the guarantee; running into it is a result, not a hang."""
    model = ScriptedModel(*[assistant(("list_regions", {})) for _ in range(100)])
    missing = relate_regions(MAPPING3, CHARS3, tmp_path / "r", llm=model)
    assert missing == [(0, 1), (1, 2)]
    assert len(model.calls) == round_budget(2)


# --- the structured channel ------------------------------------------------
#
# The other channel: the orchestration names the pair and the model is
# asked for one relation, in one call, from the two characterisations.


class ScriptedAnswers:
    """A model that fills the schema, from a script.

    The structured channel is `(prompt, schema) -> dict`, so an answer is
    the arguments the model filled the schema with. An exception in the
    script is raised instead, which is how a model that produced nothing
    usable arrives.
    """

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []

    def __call__(self, prompt, schema):
        self.calls.append((prompt, schema))
        if not self.answers:
            raise ModelError("no answer left")
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def test_the_prompt_holds_the_two_characterisations_and_no_third_region():
    """The pair is the whole of the model's world for the call.

    The prompt is built from the characterisations, so no note can be in
    it even by accident — the corpus is out of reach here as it is in the
    toolbox (`architecture.md`, Agent tools).
    """
    prompt = pair_prompt(0, 1, CHARS3)
    assert "Region 0" in prompt and "Region 1" in prompt
    assert "vinegar" not in prompt
    assert "NOTE-" not in prompt


def test_the_call_carries_the_relation_schema(tmp_path):
    """The answer is one relation: the schema is the relation's shape."""
    model = ScriptedAnswers({"source": 0, "target": 1, "statement": "a"})
    relate_pairs(MAPPING3, CHARS3, tmp_path / "r", llm=model)
    assert model.calls[0][1] is WRITE_RELATION


def test_relate_pairs_writes_one_relation_for_every_touching_pair(tmp_path):
    """The loop's contract is a relation for every pair that touches."""
    path = tmp_path / "relations"
    model = ScriptedAnswers(
        {"source": 0, "target": 1, "statement": "both are about salt"},
        {"source": 1, "target": 2, "statement": "both are about brine"},
    )
    assert relate_pairs(MAPPING3, CHARS3, path, llm=model) == []
    assert set(read_relations(path)) == {(0, 1), (1, 2)}
    assert read_relations(path)[(1, 2)]["statement"] == "both are about brine"


def test_relate_pairs_writes_the_line_the_native_loop_writes(tmp_path):
    """One file and one shape: the page renders either channel's relations."""
    path = tmp_path / "relations"
    model = ScriptedAnswers({"source": 0, "target": 1, "statement": "a"})
    relate_pairs(MAPPING3, CHARS3, path, llm=model)
    assert [json.loads(line) for line in path.read_text().splitlines()] == [
        {"source": 0, "target": 1, "statement": "a"},
    ]


def test_relate_pairs_does_not_ask_again_for_a_pair_already_written(tmp_path):
    """A rerun spends no generation on a pair the file already holds."""
    path = tmp_path / "relations"
    path.write_text(json.dumps({"source": 0, "target": 1, "statement": "already"}) + "\n")
    model = ScriptedAnswers({"source": 1, "target": 2, "statement": "b"})
    assert relate_pairs(MAPPING3, CHARS3, path, llm=model) == []
    assert len(model.calls) == 1
    assert read_relations(path)[(0, 1)]["statement"] == "already"


def test_relate_pairs_rejects_an_answer_that_names_another_pair(tmp_path):
    """The orchestration chose the pair, so another one is a bad answer.

    The call was about these two regions; a relation for a different pair
    would be written under the wrong key, so the answer is refused and
    asked again.
    """
    path = tmp_path / "relations"
    model = ScriptedAnswers(
        {"source": 1, "target": 2, "statement": "about the wrong pair"},
        {"source": 0, "target": 1, "statement": "about the right pair"},
    )
    assert relate_pairs(MAPPING3, CHARS3, path, llm=model) == [(1, 2)]
    assert set(read_relations(path)) == {(0, 1)}
    assert read_relations(path)[(0, 1)]["statement"] == "about the right pair"


def test_relate_pairs_leaves_a_pair_missing_when_no_answer_holds_up(tmp_path):
    """A model that never answers leaves the map partial, and says so."""
    path = tmp_path / "relations"
    model = ScriptedAnswers(ModelError("no tool call and empty content"))
    assert relate_pairs(MAPPING3, CHARS3, path, llm=model) == [(0, 1), (1, 2)]
    assert len(model.calls) == 2 * MAX_PAIR_ATTEMPTS
    assert not path.exists()


def test_relate_pairs_ignores_edges_to_uncharacterised_regions(tmp_path):
    """An edge to a region with no characterisation has nothing to relate."""
    mapping = {"regions": REGIONS3,
               "edges": [{"source": 0, "target": 1}, {"source": 0, "target": 2}]}
    model = ScriptedAnswers({"source": 0, "target": 1, "statement": "a"})
    assert relate_pairs(mapping, {0: CHARS3[0], 1: CHARS3[1]}, tmp_path / "r", llm=model) == []
    assert len(model.calls) == 1


def test_relate_pairs_reports_progress_per_pair_and_relation(tmp_path):
    """The progress is the pair in hand and the relations written."""
    events = []

    def progress(label, done, total, eta=None):
        events.append((label, done, total))

    model = ScriptedAnswers(
        {"source": 0, "target": 1, "statement": "a"},
        {"source": 1, "target": 2, "statement": "b"},
    )
    relate_pairs(MAPPING3, CHARS3, tmp_path / "r", llm=model, progress=progress)
    assert events == [("relation", 1, 2), ("written", 1, 2),
                      ("relation", 2, 2), ("written", 2, 2)]


def test_relate_pairs_reports_each_relation_it_writes(tmp_path):
    """The instrument needs the statement and what it cost."""
    written = []
    model = ScriptedAnswers({"source": 0, "target": 1, "statement": "a"})
    relate_pairs(MAPPING3, CHARS3, tmp_path / "r", llm=model,
                 on_pair=lambda record, seconds: written.append((record["statement"], seconds)))
    assert written[0][0] == "a"
    assert written[0][1] >= 0
