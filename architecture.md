# architecture

`product.md` holds what the project is and the decisions taken before
any code existed. `roadmap.md` holds the build order. This file holds
what sits behind those decisions: the actual components, and which
choices are still waiting on a measurement.

## Build pipeline

The map is built once, offline, in one direction:

```
notes ──(arithmetic)──▶ regions + edges
      ──(one call per region)──▶ characterisations
      ──(one agent loop)──▶ relations
      ──(one page)──▶ document   ← no model after this point
```

The pipeline's working files are written under `<branch>/.grappoli/` —
the map and the append-only characterisations. That directory is a
build directory, not an output: `grappoli read` writes it, and what a
reader eventually sees is the rendered document, never these. Keeping
them in one hidden place means a branch is not littered with
intermediates and a rerun finds its own resume state.

Each arrow is a component named for the artefact it produces. No model
runs after the relations are written — making the document from the map,
the characterisations and the relations is deterministic formatting. The
relation agent is a build-time worker: it walks the graph once while the
map is being made, and is gone before anything is read.

## Progress and logging

The pipeline is slow by design: a characterisation runs roughly four
minutes under `qwen2.5:0.5b` and about eleven under `llama3.2:latest`,
with generation ~1.9 tok/s (0.5B) and ~0.6 tok/s (3B)
(`benchmarks/throughput.md`). A build must be observable while it runs
and able to survive an interrupt.

- **Every step reports its own progress.** Each step's unit is its
  item: the map reports embedded and clustered notes, characterisation
  the region in hand (region 3 of 16), the relation loop the agent's
  round and the relation in hand (relation 5 of 9), and each tool call
  the agent makes with the answer it got — each with an ETA derived from
  the throughput record. The tool call is logged because the agent's
  choice is what the relation loop exists to produce, and a loop that
  stalls is read from the choice that stalled, not from its totals.
  Progress writes to stderr and never enters the output artefact.
- **Artefacts append; runs resume.** `characterisations` and
  `relations` are append-only line files, one item per line. An
  interrupt at region 12 of 16 resumes at region 12; a completed item
  is never regenerated. This is why they are line files and not one
  overwritten JSON document.

## Similarity

Note vectors from `BAAI/bge-small-en-v1.5` — small, fast on CPU, strong
for its size. Its weights being in the local cache is convenience, not
reasoning; they are re-fetchable anywhere.

**TF-IDF cosine runs alongside as a control.** If the encoder does not
beat bag-of-words on structure match, the encoder is not earning its
keep and the simpler one wins. The control has run and bge wins on both
fixture shapes — 0.652/1.000 against 0.450/0.435 — though TF-IDF's
failure is localised rather than across the board
(`benchmarks/structure.md`, "Reading (2026-10-16)").

Two cached cross-encoders — `ms-marco-MiniLM-L-6-v2`,
`mmarco-mMiniLMv2-L12-H384` — score pairs for redundancy. Redundancy
uses the English one to judge whether two characterisations say the same
thing; the multilingual twin is there for a corpus it cannot read
(`grappoli.measure`).

## Graph

Cosine similarity → k-nearest neighbour graph → community detection →
regions; cross-community edges become the relations. This is the rule
`product.md` states, worked out: one computation produces both the
regions and how they touch.

Graph construction makes no model calls of any kind. Cosine similarity
is arithmetic over vectors; regions, edges and representatives are all
fixed before Ollama is asked anything.

The rule has knobs — neighbourhood size, reciprocal-edge filtering,
louvain resolution and weighting — and they decide whether a map holds
together. `scripts/benchmark_structure.py` sweeps them against a corpus
and, given a reference map to score against, names a winner with
adjusted Rand index; the winning settings become `build_map`'s
defaults, the same way measurement has driven them so far. Without a
reference the sweep reports and decides nothing — the measures that
need no reference (silhouette, leave-one-out stability) demonstrably do
not reproduce structure match (`benchmarks/structure.md`).

The sweep runs per corpus, and the two fixture shapes disagree. The
saturated corpus's winner is k=5 plus the mutual filter (ARI 0.652); on
the heterogeneous corpus that same rule scores 0.381, whose own winner
is a small plain neighbourhood at higher resolution (ARI 1.000) —
`benchmarks/structure-heterogeneous.md`. The defaults are therefore
neither winner, but the best worst-case row across both: bge, k=5,
mutual, weighted, resolution 2.0 — 0.578 in-domain, 0.729
heterogeneous, and no single setting scores better in the worst case.
A scored corpus more representative than the fixtures rebakes them,
the same mechanism with a third reference.

