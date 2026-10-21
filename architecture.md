# architecture

`product.md` holds what the project is and the decisions taken before
any code existed. `roadmap.md` holds the build order. This file holds
what sits behind those decisions: the actual components, and which
choices are still waiting on a measurement.

## Corpus

A branch is a directory of notes, possibly nested, and a note is any text
file in it — extension or none. `grappoli.corpus.load_corpus` loads them
all, so a tree of `.txt`, `.org` or extensionless notes maps the same as
one of markdown. Notes are keyed by path relative to the branch root, so
a note's identity is stable however deep it sits, and the body is loaded
as-is: headings are not assumed to exist (`tests/fixtures/README.md`).

Two paths are not notes. A path with a hidden component — a leading dot,
as in `.git/` or the build directory `.grappoli/` — is skipped, and
skipping hidden paths as a class is also what keeps the build directory
out of its own map. And a file that does not decode as UTF-8 is skipped,
so an image or a document left in the tree is not read as prose.
`tests/test_corpus.py` pins the rule.

## Language

A corpus is read as words, not as English. A term is a word of three
letters or more in any script, split on letters and digits: an ASCII
split does not merely lose a word it cannot read, it shortens the one it
is in the middle of, so "città" becomes "citt" and joins every other
word beginning "citt". Which of those words say nothing is a fact about
the language a note is written in, so the lists come from `stopwordsiso`
rather than a set kept here (`grappoli.words`).

The language is not guessed. Every language's list is scored by how much
of the corpus it accounts for, and each scoring at least half the best
counts as written, so a mixed corpus is read as all its languages and a
corpus no list accounts for keeps every word. The detected set is the
corpus's, and the two places that filter words take it from there: the
TF-IDF control's stop words, and the terms `compare_regions` compares.

The TF-IDF control's structure numbers (`benchmarks/structure.md`,
`benchmarks/structure-heterogeneous.md`) are the multilingual sweep,
where the control reads the corpus's own stop words. The English sweep
they replaced — the English encoder and its English stop words — is kept
under `benchmarks/history/2026-10-16/`; a corpus in another language
re-measures the control rather than rewrites the record.

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

Note vectors from `intfloat/multilingual-e5-small` — small, fast on
CPU, and reads a hundred-odd languages, so a branch in any of them is
embedded by the same model the English one was. Its weights being in
the local cache is convenience, not reasoning; they are re-fetchable
anywhere.

**TF-IDF cosine runs alongside as a control.** If the encoder does not
beat bag-of-words on structure match, the encoder is not earning its
keep and the simpler one wins. The control has run: the multilingual
encoder wins on both fixture shapes — 0.904/1.000 against 0.435/0.494 —
though TF-IDF's failure is localised rather than across the board
(`benchmarks/structure.md`, "Reading (2026-10-16)").

Redundancy pairs are scored by `mmarco-mMiniLMv2-L12-H384-v1`, the
multilingual cross-encoder, so two characterisations are compared by a
model that reads the corpus's language; it is raw-logit like its English
twin, and its threshold carries that twin's measurement
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
saturated corpus's winner is a mutual-filtered k=4 at resolution 2 (ARI
0.904); on the heterogeneous corpus that same rule scores 0.783, whose
own winner is a small plain neighbourhood at higher resolution (ARI
1.000) — `benchmarks/structure-heterogeneous.md`. The defaults are
therefore the best worst-case row across both, which this time is also
the saturated corpus's winner: k=4, mutual, weighted, resolution 2.0 —
0.904 in-domain, 0.783 heterogeneous, and no single setting scores
better in the worst case.
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

## The document

`grappoli show NOTES` is the pipeline's last arrow: it reads the three
working files and prints one page to standard output, and it writes
nothing back into the branch. `grappoli.render.render` is a pure function
of the map, the characterisations and the relations — no model, no clock,
no file of its own — so one build always reads the same and the page is
the corpus's rather than the model's. The model's words are carried
verbatim: `about`, `topics`, `key_claims` and each relation `statement`
appear as written, because a paraphrase would be our understanding laid
over the reader's (`product.md`, What it produces).

The content contract is fixed: every region; its characterisation where
one exists; every relation, once, between characterised regions; and the
notes that stand alone. A region with no characterisation, or a touching
pair with no relation, is printed as a gap — `no characterisation`,
`(no relation recorded)` — rather than omitted or invented, so a partial
build reads as partial.

