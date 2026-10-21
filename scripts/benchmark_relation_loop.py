"""The relation loop asked one pair at a time.

The native channel is one tool conversation over the whole map, and it
writes no relations on either model (`benchmarks/relations.md`, "What
the shape rests on"). The structured channel answers one relation per
call, so the orchestration has to name the pair. This script runs that
loop over every touching pair of a map and asks what it writes: the
statement, the seconds it cost, and the statement judged against the
notes of the two regions it names — the notes that would have to bear it
out, the same evidence the faithfulness judge uses for a claim. The page
the relations render is in the record too, so what the loop wrote can be
read rather than inferred.

The characterisations are the ones a `grappoli read` wrote. The map is
built here when it is not given, as the granularity probe builds it, so
the regions the relations name are the corpus's.

The cost of each pair is kept beside the relations file, in a file of its
own, because a run that resumes asks only the pairs still missing: the
cost of a pair is a fact about the pair, and a resumed run must report
it rather than a second of its own.

Usage:
    uv run python scripts/benchmark_relation_loop.py NOTES --characterisations PATH
        [--model llama3.2:latest] [--map MAP.json] [--relations PATH]
        [--judge nli|none] [--fresh] [--out RECORD.json]
"""

import argparse
import json
import sys
import time
from pathlib import Path

from grappoli.characterise import read_characterisations
from grappoli.corpus import load_corpus
from grappoli.map import build_map
from grappoli.measure import JudgeFailed, nli_judge
from grappoli.model import DEFAULT_MODEL, structured
from grappoli.relations import read_relations, relatable_edges, relate_pairs
from grappoli.render import render
from grappoli.words import stopwords, terms


def read_characters(path) -> dict[int, dict]:
    """The characterisations a read wrote, keyed by region.

    The shipped reader, so the file the `read` step wrote is read the
    way that step wrote it — a torn line skipped rather than fatal.
    """
    return read_characterisations(Path(path))


def region_notes(region: dict, notes: dict[str, str]) -> str:
    """Every note in a region, in the order the map lists them."""
    return "\n\n".join(notes[name].strip() for name in region["members"] if name in notes)


def seconds_path(path) -> Path:
    """Where the cost of each pair is kept, beside the relations file."""
    path = Path(path)
    return path.with_name(path.name + ".seconds")


def read_seconds(path) -> dict[tuple[int, int], float]:
    """The cost of each pair already asked, from the file beside them.

    A pair on disk without a cost is one asked by a run that kept no
    record of it, which happens when the file was written by hand; it is
    left out rather than guessed at.
    """
    path = Path(path)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    seconds = {}
    for key, value in data.items():
        source, _, target = key.partition(",")
        try:
            seconds[(int(source), int(target))] = float(value)
        except (TypeError, ValueError):
            continue
    return seconds


