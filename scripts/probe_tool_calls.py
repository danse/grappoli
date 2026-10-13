"""Find a prompt shape that makes a small model name a tool.

Stage 3's loop stalls on qwen2.5:0.5b because on a real task prompt it
narrates instead of emitting `<tool_call>`; it fires only on a near-literal
"Call the X tool with <args>" command (`benchmarks/relations.md`). The
question this script answers is whether a *cue* can carry real content and
still be taken — so the loop can keep its tool surface.

It sweeps many prompt shapes over a deliberately small entity (one edge,
two short characterisation snippets) at a small cap and temperature 0, so
each case is seconds and a non-firing answer is cut short. The wins, if
any, become the loop's prompt.

Usage:
    uv run python scripts/probe_tool_calls.py NOTES \\
        --characterisations PATH [--model qwen2.5:0.5b] [--suite cues]
        [--cap 64] [--out REPORT.md]

`--suite length` reproduces the earlier note-count sweep instead.
"""

import argparse
import json
import sys
import time
from pathlib import Path

from grappoli.characterise import PROMPT_HEADER, TOOL_SCHEMA, build_prompt
from grappoli.corpus import load_corpus
from grappoli.map import build_map
from grappoli.relations import TOOL_SCHEMAS

WRITE_RELATION = next(s for s in TOOL_SCHEMAS if s["function"]["name"] == "write_relation")


def load_characterisations(path: Path) -> dict[int, dict]:
    records = [json.loads(line) for line in Path(path).read_text().splitlines()
               if line.strip()]
    return {record["region"]: record for record in records}


def length_suite(notes: dict[str, str], region: dict) -> list[tuple[str, list, list]]:
    representatives = region["representatives"]

    def case(count: int):
        label = f"characterise: header + {count} note{'s' if count > 1 else ''}"
        return (label, [{"role": "user", "content": build_prompt(representatives[:count], notes)}],
                [TOOL_SCHEMA])

    counts = sorted({1, 2, len(representatives)})
    return [
        ("characterise: literal cue",
         [{"role": "user", "content":
           "Call the characterise_region tool with about='quick pickles' and topics=['pickles']."}],
         [TOOL_SCHEMA]),
        ("characterise: short phrase",
         [{"role": "user", "content": "You are mapping a corpus. Characterise this region: "
                                     "cucumbers in salt brine, three days, clean sour smell."}],
         [TOOL_SCHEMA]),
        *(case(count) for count in counts),
    ]


def cue_suite(region0: dict, region1: dict, note: str) -> list[tuple[str, list, list]]:
    """Every shape tries to get one relation (0,1) out of the model."""
    about_a, about_b = region0["about"], region1["about"]
    topics_a, topics_b = ", ".join(region0["topics"]), ", ".join(region1["topics"])
    body = f"Region 0: {about_a}\nRegion 1: {about_b}"
    short = f"Region 0: {topics_a}\nRegion 1: {topics_b}"

    def rel(label: str, prompt: str):
        return (label, [{"role": "user", "content": prompt}], [WRITE_RELATION])

    return [
        rel("literal control",
            "Call the write_relation tool with source=0, target=1, "
            "statement='they both use salt'."),
        rel("arguments-related (about)",
            "Call the write_relation tool with arguments related to this text:\n\n" + body),
        rel("arguments-related (topics)",
            "Call the write_relation tool with arguments related to this text:\n\n" + short),
        rel("arguments-related + sentence",
            "Call the write_relation tool with arguments related to this text. "
            "Put your one-sentence statement in 'statement'.\n\n" + short),
        rel("arguments-object",
            "Call the write_relation tool with arguments "
            "{'source': 0, 'target': 1, 'statement': '<one sentence>'}. Regions:\n" + short),
        rel("imperative-now",
            "Call the write_relation tool now, to say how these two regions touch.\n" + short),
        rel("fill-template",
            "Call write_relation(source, target, statement) for regions 0 and 1.\n" + short),
        rel("few-shot",
            "Example: to relate region 0 and region 2 call write_relation with source=0, "
            "target=2, statement='they share temperature'. Now relate region 0 and region 1:\n"
            + short),
        rel("react-tool-list",
            "You must use a tool. Available: write_relation(source, target, statement). "
            "Call it for regions 0 and 1.\n" + short),
        rel("literal-summarise",
            "Call the write_relation tool with source=0, target=1, and a statement "
            "saying how they touch.\n" + body),
        ("system-message",
         [{"role": "system",
           "content": "To record a relation, call write_relation with source, target and statement."},
          {"role": "user", "content": "Relate region 0 and region 1.\n" + short}],
         [WRITE_RELATION]),
        ("characterise: arguments-related",
         [{"role": "user", "content":
           "Call the characterise_region tool with arguments related to this text:\n\n" + note}],
         [TOOL_SCHEMA]),
        ("characterise: header via arguments-related",
         [{"role": "user", "content":
           "Call the characterise_region tool with arguments related to this text:\n\n"
           + PROMPT_HEADER + note}],
         [TOOL_SCHEMA]),
    ]


