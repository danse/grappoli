"""State, in words, how two regions touch.

The map's edges already assert that regions touch; this step is what
puts that into sentences. Each relation is derived from the two
characterisations, never from the notes: the agent's whole world is the
`Toolbox` below, which holds the map structure, the stored
characterisations, and the corpus's stopwords — no note. No shipped
function returns a raw note, so the corpus is out of reach however the
agent asks (`architecture.md`, Agent tools).

A relation is one appended line, keyed by the unordered pair it names,
so an interrupted run resumes at the first missing pair and never
regenerates a completed one. Relations are only ever written between
regions that already have a characterisation: an edge to a region with
no characterisation has nothing to characterise it from.

`run_agent` is the hand-rolled loop — the model names a tool, we run it,
append the result and ask again, until it names none or the round cap is
reached (`architecture.md`, Agent tools). The tool surface, not an
instruction, is what keeps the corpus out of view.

`relate_regions` is the orchestration on top: it reads the relations
already on disk, bounds the loop with a round budget drawn from the
measured throughput, and reports progress per round and per relation. The
toolbox refuses a pair that already has a relation, so an interrupted run
resumes without regenerating a completed one.
"""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import linefile
from .model import converse
from .words import terms


class InvalidRelation(Exception):
    """An answer that parsed but is not a relation."""


def _terms(characterisation: dict, stop: frozenset[str] = frozenset()) -> set[str]:
    """The content words of a characterisation, in any language.

    The words its language says nothing with are the corpus's, handed in
    from `words.stopwords` rather than listed here, so a characterisation
    written in any language is read the same way (`architecture.md`,
    Language).
    """
    text = " ".join([characterisation["about"], *characterisation["topics"],
                     *characterisation["key_claims"]])
    return terms(text, stop)


def read_relations(path: Path) -> dict[tuple[int, int], dict]:
    """The completed relations, keyed by their unordered pair.

    The pair key is `(source, target)` with `source < target`, so a line
    written either way round is recognised as done.
    """
    done = {}
    for record in linefile.read_records(path):
        source, target = record.get("source"), record.get("target")
        if isinstance(source, int) and isinstance(target, int) and source != target:
            done[(min(source, target), max(source, target))] = record
    return done


def relatable_edges(mapping: dict, characterisations: dict[int, dict]) -> list[tuple[int, int]]:
    """The map's edges whose two regions both have a characterisation.

    A relation is written between characterisations only, so an edge to a
    region a `read` left uncharacterised — a model that gave up on it —
    is not a pair the relation step can answer. Every caller that names
    pairs, the loop and the granularity probe alike, starts from this
    list, so none of them builds a prompt around a region with nothing to
    read. Pairs are normalised low-then-high and sorted; parallel edges
    collapse to one.
    """
    return sorted({
        (min(edge["source"], edge["target"]), max(edge["source"], edge["target"]))
        for edge in mapping.get("edges", [])
        if edge["source"] in characterisations and edge["target"] in characterisations
    })


def validate_relation(source, target, statement, characterisations) -> dict:
    """Return a normalised relation record, or raise InvalidRelation.

    Both endpoints must be integers naming distinct regions that already
    hold a characterisation, because there is nothing to characterise an
    uncharacterised region from; the pair is stored low-then-high. Only
    `statement` is free text, and it must be a non-empty sentence.
    """
    for name, value in (("source", source), ("target", target)):
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidRelation(f"{name} must be a region id")
    if source == target:
        raise InvalidRelation("a region cannot relate to itself")
    for region in (source, target):
        if region not in characterisations:
            raise InvalidRelation(f"region {region} has no characterisation")
    if not isinstance(statement, str) or not statement.strip():
        raise InvalidRelation("statement must be a non-empty sentence")
    low, high = (source, target) if source < target else (target, source)
    return {"source": low, "target": high, "statement": statement.strip()}


# --- the tools the agent may call -----------------------------------------
#
# One schema per Python method on Toolbox, in the OpenAI/Ollama shape.
# The agent names one; the loop matches the name and calls the method.

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_regions",
            "description": "List the map's regions and the pairs that touch.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_characterisation",
            "description": "Read the stored characterisation of one region.",
            "parameters": {
                "type": "object",
                "properties": {"region": {"type": "integer"}},
                "required": ["region"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_regions",
            "description": "Compare two regions' characterisations for shared topics and terms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "integer"},
                    "target": {"type": "integer"},
                },
                "required": ["source", "target"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_relation",
            "description": "Record, in one sentence, how two characterised regions touch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "integer"},
                    "target": {"type": "integer"},
                    "statement": {"type": "string", "description": "one sentence"},
                },
                "required": ["source", "target", "statement"],
            },
        },
    },
]

TOOL_NAMES = {schema["function"]["name"] for schema in TOOL_SCHEMAS}


