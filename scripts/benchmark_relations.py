"""Probe a model on the relation task at each conversation size.

The relation loop's open decision is granularity: one loop over the
whole map, one per region, or one per edge. The decision is settled with
numbers, not taste. Conversation cost is one number; whether the model
actually answers is another — characterisation showed 0.5B calls tools on
short prompts and reverts to prose on long ones
(`benchmarks/characterisation.md`), so a larger conversation can be both
dearer and worse.

This sends the same task at three sizes and records, per size, the prompt
tokens, whether a tool call fired, and whether a well-formed relation came
back. It is the instrument behind the granularity decision in
`benchmarks/relations.md`, and the place the model comparison for the
relation loop is taken.

Usage:
    uv run python scripts/benchmark_relations.py NOTES --characterisations PATH
        [--model qwen2.5:0.5b] [--edge 0,1] [--out REPORT.md]
"""

import argparse
import json
import sys
import time
from pathlib import Path

from grappoli.corpus import load_corpus
from grappoli.map import build_map
from grappoli.relations import relatable_edges

WRITE_RELATION = {
    "type": "function",
    "function": {
        "name": "write_relation",
        "description": "Record in one sentence how two regions of the map touch.",
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
}


def _char_block(region_id: int, chars: dict[int, dict]) -> str:
    char = chars[region_id]
    topics = ", ".join(char["topics"])
    claims = " ".join(char["key_claims"])
    return f"Region {region_id}: {char['about']} Topics: {topics} Claims: {claims}"


def per_edge_prompt(a: int, b: int, chars: dict[int, dict]) -> str:
    return (
        "Two regions of a corpus of notes, each with its characterisation. "
        "State in one sentence how they touch, using the write_relation tool.\n\n"
        f"Region {a}: {chars[a]['about']}\n\nRegion {b}: {chars[b]['about']}\n"
    )


def per_region_prompt(region: int, neighbours: list[int], chars: dict[int, dict]) -> str:
    blocks = "\n\n".join(_char_block(r, chars) for r in [region, *neighbours])
    return (
        "A region of a corpus of notes and the regions it touches, each with its "
        "characterisation. State in one sentence how the region touches each "
        "neighbour, using the write_relation tool.\n\n" + blocks + "\n"
    )


def whole_map_prompt(chars: dict[int, dict], edges: list[tuple[int, int]]) -> str:
    blocks = "\n\n".join(_char_block(r, chars) for r in sorted(chars))
    pairs = ", ".join(f"({a},{b})" for a, b in edges)
    return (
        "A corpus of notes is mapped to the regions below, each with its "
        "characterisation. State in one sentence how each touching pair relates, "
        "using the write_relation tool.\n\n" + blocks + f"\n\nTouching pairs: {pairs}\n"
    )


def _valid_relation(arguments) -> bool:
    """Whether the storage layer would accept this as a relation.

    The three fields present, ids as distinct integers, statement a
    non-empty sentence. Whether the sentence is *true of the two regions*
    is the faithfulness judge's question, so this checks only the shape.
    """
    return (
        isinstance(arguments, dict)
        and {"source", "target", "statement"} <= set(arguments)
        and isinstance(arguments["source"], int)
        and not isinstance(arguments["source"], bool)
        and isinstance(arguments["target"], int)
        and not isinstance(arguments["target"], bool)
        and arguments["source"] != arguments["target"]
        and isinstance(arguments["statement"], str)
        and bool(arguments["statement"].strip())
    )


def probe(prompt: str, model: str) -> dict:
    import ollama

    started = time.monotonic()
    reply = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        tools=[WRITE_RELATION],
        options={"num_predict": 256},
    )
    seconds = time.monotonic() - started
    message = reply["message"]
    calls = message.get("tool_calls") or []
    arguments = calls[0]["function"].get("arguments") if calls else None
    rendered = "\n".join(
        f"- `{c['function']['name']}({c['function'].get('arguments')})`" for c in calls
    ) or "- none"
    return {
        "prompt_tokens": reply.get("prompt_eval_count"),
        "gen_tokens": reply.get("eval_count"),
        "seconds": seconds,
        "tool_calls": len(calls),
        "valid": len(calls) == 1 and _valid_relation(arguments),
        "detail": rendered,
        "content": (message.get("content") or "")[:200],
    }


