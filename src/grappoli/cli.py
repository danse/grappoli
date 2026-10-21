"""The `grappoli` command.

* `grappoli read NOTES` — read a branch of notes: build the map
  (arithmetic), characterise every region (one model call per region),
  then relate the touching pairs (one call per pair), in that order. The
  pipeline's working files — `map.json`, the append-only
  `characterisations` and the append-only `relations` — live under
  `NOTES/.grappoli/`, which is not part of what the reader is meant
  to see; the command's own output is progress on stderr.
* `grappoli measure NOTES` — score a map already built there: the four
  measurements, read from the same working files. It builds nothing,
  so it measures the candidate the branch holds; `--reference` scores
  structure match, without which that one number is not produced.
* `grappoli show NOTES` — print the page a reader reads: `render` of the
  same three working files, to stdout. It makes no model call and writes
  nothing, so it can be run again and again on one build.

The map's rule is the built-in default in `grappoli/map.py`, overridden
per-run by the flags; `scripts/benchmark_structure.py` is what re-decides
those defaults against a reference — it reports, a human agrees, the
default changes, and there is no per-corpus settings file. Progress goes
to stderr as plain lines and never into an artefact.

The model is the single interface in `grappoli/model.py`, injected here
so a run can be exercised without Ollama: `structured` for
characterisation, for the pair loop the relation step asks, and for the
model-backed faithfulness judge; `converse` for the native channel, the
one tool conversation over the whole map, which `--relation-channel
native` selects. All are bound to `--model`. `measure` judges with the
decoupled NLI cross-encoder by default — a judge that is not the model
under test — and `--judge llm` puts that model in the seat instead. A
region that exhausts its attempts is logged and skipped, and the run exits
non-zero so the failure is not mistaken for a finished map; a loop that
stops with pairs still unrelating does the same, since the build is then
partial. `measure` and `show` report on stdout, since a measurement and a
page are not progress.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from .characterise import characterise_regions, read_characterisations
from .corpus import load_corpus
from .map import build_map
from .measure import measure as measure_map
from .measure import nli_judge
from .model import converse, structured
from .relations import read_relations, relate_pairs, relate_regions
from .render import render
from .words import stopwords

PROVIDERS = ("e5", "tfidf")


class JudgeUnavailable(Exception):
    """The decoupled judge could not be built — its weights are not there."""


def main(argv=None, *, llm=structured, agent_llm=converse, compare=None) -> int:
    # Weights are part of this machine's environment; a cached model
    # must not fight DNS on every run (observed while building maps). Offline
    # by default; HF_HUB_OFFLINE=0 forces a re-fetch.
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    parser = argparse.ArgumentParser(prog="grappoli", description="Map a branch of notes.")
    sub = parser.add_subparsers(dest="command", required=True)

    read_cmd = sub.add_parser("read", help="read a branch of notes into a map")
    read_cmd.add_argument("notes", help="path to the branch of notes")
    read_cmd.add_argument("--similarity", choices=PROVIDERS,
                          help="similarity provider (default: e5)")
    read_cmd.add_argument("-k", type=int, help="neighbourhood size (default: 4)")
    read_cmd.add_argument("--target", type=int, help="representatives per region (default: 5)")
    read_cmd.add_argument("--model", help="generation model (default: llama3.2:latest)")
    read_cmd.add_argument("--relation-channel", choices=("native", "structured"),
                          default="structured",
                          help="how the relation loop asks the model: one call a "
                               "pair (structured, the default), or one tool "
                               "conversation over the whole map (native)")
    read_cmd.set_defaults(run=_run_read)

    measure_cmd = sub.add_parser("measure", help="score the map built under NOTES/.grappoli")
    measure_cmd.add_argument("notes", help="path to the branch of notes")
    measure_cmd.add_argument("--reference",
                             help="reference regions to score structure match against "
                                  "(same shape as tests/fixtures/in-domain/reference-regions.json)")
    measure_cmd.add_argument("--model",
                             help="judge model under --judge llm (default: llama3.2:latest)")
    measure_cmd.add_argument("--judge", choices=("nli", "llm"), default="nli",
                             help="faithfulness judge: the decoupled NLI "
                                  "cross-encoder (nli, the default) or the model "
                                  "under test (llm)")
    measure_cmd.set_defaults(run=_run_measure)

    show_cmd = sub.add_parser("show", help="print the map built under NOTES/.grappoli for a reader")
    show_cmd.add_argument("notes", help="path to the branch of notes")
    show_cmd.set_defaults(run=_run_show)

    args = parser.parse_args(argv)
    args.compare = compare
    return args.run(args, llm, agent_llm)


def _with_model(llm, model):
    """Bind an explicit model name, or leave the interface's default."""
    if model is None:
        return llm
    return lambda *args, **kwargs: llm(*args, model=model, **kwargs)


def _judge_for(name: str):
    """The faithfulness judge the flag names, built when the first claim is judged.

    `nli` is the decoupled NLI cross-encoder and `llm` is the model under
    test, which the measurement reaches through `llm` itself and so is
    left as `None` here. The cross-encoder is built on first use: a
    measurement that fails before it judges a claim — no map, a reference
    with no label for a note — then reports that error without loading the
    weights, and a run whose checkpoint is not cached says what to fetch
    rather than failing with a loader's traceback.
    """
    if name != "nli":
        return None

    built = []

    def judge(claim, evidence):
        if not built:
            try:
                built.append(nli_judge())
            except OSError as err:
                raise JudgeUnavailable(str(err)) from err
        return built[0](claim, evidence)

    return judge


