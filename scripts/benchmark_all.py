"""Run every pipeline-step benchmark once, and record the results as JSON.

The steps were measured one at a time, each with its own script and its
own markdown record. Deciding what is left needs them read together, so
this runs them in one batch — structure, throughput, characterisation,
the relation task, a real `grappoli read` per model, the pair loop over
each cell's touching pairs, and `grappoli measure` — and writes
everything to one pretty-printed JSON, under `benchmarks/runs/<date>/`,
to be formatted into the step records and committed as the reference for
the decisions.

It is only the batch: every number is still its own script's or its own
measure's, and nothing here picks a model or a default. The only new
behaviour is the record's shape and that a run resumes.

The report is keyed by step, then corpus, then model (then judge, for
`measure` and for the relation loop). Each entry is written as soon as it
completes, and an entry already present is skipped, so an interrupted
overnight run resumes at the first missing one instead of at the start;
`--force` throws the record away and runs the lot again. The corpus is
copied to `--work` before it is built in, because a fixture is never
written to and two models' working files must not mix.

The structure sweep is arithmetic; the other steps need Ollama and take
hours. The instruments are the sibling scripts, loaded by path so their
own command lines keep working; a test substitutes the whole set.

Usage:
    uv run python scripts/benchmark_all.py
        [--corpus tests/fixtures/in-domain/notes] [--corpus …/heterogeneous/notes]
        [--corpus …/multilingual/notes]
        [--models qwen2.5:0.5b,llama3.2:latest]
        [--judges nli]
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

from grappoli.characterise import characterise_regions, read_characterisations
from grappoli.corpus import load_corpus
from grappoli.map import build_map
from grappoli.measure import (
    NLI_MODEL,
    NLI_THRESHOLD,
    REDUNDANCY_MODEL,
    REDUNDANCY_THRESHOLD,
    judge_claim,
    nli_judge,
)
from grappoli.model import DEFAULT_MAX_TOKENS, DEFAULT_MODEL, structured
from grappoli.relations import read_relations

STEPS = ("structure", "throughput", "characterisation", "read", "relations",
         "relation_loop", "measure")
# The comparison the batch runs by default: the two models that characterise
# every region and relate every touching pair — `llama3.2:latest`, the
# shipped default, and `qwen2.5:0.5b`, the smaller one it is compared
# against — over the three corpora.
# The tool-trained pair added for the relation loop's tool choice did not
# drive it and doubled the run; `--models` still runs them.
DEFAULT_MODELS = (
    "qwen2.5:0.5b",
    "llama3.2:latest",
)
# `nli` names the decoupled NLI cross-encoder; anything else names a
# generation model, judged through the model interface. The default is the
# decoupled judge, because the model-backed judges are the model under test
# (`benchmarks/measurement.md`).
NLI_JUDGE = "nli"
DEFAULT_JUDGES = (NLI_JUDGE,)
DEFAULT_CORPORA = (
    "tests/fixtures/in-domain/notes",
    "tests/fixtures/heterogeneous/notes",
    "tests/fixtures/multilingual/notes",
)

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


def _judge_for(name: str) -> dict:
    """The keyword `measure` takes for the judge `name` names.

    `nli` is the decoupled NLI cross-encoder; anything else names a
    generation model, judged through the model interface. Kept here so the
    judge choice is one place and a test pins it without loading a model.
    """
    if name == NLI_JUDGE:
        return {"judge": nli_judge()}
    return {"llm": functools.partial(structured, model=name)}


def _claim_judge_for(name: str):
    """One callable that judges a claim against its evidence.

    `measure` takes the two judges apart — the NLI cross-encoder as
    `judge`, a generation model as `llm` — because it also measures
    without a judge. A relation statement is a claim about two regions,
    so the relation step wants the two as one: `(claim, evidence) ->
    verdict`. The NLI judge is the decoupled one; a generation model is
    the model under test, which is a limit and not a hidden one.
    """
    if name == NLI_JUDGE:
        return nli_judge()
    return functools.partial(judge_claim, llm=functools.partial(structured, model=name))


def _prepared(model: str, work: Path) -> tuple[dict, dict, dict]:
    """The map, the characterisations and the notes the pair loop reads.

    The `read` step leaves both working files in the copy it built, so
    these are that model's own map and characterisations; a copy that
    holds neither — a run resumed after the work directory was cleared —
    is given them here, because the loop has nothing to read without
    them and a step that cannot run leaves a hole in the record.
    """
    grappoli = work / ".grappoli"
    notes = load_corpus(work)
    map_path = grappoli / "map.json"
    if not map_path.is_file():
        mapping = build_map(notes, progress=lambda *e: None)
        map_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.write_text(json.dumps(mapping, indent=2) + "\n")
    mapping = json.loads(map_path.read_text())
    characters_path = grappoli / "characterisations"
    if not characters_path.is_file():
        characterise_regions(mapping, notes, characters_path,
                             llm=functools.partial(structured, model=model))
    return mapping, read_characterisations(characters_path), notes


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

    def relation_loop(corpus, model=None, judge=None):
        """The pair loop over the cell's touching pairs, and what it wrote.

        The loop runs on the copy the `read` step built, so the
        characterisations are that model's own. Its relations go to a file
        of their own, `relations-loop`, because the file the `read` step
        left is what that step recorded and the loop's statements are
        this step's measurement.

        The statements are judged by the judge the run names, as the
        claims of a characterisation are: a relation is a claim about two
        regions, and the evidence is the notes of both.
        """
        work = _stage(corpus, model, work_root)
        script = _script("benchmark_relation_loop")
        mapping, characters, notes = _prepared(model, work)
        return script.run(notes, characters, model, mapping=mapping,
                          relations_path=work / ".grappoli" / "relations-loop",
                          judge=_claim_judge_for(judge),
                          log=lambda line: print(line, file=sys.stderr, flush=True))

    def measure(corpus, model=None, judge=None):
        from grappoli.measure import measure as measure_map

        work = _stage(corpus, model, work_root)
        grappoli = work / ".grappoli"
        mapping = json.loads((grappoli / "map.json").read_text())
        characterisations = read_characterisations(grappoli / "characterisations")
        started = time.monotonic()
        result = measure_map(mapping, characterisations, load_corpus(work),
                             reference=corpus.reference, **_judge_for(judge))
        # The seconds are the measurement's own cost, the judge included:
        # the decoupled judge is the default, and what it costs is a
        # number the record carries rather than a question left to a
        # live run.
        result["seconds"] = time.monotonic() - started
        return result

    return {"structure": structure, "throughput": throughput,
            "characterisation": characterisation, "read": read,
            "relations": relations, "relation_loop": relation_loop,
            "measure": measure}


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
            "nli_model": NLI_MODEL,
            "nli_threshold": NLI_THRESHOLD,
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
    `measure` and for the relation loop), and is written after every
    entry: an interrupt leaves a readable partial record and a rerun
    resumes at the first missing one. `meta` describes the run, not the
    invocation, so it is set only on a fresh record: a resume keeps the
    date and the command the run began with, even across midnight,
    rather than stamping the rerun's.
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
                if not done("relation_loop", corpus.name, model, judge):
                    record(runners["relation_loop"](corpus=corpus, model=model, judge=judge),
                           "relation_loop", corpus.name, model, judge)
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


def _selection(models_arg: str, judges_arg: str | None = None) -> tuple[list[str], list[str]]:
    """The models to run and the judges to score them, from the two flags.

    Models and judges are independent: a model added to the batch is not
    thereby a judge of it, so the batch can widen without widening the
    judge set. An explicit `--judges` names the judges outright.
    """
    models = _split(models_arg)
    judges = _split(judges_arg) if judges_arg else list(DEFAULT_JUDGES)
    return models, judges


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", action="append", default=None,
                        help="notes directory, repeatable; a reference-regions.json "
                             "beside it is scored against if present "
                             f"(default: {', '.join(DEFAULT_CORPORA)})")
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS),
                        help="comma-separated generation models")
    parser.add_argument("--judges", default=None,
                        help="comma-separated faithfulness judges: `nli` for the "
                             "decoupled NLI cross-encoder, otherwise a generation "
                             f"model (default: {', '.join(DEFAULT_JUDGES)})")
    parser.add_argument("--work", default="/tmp/opencode/suite",
                        help="where corpus copies are built; not part of the record")
    parser.add_argument("--out", default=None,
                        help="the JSON record (default: benchmarks/runs/<date>/run.json)")
    parser.add_argument("--force", action="store_true",
                        help="throw the existing record away and run every step again")
    args = parser.parse_args(argv)

    corpora = [Corpus.discover(path) for path in (args.corpus or DEFAULT_CORPORA)]
    models, judges = _selection(args.models, args.judges)
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
