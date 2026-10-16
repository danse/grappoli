"""Measure generation throughput for one model on one representative request.

The first question: how fast is the model on the kind of prompt the
pipeline will actually send? From the answer, characterisation sizes how
many regions it can afford and the relation loop how many rounds are
safe. The script prints one markdown table row, ready to append to
benchmarks/throughput.md.

Rates come from the timing Ollama itself reports, so they are the
server's own numbers rather than wall-clock around a request.

Usage:
    uv run python scripts/benchmark_throughput.py [--model qwen2.5:0.5b]
                                                [--num-thread N] [--gen 256]
"""

import argparse
import json
import time

import ollama

from grappoli.model import DEFAULT_MODEL

REPRESENTATIVE_PROMPT = """You are mapping a corpus of notes. Give the region
below a characterisation as JSON with keys "about" (one sentence), "topics"
(three to five words or phrases), and "key_claims" (what the notes actually
assert, not what you infer). Base every claim on the notes; do not add
anything you cannot point to. Keep the whole answer under two hundred words.

Notes in this region:

Batch 7: 900 g of small cukes, 1 litre of water, 50 g salt. Warmed the
brine to dissolve the salt, cooled it before pouring. Three days in,
the jar smells right — clean sour, no off notes.

Batch 8: same recipe but I halved the salt (25 g) to see what happens.
Day two already looks livelier, cloudy, tiny bubbles. Tasted at day
four: pleasantly sour but softer texture. Worth repeating with a
proper comparison.

Batch 9: used the 50/50 vinegar brine instead. These are not
ferments — they are pickles in the fridge sense. Different thing
entirely, do not file under the same recipe."""


def measure(model: str = DEFAULT_MODEL, gen: int = 256,
            num_thread: int | None = None) -> dict:
    """One representative generation, and the server's own rates for it.

    The returned dict is the row: `benchmark_all.py` records it as JSON,
    and `render` writes it as the markdown line `throughput.md` holds.
    """
    options = {"num_predict": gen}
    if num_thread is not None:
        options["num_thread"] = num_thread

    started = time.monotonic()
    reply = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": REPRESENTATIVE_PROMPT}],
        options=options,
    )
    wall = time.monotonic() - started

    prompt_count = reply.get("prompt_eval_count", 0)
    eval_count = reply.get("eval_count", 0)
    prompt_seconds = reply.get("prompt_eval_duration", 0) / 1e9
    eval_seconds = reply.get("eval_duration", 0) / 1e9
    return {
        "date": time.strftime("%Y-%m-%d"),
        "model": model,
        "num_thread": num_thread,
        "gen": gen,
        "prompt_tokens": prompt_count,
        "prompt_rate": prompt_count / prompt_seconds if prompt_seconds else 0.0,
        "gen_tokens": eval_count,
        "gen_rate": eval_count / eval_seconds if eval_seconds else 0.0,
        "wall": wall,
    }


def render(row: dict) -> str:
    """One markdown table row, ready to append to benchmarks/throughput.md."""
    thread = f"-t{row['num_thread']}" if row["num_thread"] is not None else ""
    when = row["date"]
    return (f"| {when} | {row['model']}{thread} | {row['prompt_tokens']} "
            f"| {row['prompt_rate']:.1f} | {row['gen_tokens']} | "
            f"{row['gen_rate']:.1f} | {row['wall']:.1f} |")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--num-thread", type=int, default=None,
                        help="override Ollama's thread count; probes the "
                             "thread-starvation hypothesis")
    parser.add_argument("--gen", type=int, default=256,
                        help="max tokens to generate (num_predict)")
    args = parser.parse_args()

    print(render(measure(args.model, args.gen, args.num_thread)))


if __name__ == "__main__":
    main()