class Toolbox:
    """The agent's whole world: the map structure and the characterisations.

    Constructed without the notes — there is no argument to put them in
    — so no tool can return one. It is given the corpus's stopwords, a
    set of words and not the corpus, so a characterisation in any
    language is read by the tool that compares them (`architecture.md`,
    Language). A tool that cannot answer returns an `{"error": ...}`
    object rather than raising, so a bad call is a recoverable round
    rather than the end of the run.
    """

    def __init__(self, mapping: dict, characterisations: dict[int, dict], path: Path,
                 stop: frozenset[str] = frozenset()):
        self._regions = mapping["regions"]
        self._edges = [(e["source"], e["target"]) for e in mapping["edges"]]
        self._characterisations = characterisations
        self._path = Path(path)
        self._stop = frozenset(stop)

    def call(self, name: str, arguments: dict) -> dict:
        """Dispatch one tool call by name; unknown names are an error."""
        method = getattr(self, name, None)
        if name not in TOOL_NAMES or method is None:
            return {"error": f"no tool named {name!r}"}
        try:
            return method(**(arguments or {}))
        except TypeError as err:
            return {"error": f"bad arguments for {name}: {err}"}

    def list_regions(self) -> dict:
        done = read_relations(self._path)
        return {
            "regions": [
                {"id": region["id"], "members": len(region["members"]),
                 "characterised": region["id"] in self._characterisations}
                for region in self._regions
            ],
            "edges": [
                {"source": a, "target": b,
                 "related": (min(a, b), max(a, b)) in done}
                for a, b in self._edges
            ],
        }

    def read_characterisation(self, region: int) -> dict:
        characterisation = self._characterisations.get(region)
        if characterisation is None:
            return {"error": f"region {region} has no characterisation"}
        return {
            "region": region,
            "about": characterisation["about"],
            "topics": characterisation["topics"],
            "key_claims": characterisation["key_claims"],
        }

    def compare_regions(self, source: int, target: int) -> dict:
        left, right = self._characterisations.get(source), self._characterisations.get(target)
        for region, characterisation in ((source, left), (target, right)):
            if characterisation is None:
                return {"error": f"region {region} has no characterisation"}
        shared_topics = sorted({t.lower() for t in left["topics"]}
                               & {t.lower() for t in right["topics"]})
        shared_terms = sorted(_terms(left, self._stop) & _terms(right, self._stop))
        return {"shared_topics": shared_topics, "shared_terms": shared_terms}

    def write_relation(self, source: int, target: int, statement: str) -> dict:
        try:
            record = validate_relation(source, target, statement, self._characterisations)
        except InvalidRelation as err:
            return {"error": str(err)}
        key = (record["source"], record["target"])
        if key in read_relations(self._path):
            return {"error": f"pair ({key[0]},{key[1]}) already has a relation"}
        linefile.append(self._path, record)
        return {"ok": True, **record}


# --- the loop -------------------------------------------------------------
#
# The loop. The model names a tool, we run it, append the result and ask
# again, until it names none or the round cap is reached. A tool error is
# just another result, so a bad round is recoverable
# (architecture.md, Agent tools).


@dataclass
class AgentRun:
    """What one conversation did before it stopped or hit the cap."""

    stopped: bool
    rounds: int
    written: list[tuple[int, int]] = field(default_factory=list)


def _arguments(raw):
    """A tool call's arguments as a dict, however they arrived."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return decoded if isinstance(decoded, dict) else {}
    return {}


def _brief(arguments: dict) -> str:
    """Tool arguments as one short, loggable phrase."""
    return ", ".join(f"{key}={value!r}" for key, value in arguments.items())


def run_agent(prompt: str, toolbox: Toolbox, llm=converse, *, max_rounds: int,
              on_round=None, on_call=None, on_relation=None, on_stop=None) -> AgentRun:
    """Run one tool-using conversation to its stop, or to `max_rounds`.

    Each round asks the model for a message; a message that names tools
    is executed and its results appended, and a message that names none
    is the model stopping. `max_rounds` is the hard cap: a model that
    keeps calling tools is bounded there rather than allowed to run, and
    that is a bounded run rather than an error. A tool that cannot answer
    returns an error object, which is appended like any result, so a bad
    call costs one round and not the run. `on_round`, `on_call`,
    `on_relation` and `on_stop` are how a caller watches that happen —
    the round starting, the tool answered, a relation written, and the
    message that stopped it — without the loop itself printing anything.
    """
    messages = [{"role": "user", "content": prompt}]
    written: list[tuple[int, int]] = []
    for round_number in range(1, max_rounds + 1):
        if on_round is not None:
            on_round(round_number, max_rounds)
        message = llm(messages, TOOL_SCHEMAS)
        calls = message.get("tool_calls") or []
        if not calls:
            if on_stop is not None:
                on_stop(message)
            return AgentRun(stopped=True, rounds=round_number - 1, written=written)
        messages.append(message)
        for call in calls:
            function = call.get("function", {})
            name = function.get("name")
            arguments = _arguments(function.get("arguments"))
            result = toolbox.call(name, arguments)
            if on_call is not None:
                on_call(name, arguments, result)
            if name == "write_relation" and result.get("ok"):
                written.append((result["source"], result["target"]))
                if on_relation is not None:
                    on_relation(result["source"], result["target"])
            messages.append({"role": "tool", "content": json.dumps(result)})
    return AgentRun(stopped=False, rounds=max_rounds, written=written)


# --- orchestration --------------------------------------------------------
#
# The relation step's own bound and its prompt. A round is a model call
# plus the tool it names; at throughput.md's rates (2026-10-13) —
# ~2.4 tok/s prefill and ~1.9 tok/s generation for qwen2.5:0.5b, ~1.1
# and ~0.6 for llama3.2:latest — the conversation's growth and a short
# answer make a round about three minutes for 0.5B, and a map needs a
# round per relatable edge plus a few to find and read it. HARD_CAP
# bounds it whatever the map and the arithmetic say: an unbounded loop is
# not a bug, it is a hung machine (architecture.md, Agent tools).

SECONDS_PER_ROUND = 180.0
LOOP_SECONDS = 60 * 60.0
HARD_CAP = 20

PROMPT = """You are relating the regions of a map of notes. The map is already \
built and is reached only through the tools; no note is ever returned.

