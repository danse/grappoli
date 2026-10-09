"""Probe one model on the regions of a corpus, first attempt each.

Stage 2's question: what does the chosen model actually get wrong when
asked to characterise a region? The pipeline retries a malformed answer
(`characterise.py`), which is exactly what hides the failure being
recorded here, so this script sends each region's prompt once and
reports the raw reply, the extraction path (native tool call or content
JSON), and whether the answer validates. It is the instrument behind
`benchmarks/characterisation.md` and the place a Stage 5 model
comparison is taken.

Usage:
    uv run python scripts/benchmark_characterisation.py NOTES
        [--model qwen2.5:0.5b] [--out REPORT.md]
"""

import argparse
import json
import sys
import time
from pathlib import Path

from grappoli.characterise import TOOL_SCHEMA, build_prompt, validate
from grappoli.characterise import InvalidCharacterisation
from grappoli.corpus import load_corpus
from grappoli.map import build_map
from grappoli.model import DEFAULT_MAX_TOKENS, ModelError, parse_content


def _message_dict(message) -> dict:
    """Ollama returns a Message object, not a dict; make it serializable."""
    if hasattr(message, "model_dump"):
        return message.model_dump()
    if hasattr(message, "dict"):
        return message.dict()
    return dict(message)


def probe(region: dict, notes: dict[str, str], model: str) -> dict:
    """One first attempt at one region, raw reply kept."""
    import ollama

    prompt = build_prompt(region["representatives"], notes)
    started = time.monotonic()
    reply = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        tools=[TOOL_SCHEMA],
        format=TOOL_SCHEMA["function"]["parameters"],
        options={"num_predict": DEFAULT_MAX_TOKENS},
    )
    seconds = time.monotonic() - started
    message = _message_dict(reply["message"])
    calls = message.get("tool_calls")

    path = "tool_call" if calls else "content"
    error = None
    if calls:
        candidate = calls[0]["function"].get("arguments")
        if isinstance(candidate, str):
            try:
                candidate = json.loads(candidate)
            except json.JSONDecodeError as err:
                candidate, error = None, f"tool arguments not JSON: {err}"
    else:
        try:
            candidate = parse_content(message.get("content"))
        except ModelError as err:
            candidate, error = None, str(err)

    if error is None:
        try:
            validate(candidate)
        except InvalidCharacterisation as err:
            error = str(err)

    return {
        "region": region["id"],
        "members": region["members"],
        "representatives": region["representatives"],
        "path": path,
        "ok": error is None,
        "error": error,
        "raw": message,
        "seconds": seconds,
        "prompt_tokens": reply.get("prompt_eval_count"),
        "gen_tokens": reply.get("eval_count"),
    }


def render(probes: list[dict], model: str) -> str:
    lines = [f"# Characterisation probe — {model}", ""]
    ok = sum(1 for p in probes if p["ok"])
    fallback = sum(1 for p in probes if p["ok"] and p["path"] == "content")
    lines.append(f"{ok}/{len(probes)} first attempts validated "
                 f"({fallback} via content JSON, the rest via tool call).")
    lines.extend(["", "| region | path | valid | seconds | error |", "|---|---|---|---|---|"])
    for probe_ in probes:
        error = probe_["error"] or ""
        lines.append(f"| {probe_['region']} | {probe_['path']} | "
                     f"{'yes' if probe_['ok'] else 'no'} | {probe_['seconds']:.0f} | {error[:80]} |")
    for probe_ in probes:
        if probe_["ok"]:
            continue
        lines.extend(["", f"## region {probe_['region']} raw reply", "", "```json",
                      json.dumps(probe_["raw"], indent=2), "```"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notes", help="path to the branch of notes")
    parser.add_argument("--model", default="qwen2.5:0.5b")
    parser.add_argument("--limit", type=int, default=None,
                        help="probe only the first N regions (for a quick look)")
    parser.add_argument("--out", default=None, help="write the report here instead of stdout")
    args = parser.parse_args()

    notes = load_corpus(args.notes)
    if not notes:
        print(f"{args.notes}: no markdown notes found", file=sys.stderr)
        sys.exit(1)
    mapping = build_map(notes, progress=lambda *e: None)
    regions = mapping["regions"]
    if args.limit is not None:
        regions = regions[: args.limit]
    probes = []
    for region in regions:
        probe_ = probe(region, notes, args.model)
        print(f"region {probe_['region']}: {'ok' if probe_['ok'] else 'malformed'} "
              f"via {probe_['path']} ({probe_['seconds']:.0f}s)", file=sys.stderr)
        probes.append(probe_)
        # Written after every region, not only at the end: a region takes
        # minutes, and the raw replies are the evidence this script
        # exists to produce. An interrupt must not discard them.
        text = render(probes, args.model)
        if args.out is None:
            print(text, end="")
        else:
            Path(args.out).write_text(text)


if __name__ == "__main__":
    main()
