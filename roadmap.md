# roadmap

The build order for `grappoli`. `product.md` states what it is and why;
`architecture.md` pins the decisions. This file is when each step
happens, what it has to answer, and what its tests have to pin. Stages
run in order — a stage is not finished until its tests are in `tests/`
and describe the behaviour rather than merely exercise it. Finished
stages are removed entirely, not marked; what they learned stays in
the tests and in `benchmarks/`.

## Stage 2 — Characterisation, one region at a time

Five representative notes → prompt → structured characterisation,
validated. Retry on malformed output, log the failures rather than
swallowing them.

Structured output goes through the model's native tool-call mechanism,
which the probe in `benchmarks/throughput.md` confirmed works at 0.5B:
it emitted a correct name and correct arguments with empty content.
JSON-in-content stays the fallback if a particular schema trips it.
The model sits behind a single interface so Stage 5 can swap it
without rework.

Retries cost roughly four minutes of generation each at measured
throughput — one characterisation is a nontrivial expense and three
schemas failures in a row is an afternoon. They are capped, and their
cost is logged alongside the failure.

**Tests pin:** parsing, retry and cap behaviour; what the model
actually gets wrong, recorded as observed failures rather than
expected ones; progress is shown per region being characterised, and
an interrupted run resumes without regenerating completed regions.

**Answered when:** the chosen model's failure modes are on record — the
faithfulness row of `architecture.md`'s provisional table now has
something behind it.

## Stage 3 — The agentic loop

A hand-rolled loop, roughly 150 lines: the model returns a tool call,
our Python executes it, the result is appended, repeat until it stops
asking. The tools are in `architecture.md`; no framework, because the
mechanism is the point.

The agent sees characterisations and never raw notes — enforced by the
tool surface, since no tool returns one, rather than by instruction.

Round budget is set by the measured throughput — ≈3 tok/s prefill,
≈2.3 tok/s generation, `benchmarks/throughput.md` — with a hard cap
regardless: an unbounded loop is not a bug, it is a hung machine. The
pipeline does not touch thread counts: the benchmark showed
`num_thread=4` collapses decode on two cores to 0.5 tok/s.

**Granularity is open, and now costable.** One loop for the whole map,
one per region, or one per edge differs in conversation cost by
factors at measured throughput. Decide it in this stage with numbers
against the fixture — not by preference.

**Tests pin:** the loop terminates under adversarial tool output; tool
errors are recoverable; no path reaches a raw note; relations are
written between characterisations only. The model is stubbed with a
scripted call sequence so all of this runs without Ollama and without
nondeterminism. Progress is shown for each round and relation; an
interrupted run resumes without regenerating completed relations.

**Answered when:** relations can be characterised without any step
seeing the corpus whole.

## Stage 4 — The four measurements

**Comprehensiveness** — share of the corpus with a home in the map.
**Redundancy** — measured alongside it, because redundancy reads as
coverage and measuring one alone optimises into the other.

**Faithfulness** — atomic claims checked against their notes under an
explicit rubric. No free-form scoring: a judge without a rubric
rewards fluency, which is precisely how a small model fails.

**Structure match** — against the fixture's reference regions.

Reference metrics are not used, per the spec: ROUGE scores copying.

**Risk:** the judge is also a 0.5B. Report judge disagreement honestly
rather than adjusting the rubric until the number improves.

**Tests pin:** each metric on a corpus where the right answer is known,
including one deliberately redundant map and one deliberately
unfaithful characterisation — a metric that cannot fail on a bad input
is not measuring.

**Answered when:** all four numbers can be produced on demand for any
candidate map.

## Stage 5 — Let the measurements settle what is left

**Is characterisation worth its cost?** Selection-only output against
the full map, on comprehensiveness and redundancy. The answer may be
that selection alone is the useful output — a result, not a failure.

**Which model?** qwen2.5:0.5b against llama3.2:3b, both already
downloaded, and anything larger worth pulling now there is room,
decided primarily on faithfulness.

**Flat or nested?** Informed by structure match.

**Answered when:** every row of `architecture.md`'s provisional table
is confirmed or replaced by a number, and anything still open is left
stated rather than implied.

# Agenda

Items to be done after the stages

- corpus.load_corpus: change so that notes can be text files
  regardless of extension
- A `tune` tool for corpus-adaptive knobs (k, resolution, and whether
  the evidence ever makes mutual depend on the corpus). Not now, for
  two recorded reasons: mutual needs no picking — its best beats
  plain's best on both fixture shapes (0.675/1.000 vs 0.435/1.000) —
  while the knobs that do vary, k and resolution, have only two shapes
  to fit a rule from; and the reference-free saturation signal a tune
  would need is unestablished (`benchmarks/structure.md`, "Against
  deciding without a reference"). Revisit when Stage 4's structure
  match can validate a rule against more scored corpora. Note the
  standing decisions it would meet: no config layer, so its only
  output could be per-run flag advice; sweep machinery lives in
  `scripts/`.
