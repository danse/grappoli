"""The `grappoli` command.

* `grappoli map NOTES` — build map.json from a branch of notes, with the
  rule the structure benchmark has so far decided (the built-in
  defaults in grappoli/map.py), overridden per-run by the flags.
  `scripts/benchmark_structure.py` is what re-decides those defaults
  against a reference — it reports, a human agrees, the default
  changes; there is no per-corpus settings file. Progress goes to
  stderr as plain lines (label, done, total) and never into the map.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from .corpus import load_corpus
from .map import build_map

PROVIDERS = ("bge", "tfidf")


def main(argv=None) -> int:
    # Weights are part of this machine's environment; a cached model
    # must not fight DNS on every run (observed during Stage 1). Offline
    # by default; HF_HUB_OFFLINE=0 forces a re-fetch.
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    parser = argparse.ArgumentParser(prog="grappoli", description="Map a branch of notes.")
    sub = parser.add_subparsers(dest="command", required=True)

    map_cmd = sub.add_parser("map", help="build map.json from a branch of notes")
    map_cmd.add_argument("notes", help="path to the branch of notes")
    map_cmd.add_argument("--similarity", choices=PROVIDERS,
                         help="similarity provider (default: bge)")
    map_cmd.add_argument("-k", type=int, help="neighbourhood size (default: 5)")
    map_cmd.add_argument("--target", type=int, help="representatives per region (default: 5)")
    map_cmd.add_argument("-o", "--out", default="map.json")
    map_cmd.set_defaults(run=_run_map)

    args = parser.parse_args(argv)
    return args.run(args)


def _run_map(args) -> int:
    notes = load_corpus(args.notes)
    if not notes:
        print(f"grappoli: no markdown notes under {args.notes}", file=sys.stderr)
        return 1

    def progress(label, done, total):
        print(f"{label}: {done}/{total}", file=sys.stderr)

    mapping = build_map(
        notes, provider=args.similarity or "bge",
        k=args.k if args.k is not None else 5,
        target=args.target if args.target is not None else 5,
        progress=progress,
    )
    out = Path(args.out)
    out.write_text(json.dumps(mapping, indent=2) + "\n")
    print(f"wrote {out} — {len(mapping['regions'])} regions, "
          f"{len(mapping['edges'])} relations, {len(mapping['standalone'])} standalone notes")
    return 0