def write_seconds(path, seconds: dict[tuple[int, int], float]) -> None:
    """The cost of each pair, written whole so a resume can read it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps({f"{a},{b}": value for (a, b), value in seconds.items()},
                               indent=2) + "\n")
    temp.replace(path)


def shared_terms(statement: str, text: str, stop: frozenset[str]) -> set[str]:
    """The content terms a statement and a text share.

    The set says whether the sentence is about that region's material at
    all, which is what a relation naming two regions has to do: the judge
    reads whether the sentence is supported, this reads whether it is
    about the two regions it names.
    """
    return terms(statement, stop) & terms(text, stop)


def judge_relations(relations: dict, mapping: dict, notes: dict[str, str], judge,
                    stop: frozenset[str]) -> list[dict]:
    """Each statement against the notes of the two regions it names."""
    regions = {region["id"]: region for region in mapping["regions"]}
    verdicts = []
    for (source, target), record in sorted(relations.items()):
        evidence = "\n\n".join(region_notes(regions[region], notes)
                               for region in (source, target))
        try:
            verdict = judge(record["statement"], evidence) if judge is not None else None
        except JudgeFailed as err:
            # A judge that cannot answer a statement leaves it undecided,
            # as it leaves a claim undecided: the statement is recorded
            # and counted as neither supported nor unsupported.
            verdict = {"supported": None, "reason": str(err)}
        mentions = {
            str(region): sorted(shared_terms(record["statement"],
                                             region_notes(regions[region], notes), stop))
            for region in (source, target)
        }
        verdicts.append({
            "source": source,
            "target": target,
            "statement": record["statement"],
            "supported": None if verdict is None else verdict["supported"],
            "reason": None if verdict is None else verdict["reason"],
            "mentions": mentions,
        })
    return verdicts


def run(notes: dict[str, str], characters: dict[int, dict], model: str, *,
        mapping=None, relations_path=None, judge=None, log=None) -> dict:
    """One pass of the pair loop over a map, and what it wrote.

    `relations_path` is where the loop writes, so the page renders what
    this run produced; the file is the shipped one, keyed by pair, and a
    pair already in it is not asked again. The cost of each pair is kept
    beside that file, so a resumed run reports what the pairs cost
    rather than what the resume cost.
    """
    if mapping is None:
        mapping = build_map(notes, progress=lambda *e: None)
    path = Path(relations_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cost_path = seconds_path(path)
    seconds_by_pair = read_seconds(cost_path)
    started = time.monotonic()

    def on_pair(record, seconds):
        seconds_by_pair[(record["source"], record["target"])] = seconds
        write_seconds(cost_path, seconds_by_pair)
        if log is not None:
            log(f"  ({record['source']},{record['target']}) {seconds:.0f}s — "
                f"{record['statement']}")

    def ask(prompt, schema):
        return structured(prompt, schema, model=model)

    missing = relate_pairs(mapping, characters, path, llm=ask, on_pair=on_pair, log=log)
    wall = time.monotonic() - started

    relations = read_relations(path)
    verdicts = judge_relations(relations, mapping, notes, judge,
                               stopwords(notes.values()))
    for verdict in verdicts:
        pair = (verdict["source"], verdict["target"])
        verdict["seconds"] = seconds_by_pair.get(pair)
    supported = sum(1 for v in verdicts if v["supported"] is True)
    unsupported = sum(1 for v in verdicts if v["supported"] is False)
    return {
        "model": model,
        "regions": len(mapping["regions"]),
        "pairs": len(relatable_edges(mapping, characters)),
        "written": len(relations),
        "missing": [list(pair) for pair in missing],
        "seconds": round(sum(seconds_by_pair.values()), 1),
        "wall_seconds": round(wall, 1),
        "relations": verdicts,
        "supported": supported,
        "unsupported": unsupported,
        "both_regions": sum(1 for v in verdicts
                            if all(v["mentions"].values())),
        "page": render(mapping, characters, relations),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notes", help="path to the branch of notes")
    parser.add_argument("--characterisations", required=True,
                        help="the line file a `grappoli read` run wrote")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--map", default=None,
                        help="the map.json a read wrote; built here when absent")
    parser.add_argument("--relations", default=None,
                        help="where the loop writes; nothing written when absent")
    parser.add_argument("--judge", choices=("nli", "none"), default="nli",
                        help="how the statements are judged against the notes")
    parser.add_argument("--fresh", action="store_true",
                        help="empty the relations file, and the cost beside it, "
                             "before the run")
    parser.add_argument("--out", default=None, help="the record to write")
    args = parser.parse_args()

    notes = load_corpus(args.notes)
    characters = read_characters(args.characterisations)
    mapping = json.loads(Path(args.map).read_text()) if args.map else None
    relations_path = args.relations
    if relations_path and args.fresh:
        Path(relations_path).unlink(missing_ok=True)
        seconds_path(relations_path).unlink(missing_ok=True)

    judge = nli_judge() if args.judge == "nli" else None
    record = run(notes, characters, args.model, mapping=mapping,
                 relations_path=relations_path, judge=judge,
                 log=lambda line: print(line, file=sys.stderr))

    text = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    if args.out is None:
        print(text, end="")
    else:
        Path(args.out).write_text(text)


if __name__ == "__main__":
    main()
