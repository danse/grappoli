# Relations

The loop that states, in words, how two regions touch. Its shape is
settled: one conversation over the whole map, in which the model — not the
orchestration — chooses what to read and which pair to relate, over the
native tool channel (`model.converse`). Enumerating a granularity instead
was measured and set aside; the alternative, the experiments behind it, and
the older rows are under `history/<date>/relations.md`.

The loop is `src/grappoli/relations.py` (`run_agent`, `relate_regions`),
its tool surface and resume guarantee are in `architecture.md` (Agent
tools), and its behaviour is pinned in `tests/test_relations.py`. A
relation is one appended line keyed by the unordered pair, so a resumed run
retries only the pairs still missing and never regenerates a completed one.

## What the shape rests on

One call per approach, native channel, both models on both corpora — a
floor for the loop, so it compares the shapes, not the final bill
(`benchmarks/runs/2026-10-13/run.json`):

| corpus | model | approach | prompt tok | seconds | calls | valid |
|---|---|---|---|---|---|---|
| in-domain | 0.5B | per edge | 317 | 206 | 0 | no |
| in-domain | 0.5B | per region | 633 | 304 | 0 | no |
| in-domain | 0.5B | whole map | 664 | 333 | 0 | no |
| in-domain | 3B | per edge | 248 | 291 | 1 | no |
| in-domain | 3B | per region | 607 | 451 | 1 | no |
| in-domain | 3B | whole map | 638 | 470 | 1 | no |
| heterogeneous | 0.5B | per edge | 247 | 77 | 0 | no |
| heterogeneous | 0.5B | per region | 561 | 235 | 0 | no |
| heterogeneous | 0.5B | whole map | 698 | 284 | 0 | no |
| heterogeneous | 3B | per edge | 245 | 259 | 1 | no |
| heterogeneous | 3B | per region | 406 | 600 | 5 | no |
| heterogeneous | 3B | whole map | 489 | 748 | 4 | no |

Whole map is the cheapest single call — one call for the whole map against
a call per region — and the reason for it is not the costing: the other two
decide in advance what to read and relate, and that choice is the behaviour
the loop exists to produce. On the real prompt 0.5B does not call a tool at
all — it answers in prose, the content path `model.py` documents. The 3B
model does call tools, one to five a prompt, and still returns nothing
valid: a bigger model reaches the interface without yet reaching the result.

The channel was the decisive measurement. With a `format`-constrained
schema every cell of the batch returns a valid relation, so the shape was
never the blocker; but that schema is *one* relation, so a whole-map prompt
can only get one back, and it takes the tool choice away:

| channel | many relations in one conversation? | valid arguments? |
|---|---|---|
| native (tools only) | yes | no — schema echo, region labels, copied claims |
| structured (one-relation `format`) | no, one per call | yes |

Native is what shipped, because it is the only channel where the loop
recovers: at 3b the model held a schema-echo argument shape for ~25 calls,
then shed it once the error was visible, read regions past the first, and
wrote 4 of 6 pairs.

## What is not settled

The shipped loop, live, writes no relations at all. `grappoli read` left 0
of 6 in-domain pairs and 0 of 5 heterogeneous pairs on **both** models,
every pair missing, on its own copy of the corpus
(`benchmarks/runs/2026-10-13/run.json`, `read` step). At 3b, guided to one
relation a round, the content is there: all six pairs, every statement
relating the two regions it names. Unassisted on the whole-map native
prompt it is not — the model calls `list_regions`, reads nothing, and
serialises its *writes* as content JSON, several at once, which is neither
a native call nor one parseable object. So the map's content is within 3b's
reach and its unassisted tool use is not, on this hardware, and the model
decision turns on that (`architecture.md`, Provisional;
`benchmarks/measurement.md`).

Two cautions for any change to the prompt, both recorded as failures first:
a model will reach for a `done` tool the schemas do not define (the stop is
a message naming no tool), and it copies a worked example verbatim — the
shipped prompt carries none, and should keep it that way.

## The trail

Every configuration that led here is under `history/<date>/relations.md`,
by the date it was run — 2026-10-09, 2026-10-12, 2026-10-13 — with the
numbers and the raw replies. The batch in `benchmarks/README.md` reruns
`scripts/benchmark_relations.py`, both channels, under the current
defaults; this file is replaced by that reading, not appended to.
