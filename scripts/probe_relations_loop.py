"""One relation per round, with the whole map in view.

The array probe showed `llama3.2:1b` can start a whole-map answer but not
finish it in one bounded generation: the JSON was still open when the
token cap hit. That is a cost of asking for everything at once, not proof
that the model cannot relate the pairs. This probe bounds each round to a
single relation — the local task a per-edge `format` call already showed
works — while keeping the whole map in view and letting the model choose
which pair to state next.

The loop holds the state the model cannot: before each call it is told
which pairs still lack a relation, so it never has to remember. It stops
when every edge has one. A pair that already has a relation is refused,
which is the resume guarantee the earlier loop run showed is otherwise
missing — there, the model rewrote `(0,1)` five times.

Usage:
    uv run python scripts/probe_relations_loop.py NOTES \
        --characterisations PATH [--model llama3.2:1b] \
        [--max-rounds 12] [--out REPORT.md]
"""

import argparse
import json
import sys
import time
from pathlib import Path

from grappoli.corpus import load_corpus
from grappoli.map import build_map
from grappoli.model import ModelError, parse_content
from grappoli.relations import Toolbox, read_relations, run_agent

# One relation: the schema that worked per edge, with no tool choice folded
# in, because the only action per round is to write the next relation.
RELATION_SCHEMA = {
    "type": "object",
    "properties": {
        "source": {"type": "integer"},
        "target": {"type": "integer"},
        "statement": {"type": "string", "description": "one sentence"},
    },
    "required": ["source", "target", "statement"],
}


class RoundToolbox(Toolbox):
    """Refuses a pair that already has a relation, so the loop can converge."""

    def write_relation(self, source, target, statement):
        if isinstance(source, int) and isinstance(target, int) and source != target:
            key = (min(source, target), max(source, target))
            if key in read_relations(self._path):
                return {"error": f"pair ({key[0]},{key[1]}) already has a relation"}
        return super().write_relation(source, target, statement)


def _char_block(region_id: int, chars: dict[int, dict]) -> str:
    char = chars[region_id]
    topics = ", ".join(char["topics"])
    claims = " ".join(char["key_claims"])
    return f"Region {region_id}: {char['about']} Topics: {topics} Claims: {claims}"


def scaffold_prompt(chars: dict[int, dict], edges: list[tuple[int, int]]) -> str:
    blocks = "\n\n".join(_char_block(r, chars) for r in sorted(chars))
    pairs = ", ".join(f"({a},{b})" for a, b in edges)
    return (
        "A corpus of notes is mapped to the regions below, each with its "
        f"characterisation. The pairs that touch: {pairs}.\n\n"
        "Relate one touching pair per turn: give one sentence saying how the "
        "two regions relate, with the write_relation tool. Only pairs that do "
        "not yet have a relation remain, and at each turn you are told which "
        "they are. When none remain, the task is done.\n\n" + blocks + "\n"
    )


def relation_llm(model: str, max_tokens: int, path: Path,
                 edge_keys: list[tuple[int, int]], trace: list[dict]):
    """An llm for `run_agent` that writes one relation each round."""
    import ollama

    def llm(messages: list[dict], tools: list[dict]) -> dict:
        written = set(read_relations(path))
        missing = [key for key in edge_keys if key not in written]
        if not missing:
            return {"role": "assistant", "content": ""}
        pairs = ", ".join(f"({a},{b})" for a, b in missing)
        turn = messages + [{"role": "user", "content":
                            f"Pairs still without a relation: {pairs}. "
                            "State one of them now."}]
        started = time.monotonic()
        reply = ollama.chat(model=model, messages=turn, format=RELATION_SCHEMA,
                            options={"num_predict": max_tokens})
        seconds = time.monotonic() - started
        message = reply["message"]
        record = {"prompt_tokens": reply.get("prompt_eval_count"),
                  "gen_tokens": reply.get("eval_count"), "seconds": seconds}
        try:
            action = parse_content(message.get("content"))
        except ModelError as err:
            record.update(source=None, target=None, statement=str(err)[:80])
            trace.append(record)
            return {"role": "assistant", "content": ""}
        record.update(source=action.get("source"), target=action.get("target"),
                      statement=str(action.get("statement"))[:80])
        trace.append(record)
        if not {"source", "target", "statement"} <= set(action):
            return {"role": "assistant", "content": ""}
        return {"role": "assistant", "content": "",
                "tool_calls": [{"function": {"name": "write_relation",
                                             "arguments": action}}]}

    return llm


def render(trace, run, edges, path, elapsed, model, max_rounds) -> str:
    edge_set = {tuple(sorted(e)) for e in edges}
    covered = sorted(set(read_relations(path)))
    lines = [f"# Relation-per-round loop — {model}", "",
             f"- rounds: {run.rounds} of a cap of {max_rounds}; "
             f"{'stopped' if run.stopped else 'hit the cap'}",
             f"- touching pairs covered: {len(covered)} of {len(edges)}",
             f"- wall clock: {elapsed:.0f}s", "",
             "| round | source | target | statement | prompt tok | gen tok | seconds |",
             "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(trace, start=1):
        lines.append(f"| {i} | {r.get('source')} | {r.get('target')} | "
                     f"`{str(r.get('statement'))[:80]}` | {r.get('prompt_tokens')} | "
                     f"{r.get('gen_tokens')} | {r.get('seconds', 0):.0f} |")
    lines += ["", "## Pairs covered"]
    for source, target in covered:
        lines.append(f"- ({source}, {target})")
    if not covered:
        lines.append("- none")
    lines += ["", "## Pairs still missing"]
    for source, target in sorted(edge_set - set(covered)):
        lines.append(f"- ({source}, {target})")
    if edge_set <= set(covered):
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notes")
    parser.add_argument("--characterisations", required=True)
    parser.add_argument("--model", default="llama3.2:1b")
    parser.add_argument("--max-rounds", type=int, default=12)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--work", default="/tmp/opencode/relations-loop")
    parser.add_argument("--out")
    args = parser.parse_args()

    notes = load_corpus(args.notes)
    mapping = build_map(notes, progress=lambda *e: None)
    chars = {}
    for line in Path(args.characterisations).read_text().splitlines():
        if line.strip():
            record = json.loads(line)
            chars[record["region"]] = record
    edges = [(e["source"], e["target"]) for e in mapping["edges"]]
    edge_keys = [tuple(sorted(edge)) for edge in edges]

    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    path = work / "relations"
    path.unlink(missing_ok=True)

    toolbox = RoundToolbox(mapping, chars, path)
    trace: list[dict] = []

    def on_round(number, total):
        print(f"round {number}/{total}", file=sys.stderr)

    def on_relation(source, target):
        print(f"  relation written: {source}-{target}", file=sys.stderr)

    started = time.monotonic()
    run = run_agent(
        scaffold_prompt(chars, edges), toolbox,
        llm=relation_llm(args.model, args.max_tokens, path, edge_keys, trace),
        max_rounds=args.max_rounds, on_round=on_round, on_relation=on_relation,
    )
    elapsed = time.monotonic() - started
    covered = list(read_relations(path))
    text = render(trace, run, edges, path, elapsed, args.model, args.max_rounds)
    print(f"{args.model}: {len(covered)}/{len(edges)} pairs covered, "
          f"{run.rounds} rounds, {'stopped' if run.stopped else 'cap'}, {elapsed:.0f}s",
          file=sys.stderr)
    if args.out is None:
        print(text, end="")
    else:
        Path(args.out).write_text(text)


if __name__ == "__main__":
    main()
