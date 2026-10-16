"""Run every pipeline-step benchmark once, and record the results as JSON.

The steps were measured one at a time, each with its own script and its
own markdown record. Deciding what is left needs them read together, so
this runs them in one batch — structure, throughput, characterisation,
the relation task, a real `grappoli read` per model, and `grappoli
measure` — and writes everything to one pretty-printed JSON, under
`benchmarks/runs/<date>/`, to be formatted into the step records and
committed as the reference for the decisions.

It is only the batch: every number is still its own script's or its own
measure's, and nothing here picks a model or a default. The only new
behaviour is the record's shape and that a run resumes.

The report is keyed by step, then corpus, then model (then judge, for
`measure`). Each entry is written as soon as it completes, and an entry
already present is skipped, so an interrupted overnight run resumes at
the first missing one instead of at the start; `--force` throws the
record away and runs the lot again. The corpus is copied to `--work`
before it is built in, because a fixture is never written to and two
models' working files must not mix.

The structure sweep is arithmetic; the other steps need Ollama and take
hours. The instruments are the sibling scripts, loaded by path so their
own command lines keep working; a test substitutes the whole set.

Usage:
    uv run python scripts/benchmark_all.py
        [--corpus tests/fixtures/in-domain/notes] [--corpus …/heterogeneous/notes]
        [--models qwen2.5:0.5b,llama3.2:latest]
        [--judges qwen2.5:0.5b,llama3.2:latest]
        [--work /tmp/opencode/suite] [--out benchmarks/runs/YYYY-MM-DD/run.json] [--force]
"""

import argparse
import functools
import importlib.util
import inspect
import json
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from grappoli.characterise import read_characterisations
from grappoli.corpus import load_corpus
from grappoli.map import build_map
from grappoli.measure import REDUNDANCY_MODEL, REDUNDANCY_THRESHOLD
from grappoli.model import DEFAULT_MAX_TOKENS, DEFAULT_MODEL, structured
from grappoli.relations import read_relations

STEPS = ("structure", "throughput", "characterisation", "read", "relations", "measure")
DEFAULT_MODELS = ("qwen2.5:0.5b", "llama3.2:latest")
DEFAULT_JUDGE = "llama3.2:latest"
DEFAULT_CORPORA = ("tests/fixtures/in-domain/notes", "tests/fixtures/heterogeneous/notes")

_SCRIPTS: dict = {}


@dataclass(frozen=True)
class Corpus:
    """One branch of notes, and the reference map beside it if there is one."""

    name: str
    path: Path
    reference: Path | None

    @classmethod
    def discover(cls, path) -> "Corpus":
        """Name a corpus and find the reference that sits with it.

        The fixture shape is `<corpus>/notes/` with `reference-regions.json`
        beside `notes/`; a plain directory with the reference inside it
        works too. The name is the corpus's, not the `notes/` leaf's.
        """
        path = Path(path)
        name = path.parent.name if path.name == "notes" and path.parent.name else path.name
        for candidate in (path / "reference-regions.json", path.parent / "reference-regions.json"):
            if candidate.is_file():
                return cls(name, path, candidate)
        return cls(name, path, None)


def _script(name: str):
    """Load a sibling benchmark script by path (`scripts/` is not a package)."""
    if name not in _SCRIPTS:
        path = Path(__file__).with_name(f"{name}.py")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _SCRIPTS[name] = module
    return _SCRIPTS[name]


def _slug(text: str) -> str:
    return text.replace(":", "-").replace("/", "-")


def _stage(corpus: Corpus, model: str, work_root: Path) -> Path:
    """A private copy of the corpus to build in; the fixture is left alone.

    The copy is keyed by model, because a `grappoli read` writes the
    model's characterisations into the branch's `.grappoli/` and two
    models' records must not end up in the same file.
    """
    work = work_root / f"{corpus.name}--{_slug(model)}"
    if not work.exists():
        work_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(corpus.path, work)
    return work


def _read_summary(work: Path, exit_code: int, seconds: float) -> dict:
    """What a `grappoli read` left in `work`, as the record keeps it."""
    grappoli = work / ".grappoli"
    mapping = json.loads((grappoli / "map.json").read_text())
    characterisations = read_characterisations(grappoli / "characterisations")
    relations = read_relations(grappoli / "relations")
    relatable = sorted({
        (min(edge["source"], edge["target"]), max(edge["source"], edge["target"]))
        for edge in mapping["edges"]
        if edge["source"] in characterisations and edge["target"] in characterisations
    })
    return {
        "exit": exit_code,
        "seconds": seconds,
        "regions": len(mapping["regions"]),
        "standalone": len(mapping["standalone"]),
        "characterised": len(characterisations),
        "failed": [r["id"] for r in mapping["regions"] if r["id"] not in characterisations],
        "relations": len(relations),
        "relatable": len(relatable),
        "missing": [list(pair) for pair in relatable if pair not in relations],
    }


