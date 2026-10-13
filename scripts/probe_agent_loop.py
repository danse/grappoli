"""Drive the real relation loop with a real model, whole map.

The loop's tools and storage are settled and tested against the stub
(`relations.py`); what is not measured is whether a local model can drive
them — choose the tools itself, round after round, until the edges are
covered. Two channels have already failed a cell of that: native tool
calls carry invalid arguments even at 1b, and a one-relation `format`
cannot express the whole map. The remaining shape is an **action
object**: each round the model returns `{"tool": ..., ...}` under
`format`, pinned to valid JSON and a known tool name, and the adapter
turns it into the tool call `run_agent` already knows how to run. The
model still owns the choice; only the serialisation is constrained.

This is not a reimplementation — it wraps `run_agent` and `Toolbox`, so a
run measures the shipped loop, and traces every round so
`benchmarks/relations.md` can record whether whole-map agentic behaviour
is reachable on this hardware.

Usage:
    uv run python scripts/probe_agent_loop.py NOTES \
        --characterisations PATH [--model qwen2.5:0.5b]
        [--channel action|native] [--max-rounds 20] [--out REPORT.md]
"""

import argparse
import sys
import time
from pathlib import Path

from grappoli.corpus import load_corpus
from grappoli.map import build_map
from grappoli.model import ModelError, parse_content
from grappoli.relations import Toolbox, read_relations, run_agent