The layout is a presentation choice rather than a measurement, and is
fixed here so that changing it is a change to the record: the header and
its rule first, then the regions, then how they touch, then the notes
nothing refers to. The regions lead because they are the figure a reader
acts on; each lists its notes in full and names its representatives only
when they are a proper subset, since for a region small enough that every
note was sent to the model the two would say the same thing twice. The
map is shown flat, and nesting, if it is ever wanted, is a choice for
this section judged by reading rather than scored (Provisional).
`tests/test_render.py` pins the contract and the layout.

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
  `mmarco-mMiniLMv2-L12-H384-v1` cross-encoder, both orders scored and the
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
  or relation the notes do not hold, or contradicts them. The judge is
  either the model under test — a known limit, the verdicts are part of
  the result so the disagreement is readable rather than smoothed away,
  and a malformed verdict is retried up to three attempts as a malformed
  characterisation is — or, under `--judge nli`, the
  `mDeBERTa-v3-base-mnli-xnli` cross-encoder, which scores entailment
  straight off the notes and is decoupled from the model by construction.
  The cross-encoder is trained on sentence pairs, so the evidence is cut
  into sentences and adjacent pairs and the claim is supported when any
  premise entails it; a whole region's notes are a long, multi-topic
  premise on which entailment drifts to neutral (`benchmarks/measurement.md`,
  "Reading (2026-10-20)"). A claim the model judge never answers is
  recorded undecided and left out of the share, so a failing judge cannot
  move the number it reports; the NLI judge always answers, so it leaves
  no claim undecided.
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
them. All four are settled now, and each is stated with what settled it:

**Communities as regions — confirmed by structure match.** Mutual-filtered
communities reach 0.904 on the saturated corpus
(`benchmarks/structure.md`, "Reading (2026-10-16)") and 1.000 on the
separable one (`benchmarks/structure-heterogeneous.md`, "Reading
(2026-10-16)"); the English sweep that first confirmed it was reproduced
exactly by the 2026-10-13 batch (`benchmarks/runs/2026-10-13/run.json`).

**An encoder over TF-IDF — confirmed by structure match.** The
multilingual encoder beats TF-IDF on both shapes, 0.904/1.000 against
0.435/0.494 at each provider's own best. The mean margin was never the
test: reproducing the intended partition is.

**Flat map — settled.** Structure match cannot be the arbiter it was
promised to be: adjusted Rand index compares two flat partitions, so a
level added *above* the regions is invisible to it, and a level *below*
is scored only as a splitting of the reference's own regions. What the
measurement could still say it did: the in-domain map makes five regions
against a reference of four, splitting equipment-and-storage, and going
coarser — resolutions below 1.0 — is worse on the English sweep, not
better (`benchmarks/structure.md`, "Coarser resolution (2026-10-15)";
`benchmarks/structure-heterogeneous.md`, "Coarser resolution
(2026-10-15)"). The map sits flat, and nesting is not a shape the
measurements reach; if it is wanted it is a presentation choice for the
render, to be judged by reading rather than scored.

**qwen2.5:0.5b as the model — confirmed by faithfulness.** The row stood
open until a judge decoupled from the model under test could score the two
characterisers, because both LLM judges misread verbatim claims (the 0.5B
judge ten of ten) and neither could rank the models at all
(`benchmarks/measurement.md`, "The judge is the larger term"). The NLI
cross-encoder has now done it: qwen2.5:0.5b scores 0.478, 0.857 and
0.950 over the three corpora against llama3.2:latest's 0.800, 0.765 and
0.750 — behind on the saturated one, ahead on the other two, level on the
average (0.762 against 0.772) — while generating at three times the speed
(`benchmarks/measurement.md`, "Reading (2026-10-20)"). Faithfulness does
not overturn the smaller model, so it stands. The other leg of the row is
not settled by this: the relation loop's tool channel fails for both
models, so the map's relations are out of reach of either one unassisted
(`benchmarks/relations.md`).

Characterisation put 0.5B's failure modes on record — the tool ignored
on a real prompt, prose instead of JSON without `format`, an over-long
answer that truncates under a cap (`benchmarks/characterisation.md`).
The relation loop put its own prompt on the same record: at 3b the
shipped whole-map loop names `list_regions` and then serialises its
writes in content, so whether a model drives the tools unassisted is part
of what the model row decides (`benchmarks/relations.md`). That was the
ground the faithfulness row stood on: across both fixtures the 0.5B judge
flags ten claims and every one is a sentence lying verbatim in the
region's own notes, and the 3B judge errs often enough to be a floor too —
the judge, not the map, is the weak link (`benchmarks/measurement.md`,
"The judge is the larger term"). The judge decoupled from the model under test
has since scored both characterisers, and found them level.

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