The resolution sweep originally stopped at 1.0. Extending it below —
the direction that would merge regions rather than split them — does
not improve either shape, so that corner of the space is closed too
(`benchmarks/structure.md`, "Coarser resolution (2026-10-15)").
Nothing in the measurement reaches a nested map: adjusted Rand index
compares flat partitions, so a level above the regions is invisible to
it, and the map sits flat (Provisional).

The model meets this structure only afterwards, in the relation loop —
and only to state, in words, what the graph's edges already assert.

## Model interface

Generation goes through one function, `grappoli.model.structured`: it
sends a prompt with a tool schema and a JSON `format`, reads a native
tool call if there is one, and otherwise reads JSON in the content. On a
real region prompt 0.5B answers in content — the tool fires only on
trivial prompts — so the content path is the normal one, and `format` is
what keeps it JSON rather than prose (`benchmarks/characterisation.md`).
The tool is still offered first, because a larger model may take it and
the interface must let the model comparison find out. It is the only
place `ollama` is imported, so the comparison replaces models by
replacing it rather than by editing the pipeline steps; the import is
lazy, so building a map still pulls no generation machinery into the
process.

The relation loop uses a second turn in the same module, `converse`: one
message of a tool-using conversation, the tool schemas sent natively and
no `format` imposed, the assistant message returned unread for the loop
to dispatch. The two are the whole model surface — `structured` forces a
single JSON shape, `converse` lets the model name a tool — and neither
imports `ollama` until it is called.

Characterisation sits on top of it in `grappoli.characterise`: the
prompt is the region's representatives and nothing else, the answer is
validated structurally, a malformed one is retried up to three attempts
total, and each completed region is appended to the line file. A region
that exhausts its attempts is logged from its own measurements —
attempts and wall-clock seconds — rather than swallowed, so a build
records where it spent generation and failed.

## Agent tools

The tools are Python functions in our own process; Ollama only ever
names one. It returns a `<tool_call>` block, the loop matches the name,
runs the function, appends the result and calls again — generation
produces the tokens, our code does the work.

- `list_regions` — the regions, the pairs that touch, and which pairs
  already have a relation
- `read_characterisation` — read a stored characterisation
- `compare_regions` — a computation over two characterisations
- `write_relation` — append a relation to the output

The list is the whole-map shape on purpose: one conversation, in which
the model — not the orchestration — chooses which region to read and
which pair to relate, and `list_regions` is what lets it find the pairs
itself. Splitting the loop per region or per edge was considered and set
aside, because it takes that choice away from the model, which is the
behaviour the relation loop is here to produce (`benchmarks/relations.md`).

The loop itself is `product.md`'s decision; the tool list is what makes
its central constraint real. No tool returns a raw note, because no
such function was ever written — the agent cannot reach the corpus
however it asks.

An interrupted run resumes from what is on disk, so the loop never
regenerates a completed relation: `list_regions` marks a pair already
related, and `write_relation` refuses one that already has a line. The
refusal sits in the toolbox rather than in the prompt, so a model that
repeats itself cannot append a second line for a pair that is done.

## Measurements

`grappoli measure NOTES` scores a map already built under
`NOTES/.grappoli/`: it reads the working files and writes nothing. It is
not one of the pipeline's steps above — the build never calls it, and the
models it uses run only when it is asked. So "no model after the
relations are written" holds for the build and the render; measurement
is a reading of the finished map, on demand.

The four numbers are `grappoli.measure`:

- **Comprehensiveness** — the share of the corpus a region holds. A
  note left standing alone is accounted for but not homed, so a map
  that explains little scores low however tidy its regions are. It is
  the one number with no model behind it.
- **Redundancy** — the share of characterisations that repeat another.
  Whole characterisations are compared pairwise by the cached
  `ms-marco-MiniLM-L-6-v2` cross-encoder, both orders scored and the
  higher kept because neither is the other's query. Two regions say the
  same thing at or above `0.0` on the model's raw logits; a chain of
  repeats collapses to one group. Redundancy is then the share of
  regions that are not the first of their group — 0 when every region
  adds something, `(n-1)/n` when one thing is repeated n ways. The
  threshold is provisional, like every threshold here
  (`benchmarks/measurement.md`).
- **Faithfulness** — the share of `key_claim`s the notes of their own
  region support. Each claim is judged alone against every member of
  the region under an explicit rubric: supported when the notes state
  or directly entail it, unsupported when it adds a fact, name, number
  or relation the notes do not hold, or contradicts them. A malformed
  verdict is retried up to three attempts, exactly as a malformed
  characterisation is; a claim the judge never answers is recorded
  undecided and left out of the share, so a failing judge cannot move
  the number it reports. The judge is the model under test, which is a
  known limit: the verdicts are part of the result so the disagreement
  is readable rather than smoothed away.