def runners(work_root: Path) -> dict:
    """The instrument behind each step, as `run` calls it.

    Every runner takes `(corpus, model, judge)` by keyword and ignores
    what it does not use, so the engine calls them all the same way.
    Kept in one place so a test can substitute the whole set and pin the
    record's shape without Ollama.
    """
    work_root = Path(work_root)

    def structure(corpus, model=None, judge=None):
        return _script("benchmark_structure").sweep(load_corpus(corpus.path), corpus.reference)

    def throughput(corpus=None, model=None, judge=None):
        return _script("benchmark_throughput").measure(model)

    def characterisation(corpus, model=None, judge=None):
        return _script("benchmark_characterisation").sweep(load_corpus(corpus.path), model)

    def read(corpus, model=None, judge=None):
        work = _stage(corpus, model, work_root)
        from grappoli.cli import main as cli_main

        started = time.monotonic()
        exit_code = cli_main(["read", str(work), "--model", model])
        return _read_summary(work, exit_code, time.monotonic() - started)

    def relations(corpus, model=None, judge=None):
        work = _stage(corpus, model, work_root)
        script = _script("benchmark_relations")
        characters_path = work / ".grappoli" / "characterisations"
        notes = load_corpus(work)
        return {
            channel: script.sweep(notes, characters_path, model, channel=channel)
            for channel in ("native", "structured")
        }

    def measure(corpus, model=None, judge=None):
        from grappoli.measure import measure as measure_map

        work = _stage(corpus, model, work_root)
        grappoli = work / ".grappoli"
        mapping = json.loads((grappoli / "map.json").read_text())
        characterisations = read_characterisations(grappoli / "characterisations")
        llm = functools.partial(structured, model=judge)
        return measure_map(mapping, characterisations, load_corpus(work),
                           reference=corpus.reference, llm=llm)

    return {"structure": structure, "throughput": throughput,
            "characterisation": characterisation, "read": read,
            "relations": relations, "measure": measure}


def _meta(corpora, models, judges) -> dict:
    """What the run was, so the JSON needs no other file beside it."""
    defaults = {
        name: parameter.default
        for name, parameter in inspect.signature(build_map).parameters.items()
        if parameter.default is not inspect.Parameter.empty
    }
    return {
        "date": date.today().isoformat(),
        "command": " ".join(sys.argv),
        "models": list(models),
        "judges": list(judges),
        "defaults": {
            "build_map": defaults,
            "model": DEFAULT_MODEL,
            "max_tokens": DEFAULT_MAX_TOKENS,
            "redundancy_model": REDUNDANCY_MODEL,
            "redundancy_threshold": REDUNDANCY_THRESHOLD,
        },
        "corpora": {
            corpus.name: {
                "path": str(corpus.path),
                "reference": str(corpus.reference) if corpus.reference else None,
                "notes": len(load_corpus(corpus.path)),
            }
            for corpus in corpora
        },
    }


def run(corpora, models, judges, out, *, runners, log=print, force=False, meta=None) -> dict:
    """Run the batch into `out`, skipping entries already recorded there.

    The report is keyed by step, then corpus, then model (then judge for
    `measure`), and is written after every entry: an interrupt leaves a
    readable partial record and a rerun resumes at the first missing one.
    `meta` describes the run, not the invocation, so it is set only on a
    fresh record: a resume keeps the date and the command the run began
    with, even across midnight, rather than stamping the rerun's.
    """
    out = Path(out)
    if force or not out.is_file():
        report: dict = {}
    else:
        report = json.loads(out.read_text())
    if meta is not None and "meta" not in report:
        report["meta"] = meta
    for step in STEPS:
        report.setdefault(step, {})

    def done(*keys) -> bool:
        node = report
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return False
            node = node[key]
        return True

    def record(value, *keys) -> None:
        node = report
        for key in keys[:-1]:
            node = node.setdefault(key, {})
        node[keys[-1]] = value
        _write(out, report)
        log(f"recorded {'/'.join(keys)}")

    for corpus in corpora:
        if not done("structure", corpus.name):
            record(runners["structure"](corpus=corpus), "structure", corpus.name)
    for model in models:
        if not done("throughput", model):
            record(runners["throughput"](model=model), "throughput", model)
    for corpus in corpora:
        for model in models:
            if not done("characterisation", corpus.name, model):
                record(runners["characterisation"](corpus=corpus, model=model),
                       "characterisation", corpus.name, model)
            if not done("read", corpus.name, model):
                record(runners["read"](corpus=corpus, model=model),
                       "read", corpus.name, model)
            if not done("relations", corpus.name, model):
                record(runners["relations"](corpus=corpus, model=model),
                       "relations", corpus.name, model)
            for judge in judges:
                if not done("measure", corpus.name, model, judge):
                    record(runners["measure"](corpus=corpus, model=model, judge=judge),
                           "measure", corpus.name, model, judge)
    return report


def _write(out: Path, report: dict) -> None:
    """Write the report through a temp file; the next run reads it to resume."""
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = out.with_name(out.name + ".tmp")
    temp.write_text(json.dumps(report, indent=2) + "\n")
    temp.replace(out)


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _unique(items) -> list[str]:
    seen: list[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", action="append", default=None,
                        help="notes directory, repeatable; a reference-regions.json "
                             "beside it is scored against if present "
                             f"(default: {', '.join(DEFAULT_CORPORA)})")
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS),
                        help="comma-separated generation models")
    parser.add_argument("--judges", default=None,
                        help="comma-separated faithfulness judges "
                             f"(default: the models plus {DEFAULT_JUDGE})")
    parser.add_argument("--work", default="/tmp/opencode/suite",
                        help="where corpus copies are built; not part of the record")
    parser.add_argument("--out", default=None,
                        help="the JSON record (default: benchmarks/runs/<date>/run.json)")
    parser.add_argument("--force", action="store_true",
                        help="throw the existing record away and run every step again")
    args = parser.parse_args(argv)

    corpora = [Corpus.discover(path) for path in (args.corpus or DEFAULT_CORPORA)]
    models = _split(args.models)
    judges = _split(args.judges) if args.judges else _unique([*models, DEFAULT_JUDGE])
    out = (Path(args.out) if args.out
           else Path("benchmarks") / "runs" / date.today().isoformat() / "run.json")

    def log(line):
        print(f"[{time.strftime('%H:%M:%S')}] {line}", file=sys.stderr, flush=True)

    report = run(corpora, models, judges, out, runners=runners(args.work),
                 log=log, force=args.force, meta=_meta(corpora, models, judges))
    log(f"wrote {out} ({len(json.dumps(report))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