class TracingToolbox(Toolbox):
    """A Toolbox that remembers every result, for the report."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results: list[dict] = []

    def call(self, name: str, arguments: dict) -> dict:
        result = super().call(name, arguments)
        self.results.append({"name": name, "arguments": arguments, "result": result})
        return result


# The action the model may return, as JSON. `done` is the action-loop's
# equivalent of a native message that names no tool: it is how the model
# says it has finished, since `format` always returns an object.
ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "tool": {
            "type": "string",
            "enum": ["list_regions", "read_characterisation", "compare_regions",
                     "write_relation", "done"],
        },
        "region": {"type": "integer"},
        "source": {"type": "integer"},
        "target": {"type": "integer"},
        "statement": {"type": "string"},
    },
    "required": ["tool"],
    "additionalProperties": False,
}


def whole_map_prompt() -> str:
    """The whole-map task, with nothing pre-chewed.

    The architecture's whole-map shape has the model find the pairs for
    itself through `list_regions`, so the prompt gives it neither the
    regions nor the edges nor the characterisations — only the job, the
    protocol, and two worked actions. Reading and choosing pairs is the
    behaviour under test; the examples are there because 1b fills a `tool`
    field happily but not yet the arguments that belong to it.
    """
    return (
        "A corpus of notes has been mapped to regions that touch one another. "
        "State, for each pair of touching regions, one sentence describing how "
        "they relate.\n\n"
        "Find the regions and the pairs that touch with list_regions. Read a "
        "region's characterisation with read_characterisation(region). Record a "
        "relation with write_relation(source, target, statement). When every "
        "touching pair has a relation, call done.\n\n"
        "Answer every turn with exactly one JSON object: the tool, and only "
        "that tool's arguments. For example\n"
        '{"tool": "read_characterisation", "region": 0}\n'
        '{"tool": "write_relation", "source": 0, "target": 1, '
        '"statement": "Both regions concern the cold chain."}'
    )


def action_llm(model: str, max_tokens: int, trace: list[dict]):
    """An llm for `run_agent` that reads an action object out of content.

    The tools are deliberately *not* sent to Ollama. With `tools` and a
    `format` schema both present, a model routes through the native
    tool-call channel but fills its arguments from the schema, so the
    call is half one thing and half the other (a `list_regions` call
    carrying the whole action object, `tool` field included) and the
    arguments match no real signature. Sent `format` alone, the model has
    one channel: the JSON object the schema describes, which names its
    tool in a field we dispatch on. So the model still chooses the tool —
    that is the agentic behaviour — but every choice arrives in a shape
    the schema has already validated.
    """
    import ollama

    def llm(messages: list[dict], tools: list[dict]) -> dict:
        started = time.monotonic()
        reply = ollama.chat(
            model=model, messages=messages, format=ACTION_SCHEMA,
            options={"num_predict": max_tokens},
        )
        seconds = time.monotonic() - started
        message = reply["message"]
        record = {
            "prompt_tokens": reply.get("prompt_eval_count"),
            "gen_tokens": reply.get("eval_count"),
            "seconds": seconds,
        }
        if message.get("tool_calls"):
            call = message["tool_calls"][0]["function"]
            record.update(channel="native", name=call.get("name"),
                          arguments=call.get("arguments"))
            trace.append(record)
            return message
        try:
            action = parse_content(message.get("content"))
        except ModelError:
            action = None
        if action and "tool" in action:
            name = action.pop("tool")
            record.update(channel="action", name=name, arguments=action)
            trace.append(record)
            if name == "done":
                return {"role": "assistant", "content": ""}
            return {"role": "assistant", "content": "",
                    "tool_calls": [{"function": {"name": name, "arguments": action}}]}
        record.update(channel="none", name=None,
                      arguments=(message.get("content") or "")[:200])
        trace.append(record)
        return message

    return llm


def native_llm(model: str, max_tokens: int, trace: list[dict]):
    """An llm for `run_agent` that uses the native tool channel.

    This is what `model.converse` does — the tool schemas are sent to
    Ollama and the model answers with a native tool call — wrapped here
    only to trace each round. It is the channel the earlier single-prompt
    "native" rows used, never the loop.
    """
    import ollama

    def llm(messages: list[dict], tools: list[dict]) -> dict:
        started = time.monotonic()
        reply = ollama.chat(
            model=model, messages=messages, tools=tools,
            options={"num_predict": max_tokens},
        )
        seconds = time.monotonic() - started
        message = reply["message"]
        calls = message.get("tool_calls") or []
        first = calls[0]["function"] if calls else {}
        trace.append({
            "prompt_tokens": reply.get("prompt_eval_count"),
            "gen_tokens": reply.get("eval_count"),
            "seconds": seconds,
            "channel": "native" if calls else "none",
            "name": first.get("name"),
            "arguments": first.get("arguments") if calls
            else (message.get("content") or "")[:200],
        })
        return message

    return llm


def render(trace: list[dict], results: list[dict], run, written: list, edges: list,
           elapsed: float, model: str, max_rounds: int) -> str:
    edge_set = {tuple(sorted(e)) for e in edges}
    lines = [f"# Agent-loop run — {model}", "",
             f"- rounds: {run.rounds} of a cap of {max_rounds}; "
             f"{'stopped' if run.stopped else 'hit the cap'}",
             f"- relations written: {len(written)} of {len(edges)} edges",
             f"- wall clock: {elapsed:.0f}s", "",
             "| round | channel | tool | arguments | prompt tok | gen tok | seconds |",
             "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(trace, start=1):
        arguments = r.get("arguments")
        if isinstance(arguments, dict):
            arguments = ", ".join(f"{k}={v}" for k, v in arguments.items())
        lines.append(f"| {i} | {r.get('channel')} | {r.get('name')} | "
                     f"`{str(arguments)[:120]}` | {r.get('prompt_tokens')} | "
                     f"{r.get('gen_tokens')} | {r.get('seconds', 0):.0f} |")
    lines.append("")
    lines.append("## Tool results")
    if results:
        for i, r in enumerate(results, start=1):
            lines.append(f"- {i}. `{r['name']}({r['arguments']})` → "
                         f"`{str(r['result'])[:200]}`")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Relations written")
    for source, target in written:
        marker = "" if tuple(sorted((source, target))) in edge_set else "  (not an edge)"
        lines.append(f"- ({source}, {target}){marker}")
    if not written:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notes")
    parser.add_argument("--characterisations", required=True)
    parser.add_argument("--model", default="qwen2.5:0.5b")
    parser.add_argument("--max-rounds", type=int, default=20)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--channel", choices=["action", "native"], default="action")
    parser.add_argument("--work", default="/tmp/opencode/agent-loop")
    parser.add_argument("--out")
    args = parser.parse_args()

    import json

    notes = load_corpus(args.notes)
    mapping = build_map(notes, progress=lambda *e: None)
    chars = {}
    for line in Path(args.characterisations).read_text().splitlines():
        if line.strip():
            record = json.loads(line)
            chars[record["region"]] = record
    edges = [(e["source"], e["target"]) for e in mapping["edges"]]

    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    path = work / "relations"
    path.unlink(missing_ok=True)

    toolbox = TracingToolbox(mapping, chars, path)
    trace: list[dict] = []

    def on_round(number, total):
        print(f"round {number}/{total}", file=sys.stderr)

    def on_relation(source, target):
        print(f"  relation written: {source}-{target}", file=sys.stderr)

    started = time.monotonic()
    llm = (native_llm(args.model, args.max_tokens, trace) if args.channel == "native"
           else action_llm(args.model, args.max_tokens, trace))
    run = run_agent(
        whole_map_prompt(), toolbox,
        llm=llm,
        max_rounds=args.max_rounds, on_round=on_round, on_relation=on_relation,
    )
    elapsed = time.monotonic() - started
    written = sorted(read_relations(path).values(), key=lambda r: (r["source"], r["target"]))
    written_pairs = [(r["source"], r["target"]) for r in written]

    text = render(trace, toolbox.results, run, written_pairs, edges, elapsed,
                  args.model, args.max_rounds)
    print(f"{args.model}: {len(written_pairs)}/{len(edges)} edges written, "
          f"{run.rounds} rounds, {'stopped' if run.stopped else 'cap'}, "
          f"{elapsed:.0f}s", file=sys.stderr)
    if args.out is None:
        print(text, end="")
    else:
        Path(args.out).write_text(text)


if __name__ == "__main__":
    main()