- **Structure match** — adjusted Rand index of the map's regions
  against a reference, the score `scripts/benchmark_structure.py` also
  sweeps the rule with, through the same `reference_labels` check. It
  is the only measure that needs a labelled corpus, and it is simply
  absent without `--reference`.

What the four cannot do is weigh whether to produce a characterisation
at all. Comprehensiveness and structure match are properties of the map,
and the map is built with no model call; redundancy reads
characterisations, so it is `0` when there are none; faithfulness scores
a characterisation's claims and is therefore a gate on one that exists.
A selection-only map — regions and representatives, no prose — thus ties
on coverage and cannot lose on redundancy, and no number says what the
prose adds. So the measured set polices the characterisation; it does
not justify it. Whether it is worth its cost is settled on the product's
premise, not by a measurement: the statement of what each region is
about, and the relations the agent reaches only through
characterisations (`product.md`, The problem; `roadmap.md`).

ROUGE and the reference-free measures are deliberately not here: ROUGE
scores copying, and silhouette and leave-one-out stability demonstrably
do not reproduce structure match (`benchmarks/structure.md`).

## Provisional

Choices taken to get moving, with the measurement that can overturn
them. Three have been confirmed and left the table for the readings that
confirm them; the one that remains is stated with what settles it:

| Decision | Overturned by | Standing |
|---|---|---|
| qwen2.5:0.5b | faithfulness | Open — both LLM judges misread verbatim claims (the 0.5B judge ten of ten), so neither can settle it; a judge decoupled from the model under test is required (`benchmarks/measurement.md`, "Reading (2026-10-13)"). |

**Communities as regions — confirmed by structure match.** Mutual-filtered
communities reach 0.652 on the saturated corpus
(`benchmarks/structure.md`, "Reading (2026-10-16)") and 1.000 on the
separable one (`benchmarks/structure-heterogeneous.md`, "Reading
(2026-10-16)"); the 2026-10-13 batch reproduced both sweeps exactly
(`benchmarks/runs/2026-10-13/run.json`).

**bge-small over TF-IDF — confirmed by structure match.** bge beats
TF-IDF on both shapes, 0.652/1.000 against 0.450/0.435 at each
provider's own best. The mean margin was never the test: reproducing the
intended partition is.

**Flat map — settled.** Structure match cannot be the arbiter it was
promised to be: adjusted Rand index compares two flat partitions, so a
level added *above* the regions is invisible to it, and a level *below*
is scored only as a splitting of the reference's own regions. What the
measurement could still say it did: the in-domain map makes four
regions, as the reference does, but not the same four (equipment-and-
storage is dismantled), and going coarser — resolutions below 1.0,
never swept until now — is worse on both shapes, not better, so the
best worst-case setting is unchanged
(`benchmarks/structure.md`, "Coarser resolution (2026-10-15)";
`benchmarks/structure-heterogeneous.md`, "Coarser resolution
(2026-10-15)"). The map sits flat, and nesting is not a shape the
measurements reach; if it is wanted it is a presentation choice for the
render, to be judged by reading rather than scored.

Characterisation put 0.5B's failure modes on record — the tool ignored
on a real prompt, prose instead of JSON without `format`, an over-long
answer that truncates under a cap (`benchmarks/characterisation.md`).
The relation loop put its own prompt on the same record: at 3b the
shipped whole-map loop names `list_regions` and then serialises its
writes in content, so whether a model drives the tools unassisted is part
of what the model row decides (`benchmarks/relations.md`). That is the
ground the faithfulness row now stands on: across both fixtures the 0.5B
judge flags ten claims and every one is a sentence lying verbatim in the
region's own notes, and the 3B judge errs often enough to be a floor too —
the judge, not the map, is the weak link (`benchmarks/measurement.md`,
"Reading (2026-10-13)"). The choice of model is still open, to be settled
by a judge decoupled from the model under test.

## Environment

Python 3.12 under `uv`; `sentence-transformers`, `ollama`,
`scikit-learn`, `pytest`. CPU-only — there is no GPU, and no framework
for the agent.

Generation goes through Ollama (`qwen2.5:0.5b`). Its server has no
embedding support and is left as it is.

Generation runs at ~1.9 tok/s for `qwen2.5:0.5b` and ~0.6 for
`llama3.2:latest`, with prefill at ~2.4 and ~1.1 tok/s respectively
(`benchmarks/throughput.md`, 2026-10-13). The pipeline is sized against
the 0.5B rates; the 3B rates cap what it can afford on this hardware.
