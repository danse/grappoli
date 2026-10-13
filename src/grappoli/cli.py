"""The `grappoli` command.

* `grappoli read NOTES` — read a branch of notes: build the map
  (Stage 1, arithmetic), characterise every region (Stage 2, one model
  call per region), then relate the touching pairs (Stage 3, one agent
  loop), in that order. The stages' working files — `map.json`, the
  append-only `characterisations` and the append-only `relations` — live
  under `NOTES/.grappoli/`, which is not part of what the reader is meant
  to see; the command's own output is progress on stderr.

The map's rule is the built-in default in `grappoli/map.py`, overridden
per-run by the flags; `scripts/benchmark_structure.py` is what re-decides
those defaults against a reference — it reports, a human agrees, the
default changes, and there is no per-corpus settings file. Progress goes
to stderr as plain lines and never into an artefact.

The model is the single interface in `grappoli/model.py`, injected here
so a run can be exercised without Ollama: `structured` for Stage 2 and
`converse` for the Stage 3 loop, both bound to `--model`. A region that
exhausts its attempts is logged and skipped, and the run exits non-zero
so the failure is not mistaken for a finished map; a loop that stops with
pairs still unrelating does the same, since the build is then partial.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from .characterise import characterise_regions, read_characterisations
from .corpus import load_corpus
from .map import build_map
from .model import converse, structured
from .relations import read_relations, relate_regions

PROVIDERS = ("bge", "tfidf")


def main(argv=None, *, llm=structured, agent_llm=converse) -> int:
    # Weights are part of this machine's environment; a cached model
    # must not fight DNS on every run (observed during Stage 1). Offline
    # by default; HF_HUB_OFFLINE=0 forces a re-fetch.
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    parser = argparse.ArgumentParser(prog="grappoli", description="Map a branch of notes.")
    sub = parser.add_subparsers(dest="command", required=True)

    read_cmd = sub.add_parser("read", help="read a branch of notes into a map")
    read_cmd.add_argument("notes", help="path to the branch of notes")
    read_cmd.add_argument("--similarity", choices=PROVIDERS,
                          help="similarity provider (default: bge)")
    read_cmd.add_argument("-k", type=int, help="neighbourhood size (default: 5)")
    read_cmd.add_argument("--target", type=int, help="representatives per region (default: 5)")
    read_cmd.add_argument("--model", help="generation model (default: qwen2.5:0.5b)")
    read_cmd.set_defaults(run=_run_read)

    args = parser.parse_args(argv)
    return args.run(args, llm, agent_llm)


def _with_model(llm, model):
    """Bind an explicit model name, or leave the interface's default."""
    if model is None:
        return llm
    return lambda *args, **kwargs: llm(*args, model=model, **kwargs)


def _run_read(args, llm, agent_llm) -> int:
    llm = _with_model(llm, args.model)
    agent_llm = _with_model(agent_llm, args.model)
    notes = load_corpus(args.notes)
    if not notes:
        print(f"grappoli: no markdown notes under {args.notes}", file=sys.stderr)
        return 1

    work = Path(args.notes) / ".grappoli"
    work.mkdir(parents=True, exist_ok=True)

    def progress(label, done, total, eta=None):
        suffix = f" (~{_human(eta)} remaining)" if eta is not None else ""
        print(f"{label}: {done}/{total}{suffix}", file=sys.stderr)

    def log(line):
        print(line, file=sys.stderr)

    mapping = build_map(
        notes, provider=args.similarity or "bge",
        k=args.k if args.k is not None else 5,
        target=args.target if args.target is not None else 5,
        progress=progress,
    )
    (work / "map.json").write_text(json.dumps(mapping, indent=2) + "\n")

    failed = characterise_regions(
        mapping, notes, work / "characterisations", llm=llm,
        progress=progress, log=log,
    )

    missing = relate_regions(
        mapping, read_characterisations(work / "characterisations"),
        work / "relations", llm=agent_llm, progress=progress, log=log,
    )

    characterised = len(mapping["regions"]) - len(failed)
    print(f"read {args.notes} — {len(mapping['regions'])} regions "
          f"({characterised} characterised, {len(mapping['standalone'])} standalone notes), "
          f"{len(read_relations(work / 'relations'))} relations; "
          f"working files under {work}", file=sys.stderr)
    return 1 if (failed or missing) else 0


def _human(seconds: float) -> str:
    seconds = int(round(seconds))
    if seconds < 90:
        return f"{seconds}s"
    return f"{seconds // 60}m"