def probe_structured(prompt: str, model: str) -> dict:
    """The `structured` channel: `format`-constrained JSON, native call preferred."""
    from grappoli.model import ModelError, structured

    started = time.monotonic()
    try:
        arguments = structured(prompt, WRITE_RELATION, model=model, max_tokens=256)
    except ModelError as err:
        return {
            "prompt_tokens": None, "gen_tokens": None, "tool_calls": None,
            "seconds": time.monotonic() - started, "valid": False,
            "detail": f"- error: {err}", "content": None,
        }
    return {
        "prompt_tokens": None, "gen_tokens": None, "tool_calls": None,
        "seconds": time.monotonic() - started, "valid": _valid_relation(arguments),
        "detail": f"- `write_relation({arguments})`", "content": None,
    }


def sweep(notes: dict[str, str], characterisations, model: str, edge: str | None = None,
          approaches: str = "per edge,per region,whole map", channel: str = "native",
          log=None) -> list[dict]:
    """The same task at each conversation size, one result per approach.

    `characterisations` is the line file a `grappoli read` run wrote;
    `sweep` builds the map from `notes` itself, so the regions the
    prompts name are the corpus's. Only pairs whose two regions have a
    characterisation are asked about, because a relation is written
    between characterisations only. The CLI renders the list;
    `benchmark_all.py` records it.
    """
    mapping = build_map(notes, progress=lambda *e: None)
    chars = {}
    for line in Path(characterisations).read_text().splitlines():
        if line.strip():
            record = json.loads(line)
            chars[record["region"]] = record
    # A relation is written between characterisations only, so the probe
    # asks only about pairs whose two regions have one; a region a read
    # left uncharacterised is not an endpoint (relations.relatable_edges).
    edges = relatable_edges(mapping, chars)

    if edge:
        a, b = (int(x) for x in edge.split(","))
        if a not in chars or b not in chars:
            raise ValueError(f"edge ({a},{b}) names a region with no characterisation")
    elif edges:
        a, b = edges[0]
    else:
        return []
    neighbours = sorted({y for x, y in edges if x == a} | {x for x, y in edges if y == a})

    sizes = [
        ("per edge", per_edge_prompt(a, b, chars)),
        ("per region", per_region_prompt(a, neighbours, chars)),
        ("whole map", whole_map_prompt(chars, edges)),
    ]
    wanted = {label.strip() for label in approaches.split(",") if label.strip()}
    sizes = [(label, prompt) for label, prompt in sizes if label in wanted]
    ask = probe if channel == "native" else probe_structured
    results = []
    for label, prompt in sizes:
        result = ask(prompt, model)
        result["approach"] = label
        result["chars"] = len(prompt)
        if log is not None:
            log(f"{label}: {result['tool_calls']} tool calls, valid={result['valid']} "
                f"({result['seconds']:.0f}s)")
        results.append(result)
    return results


def render(results: list[dict], channel: str, model: str) -> str:
    def cell(value):
        return "-" if value is None else value

    lines = [f"# Relation granularity probe ({channel}) — {model}", "",
             "| approach | prompt tok | gen tok | tool calls | valid relation | seconds |",
             "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['approach']} | {cell(r['prompt_tokens'])} | {cell(r['gen_tokens'])} | "
                     f"{cell(r['tool_calls'])} | {'yes' if r['valid'] else 'no'} | "
                     f"{r['seconds']:.0f} |")
    lines.append("")
    lines.append("## What came back")
    for r in results:
        lines.extend(["", f"### {r['approach']}", r["detail"]])
    if channel == "native":
        lines.append("")
        lines.append("## Raw content per approach")
        for r in results:
            lines.extend(["", f"### {r['approach']}", "```", r["content"], "```"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notes")
    parser.add_argument("--characterisations", required=True,
                        help="the line file a `grappoli read` run wrote")
    parser.add_argument("--model", default="qwen2.5:0.5b")
    parser.add_argument("--edge", default=None, help="edge to use for per-edge/per-region, 'a,b'")
    parser.add_argument("--out", default=None)
    parser.add_argument("--approaches", default="per edge,per region,whole map",
                        help="comma-separated subset of the three approaches")
    parser.add_argument("--channel", choices=("native", "structured"), default="native",
                        help="how the model is asked: tools only, or format-constrained JSON")
    args = parser.parse_args()

    notes = load_corpus(args.notes)
    results = sweep(notes, args.characterisations, args.model, args.edge,
                    args.approaches, args.channel,
                    log=lambda line: print(line, file=sys.stderr))

    text = render(results, args.channel, args.model)
    if args.out is None:
        print(text, end="")
    else:
        Path(args.out).write_text(text)


if __name__ == "__main__":
    main()
