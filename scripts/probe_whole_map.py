"""Ask a model for the whole map in one structured call.

The relation loop is the agentic shape, but before building orchestration on
it, it is worth knowing the ceiling: given every region's characterisation
and the touching pairs, can a local model return *all* the relations in a
single `format`-constrained answer? A loop that has to hold state across
rounds is strictly harder than this, so what this measures is the upper
bound a loop could approach.

The earlier whole-map `format` run used a *one-relation* schema, so it
could only ever return one relation and the rest of the map fell into a
prose statement. This asks for an array instead, which is the shape that
can actually express the whole map in one object. If the array comes back
complete, the task is within reach and the question is whether the loop
can reach it; if it truncates or breaks, the task is out of reach at this
size and no loop will rescue it.

Usage:
    uv run python scripts/probe_whole_map.py NOTES \
        --characterisations PATH [--model qwen2.5:0.5b] \
        [--max-tokens 768] [--out REPORT.md]
"""

import argparse
import json
import sys
import time
from pathlib import Path

from grappoli.corpus import load_corpus
from grappoli.map import build_map
from grappoli.model import ModelError, structured

ARRAY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_relations",
        "description": "Record, for every pair of touching regions, one sentence saying how they relate.",
        "parameters": {
            "type": "object",
            "properties": {
                "relations": {
                    "type": "array",
                    "description": "one entry per touching pair",
                    "items": {
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
            "required": ["relations"],
        },
    },
}


def char_block(region_id: int, chars: dict[int, dict]) -> str:
    char = chars[region_id]
    topics = ", ".join(char["topics"])
    claims = " ".join(char["key_claims"])
    return f"Region {region_id}: {char['about']} Topics: {topics} Claims: {claims}"


def whole_map_prompt(chars: dict[int, dict], edges: list[tuple[int, int]]) -> str:
    blocks = "\n\n".join(char_block(r, chars) for r in sorted(chars))
    pairs = ", ".join(f"({a},{b})" for a, b in edges)
    return (
        "A corpus of notes is mapped to the regions below, each with its "
        f"characterisation. The pairs that touch: {pairs}.\n\n"
        "For every touching pair, give one sentence saying how the two regions "
        "relate. Return them all with the write_relations tool, exactly one "
        "entry per pair.\n\n" + blocks + "\n"
    )


def evaluate(arguments, edges: list[tuple[int, int]]) -> dict:
    """Shape-check the returned array against the touching pairs."""
    result = {
        "returned": None, "valid": 0, "covered": 0, "duplicated": 0,
        "not_an_edge": 0, "malformed": 0, "missing": [], "statements": [],
    }
    if not isinstance(arguments, dict) or not isinstance(arguments.get("relations"), list):
        result["returned"] = 0 if isinstance(arguments, dict) else None
        result["missing"] = [list(edge) for edge in edges]
        return result
    relations = arguments["relations"]
    result["returned"] = len(relations)
    edge_set = {tuple(sorted(edge)) for edge in edges}
    seen = set()
    for entry in relations:
        if not isinstance(entry, dict) or not {"source", "target", "statement"} <= set(entry):
            result["malformed"] += 1
            continue
        source, target, statement = entry["source"], entry["target"], entry["statement"]
        if (not isinstance(source, int) or isinstance(source, bool)
                or not isinstance(target, int) or isinstance(target, bool)
                or source == target
                or not isinstance(statement, str) or not statement.strip()):
            result["malformed"] += 1
            continue
        result["valid"] += 1
        result["statements"].append(statement.strip())
        key = tuple(sorted((source, target)))
        if key not in edge_set:
            result["not_an_edge"] += 1
        elif key in seen:
            result["duplicated"] += 1
        else:
            seen.add(key)
            result["covered"] += 1
    result["missing"] = [list(edge) for edge in sorted(edge_set - seen)]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notes")
    parser.add_argument("--characterisations", required=True)
    parser.add_argument("--model", default="qwen2.5:0.5b")
    parser.add_argument("--max-tokens", type=int, default=768)
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

    started = time.monotonic()
    try:
        arguments = structured(whole_map_prompt(chars, edges), ARRAY_SCHEMA,
                               model=args.model, max_tokens=args.max_tokens)
        error = None
    except ModelError as err:
        arguments, error = None, str(err)
    seconds = time.monotonic() - started

    summary = evaluate(arguments, edges)
    summary.update(model=args.model, seconds=seconds, error=error, edges=len(edges))

    lines = [f"# Whole-map array probe — {args.model}", "",
             f"- edges to relate: {len(edges)}",
             f"- relations returned: {summary['returned']}",
             f"- valid entries: {summary['valid']}",
             f"- touching pairs covered: {summary['covered']} of {len(edges)}",
             f"- duplicated: {summary['duplicated']}; not an edge: {summary['not_an_edge']}; "
             f"malformed: {summary['malformed']}",
             f"- missing: {summary['missing']}",
             f"- wall clock: {seconds:.0f}s", ""]
    if error:
        lines += ["## Error", "```", error, "```", ""]
    lines.append("## Statements")
    for statement in summary["statements"]:
        lines.append(f"- {statement}")
    if not summary["statements"]:
        lines.append("- none")
    text = "\n".join(lines) + "\n"
    with_returns = (f"{args.model}: {summary['covered']}/{len(edges)} covered "
                    f"({summary['valid']} valid, {summary['returned']} returned), {seconds:.0f}s")
    print(with_returns, file=sys.stderr)
    if args.out is None:
        print(text, end="")
    else:
        Path(args.out).write_text(text)


if __name__ == "__main__":
    main()