Reply to every turn with exactly one tool call. Do not answer in prose.

The tools:
- list_regions — the regions, the pairs that touch, and which pairs are \
already related
- read_characterisation(region) — a region's stored characterisation
- compare_regions(source, target) — what two regions share
- write_relation(source, target, statement) — one sentence saying how the two \
regions relate

Work through it: call list_regions; then, for each touching pair that is not \
already related, read_characterisation on both regions and call \
write_relation. Only a pair whose two regions have a characterisation can be \
related, and a pair is related once. When every touching pair has a relation, \
reply without calling a tool — that is the only turn that is not a tool call.
"""


def round_budget(edges: int) -> int:
    """Rounds allowed for a map with `edges` relatable edges.

    Drawn from the measured throughput so the loop's generation is
    bounded in time, and hard-capped however large the map is.
    """
    timed = int(LOOP_SECONDS / SECONDS_PER_ROUND)
    needed = 4 + 2 * edges
    return max(1, min(timed, HARD_CAP, needed))


def build_prompt() -> str:
    """The whole-map task prompt.

    It names no region and no pair: finding them is what `list_regions`
    is for, and that the model chooses which to read and relate is the
    behaviour the relation loop exists to produce (`architecture.md`, Agent
    tools). A pair already on disk is not named either; the model finds
    that from `list_regions` too, which is what lets a resumed run pick up
    where the last one stopped.
    """
    return PROMPT


def relate_regions(mapping: dict, characterisations: dict[int, dict], path: Path,
                   stop: frozenset[str] = frozenset(),
                   llm=converse, clock=time.monotonic,
                   progress=None, log=None) -> list[tuple[int, int]]:
    """Record a relation for every touching pair, resuming a partial file.

    The relations already on disk are read first, so a completed pair is
    never regenerated, and the toolbox refuses a duplicate write as well,
    so a model that repeats a pair cannot append one. Only edges whose two
    endpoints are characterised are attempted, because a relation is
    written between characterisations only. `stop` is the corpus's words
    that say nothing, handed to the toolbox so its `compare_regions` reads
    a characterisation in any language (`architecture.md`, Language).
    Returns the relatable pairs still missing when the loop stopped or hit
    its cap.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    linefile.drop_torn_tail(path)
    characterisations = characterisations or {}
    relatable = relatable_edges(mapping, characterisations)
    total = len(relatable)
    if all(pair in read_relations(path) for pair in relatable):
        return []

    toolbox = Toolbox(mapping, characterisations, path, stop)

    def on_round(number, cap):
        if progress is not None:
            progress("round", number, cap, (cap - number) * SECONDS_PER_ROUND)

    def on_call(name, arguments, result):
        # The model's choice is the behaviour the relation loop exists to
        # produce, so a stalled loop must be readable from the run: the
        # tool it named and the answer it got
        # (architecture.md, Progress and logging).
        if log is not None:
            outcome = result.get("error") if "error" in result else "ok"
            log(f"  {name}({_brief(arguments)}) → {outcome}")

    def on_stop(message):
        # Why it stopped matters as much as what it called: a loop that
        # ends in prose after one tool call is not the same failure as
        # one that ends after every pair is related.
        if log is not None:
            content = (message.get("content") or "").strip()
            log(f"  stopped: {content[:500] or '(no content)'}")

    def on_relation(source, target):
        if progress is not None:
            covered = len(read_relations(path))
            progress("relation", covered, total,
                     max(0, total - covered) * SECONDS_PER_ROUND)

    started = clock()
    run = run_agent(build_prompt(), toolbox, llm,
                    max_rounds=round_budget(total),
                    on_round=on_round, on_call=on_call,
                    on_relation=on_relation, on_stop=on_stop)
    seconds = clock() - started

    missing = [pair for pair in relatable if pair not in read_relations(path)]
    if log is not None:
        written = total - len(missing)
        if missing:
            log(f"relations: {written}/{total} written in {run.rounds} rounds "
                f"({seconds:.0f}s) — {len(missing)} missing; next run retries only those")
        else:
            log(f"relations: {written}/{total} written in {run.rounds} rounds ({seconds:.0f}s)")
    return missing
