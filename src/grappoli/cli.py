"""The `grappoli` command.

* `grappoli read NOTES` — read a branch of notes: build the map
  (Stage 1, arithmetic) and characterise every region (Stage 2, one
  model call per region), in that order. Both stages' working files —
  `map.json` and the append-only `characterisations` — live under
  `NOTES/.grappoli/`, which is not part of what the reader is meant to
  see; the command's own output is progress on stderr.

The map's rule is the built-in default in `grappoli/map.py`, overridden
per-run by the flags; `scripts/benchmark_structure.py` is what re-decides
those defaults against a reference — it reports, a human agrees, the
default changes, and there is no per-corpus settings file. Progress goes
to stderr as plain lines and never into an artefact.

The model is the single interface in `grappoli/model.py`, injected here
so a run can be exercised without Ollama; a region that exhausts its
attempts is logged and skipped, and the run exits non-zero so the
failure is not mistaken for a finished map.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from .characterise import characterise_regions
from .corpus import load_corpus
from .map import build_map
from .model import structured

PROVIDERS = ("bge", "tfidf")


def main(argv=None, *, llm=structured) -> int:
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
    read_cmd.set_defaults(run=_run_read)

    args = parser.parse_args(argv)
    return args.run(args, llm)


def _run_read(args, llm) -> int:
    notes = load_corpus(args.notes)
    if not notes:
        print(f"grappoli: no markdown notes under {args.notes}", file=sys.stderr)
        return 1

    work = Path(args.notes) / ".grappoli"
    work.mkdir(parents=True, exist_ok=True)

    def progress(label, done, total, eta=None):
        suffix = f" (~{_human(eta)} remaining)" if eta is not None else ""
        print(f"{label}: {done}/{total}{suffix}", file=sys.stderr)

    mapping = build_map(
        notes, provider=args.similarity or "bge",
        k=args.k if args.k is not None else 5,
        target=args.target if args.target is not None else 5,
        progress=progress,
    )
    (work / "map.json").write_text(json.dumps(mapping, indent=2) + "\n")

    failed = characterise_regions(
        mapping, notes, work / "characterisations", llm=llm,
        progress=progress, log=lambda line: print(line, file=sys.stderr),
    )

    characterised = len(mapping["regions"]) - len(failed)
    print(f"read {args.notes} — {len(mapping['regions'])} regions "
          f"({characterised} characterised, {len(mapping['standalone'])} standalone notes); "
          f"working files under {work}", file=sys.stderr)
    return 1 if failed else 0


def _human(seconds: float) -> str:
    seconds = int(round(seconds))
    if seconds < 90:
        return f"{seconds}s"
    return f"{seconds // 60}m"