def _run_read(args, llm, agent_llm) -> int:
    llm = _with_model(llm, args.model)
    agent_llm = _with_model(agent_llm, args.model)
    notes = load_corpus(args.notes)
    if not notes:
        print(f"grappoli: no notes under {args.notes}", file=sys.stderr)
        return 1

    work = Path(args.notes) / ".grappoli"
    work.mkdir(parents=True, exist_ok=True)

    def progress(label, done, total, eta=None):
        suffix = f" (~{_human(eta)} remaining)" if eta is not None else ""
        print(f"{label}: {done}/{total}{suffix}", file=sys.stderr)

    def log(line):
        print(line, file=sys.stderr)

    mapping = build_map(
        notes, provider=args.similarity or "e5",
        k=args.k if args.k is not None else 4,
        target=args.target if args.target is not None else 5,
        progress=progress,
    )
    (work / "map.json").write_text(json.dumps(mapping, indent=2) + "\n")

    failed = characterise_regions(
        mapping, notes, work / "characterisations", llm=llm,
        progress=progress, log=log,
    )

    characterisations = read_characterisations(work / "characterisations")
    if args.relation_channel == "structured":
        missing = relate_pairs(
            mapping, characterisations, work / "relations",
            llm=llm, progress=progress, log=log,
        )
    else:
        missing = relate_regions(
            mapping, characterisations, work / "relations",
            stop=stopwords(notes.values()),
            llm=agent_llm, progress=progress, log=log,
        )
    characterised = len(mapping["regions"]) - len(failed)
    print(f"read {args.notes} — {len(mapping['regions'])} regions "
          f"({characterised} characterised, {len(mapping['standalone'])} standalone notes), "
          f"{len(read_relations(work / 'relations'))} relations; "
          f"working files under {work}", file=sys.stderr)
    return 1 if (failed or missing) else 0


def _run_measure(args, llm, agent_llm) -> int:
    llm = _with_model(llm, args.model)
    notes = load_corpus(args.notes)
    if not notes:
        print(f"grappoli: no notes under {args.notes}", file=sys.stderr)
        return 1

    work = Path(args.notes) / ".grappoli"
    map_path = work / "map.json"
    if not map_path.exists():
        print(f"grappoli: no map under {work} — run `grappoli read {args.notes}` first",
              file=sys.stderr)
        return 1
    mapping = json.loads(map_path.read_text())
    characterisations = read_characterisations(work / "characterisations")

    def progress(label, done, total):
        print(f"{label}: {done}/{total}", file=sys.stderr)

    def log(line):
        print(line, file=sys.stderr)

    reference = Path(args.reference) if args.reference else None
    judge = _judge_for(args.judge)
    try:
        result = measure_map(mapping, characterisations, notes, reference,
                             llm=llm, judge=judge, compare=args.compare,
                             progress=progress, log=log)
    except ValueError as err:
        print(f"grappoli: {err}", file=sys.stderr)
        return 1
    except JudgeUnavailable as err:
        print(f"grappoli: the NLI judge could not be loaded ({err}). Fetch it "
              "once with HF_HUB_OFFLINE=0, or judge with the model under "
              "test: --judge llm.", file=sys.stderr)
        return 1
    print(_report(result))
    return 0


def _run_show(args, llm, agent_llm) -> int:
    """Print the page for the map already built under `NOTES/.grappoli`.

    Nothing is built and no model is asked: the three working files are
    read and `render` is printed, so the command is a view of one build
    (`architecture.md`, The document).
    """
    work = Path(args.notes) / ".grappoli"
    map_path = work / "map.json"
    if not map_path.exists():
        print(f"grappoli: no map under {work} — run `grappoli read {args.notes}` first",
              file=sys.stderr)
        return 1
    mapping = json.loads(map_path.read_text())
    characterisations = read_characterisations(work / "characterisations")
    relations = read_relations(work / "relations")
    print(render(mapping, characterisations, relations))
    return 0


def _report(result: dict) -> str:
    """The four numbers as a reader reads them, with what each rests on."""
    detail = result["faithfulness_detail"]
    lines = [
        f"notes: {result['notes']}  regions: {result['regions']}  "
        f"standalone: {result['standalone']}",
        f"comprehensiveness: {result['comprehensiveness']:.3f}",
        f"redundancy: {result['redundancy']:.3f}",
    ]
    if result["faithfulness"] is None:
        lines.append(f"faithfulness: n/a ({detail['total']} claims, none judged)")
    else:
        judged = detail["supported"] + detail["unsupported"]
        line = (f"faithfulness: {result['faithfulness']:.3f} "
                f"({detail['supported']}/{judged} claims supported")
        if detail["undecided"]:
            line += f", {detail['undecided']} undecided"
        lines.append(line + ")")
    if result["structure_match"] is None:
        lines.append("structure match: n/a (no reference given)")
    else:
        lines.append(f"structure match: {result['structure_match']:.3f} "
                     f"(against {result['reference']})")
    return "\n".join(lines)


def _human(seconds: float) -> str:
    seconds = int(round(seconds))
    if seconds < 90:
        return f"{seconds}s"
    return f"{seconds // 60}m"