def probe(messages: list, tools: list, model: str, cap: int, temperature: float) -> dict:
    import ollama

    started = time.monotonic()
    reply = ollama.chat(
        model=model,
        messages=messages,
        tools=tools,
        options={"num_predict": cap, "temperature": temperature},
    )
    message = reply["message"]
    calls = message.get("tool_calls") or []
    return {
        "prompt_tokens": reply.get("prompt_eval_count"),
        "gen_tokens": reply.get("eval_count"),
        "done": reply.get("done_reason"),
        "seconds": time.monotonic() - started,
        "tool_calls": len(calls),
        "call": calls[0]["function"] if calls else None,
        "content": (message.get("content") or "")[:200],
    }


def render(rows: list[tuple[str, dict]], model: str, suite: str) -> str:
    lines = [f"# Tool-call cue sweep ({suite}) — {model}", "",
             "| variant | prompt tok | tool calls | done | gen tok | seconds |",
             "|---|---|---|---|---|---|"]
    for label, row in rows:
        lines.append(f"| {label} | {row['prompt_tokens']} | {row['tool_calls']} | "
                     f"{row['done']} | {row['gen_tokens']} | {row['seconds']:.0f} |")
    lines.append("")
    lines.append("## What each variant returned")
    for label, row in rows:
        lines.append("")
        lines.append(f"### {label}")
        if row["call"]:
            lines.append(f"tool: `{row['call']['name']}({row['call']['arguments']})`")
        else:
            lines.append(f"content: `{row['content']}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notes")
    parser.add_argument("--characterisations")
    parser.add_argument("--model", default="qwen2.5:0.5b")
    parser.add_argument("--suite", choices=("cues", "length"), default="cues")
    parser.add_argument("--region", type=int, default=0)
    parser.add_argument("--cap", type=int, default=160)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--only", default=None,
                        help="comma-separated substrings; run only matching variants")
    parser.add_argument("--out")
    args = parser.parse_args()

    notes = load_corpus(args.notes)
    mapping = build_map(notes, progress=lambda *e: None)
    if args.suite == "length":
        cases = length_suite(notes, mapping["regions"][args.region])
    else:
        if not args.characterisations:
            parser.error("--characterisations is required for the cues suite")
        chars = load_characterisations(args.characterisations)
        note = notes[mapping["regions"][args.region]["representatives"][0]]
        cases = cue_suite(chars[0], chars[1], note)

    if args.only:
        wanted = [s.strip().lower() for s in args.only.split(",") if s.strip()]
        cases = [case for case in cases if any(w in case[0].lower() for w in wanted)]

    rows = []
    for label, messages, tools in cases:
        row = probe(messages, tools, args.model, args.cap, args.temperature)
        print(f"{label}: {row['tool_calls']} tool calls, done={row['done']} "
              f"({row['seconds']:.0f}s)", file=sys.stderr)
        rows.append((label, row))
        text = render(rows, args.model, args.suite)
        if args.out is None:
            print(text, end="")
        else:
            Path(args.out).write_text(text)


if __name__ == "__main__":
    main()
