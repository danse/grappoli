# roadmap

The build order for `grappoli`. `product.md` states what it is and why;
`architecture.md` pins the decisions. This file is when each step
happens, what it has to answer, and what its tests have to pin. Stages
run in order — a stage is not finished until its tests are in `tests/`
and describe the behaviour rather than merely exercise it.

## Stage 0 — Environment and throughput

Create the project venv and the fixture corpus: a small branch of
markdown notes, hand-written so the correct regions are known in
advance. Stage 4's structure match scores against it.

Then **measure how fast the model actually is.** One representative
request — prompt of a few hundred tokens, generation of a few hundred —
recorded as prefill and generation tokens per second. The probe so far
gave 2.1 tok/s prefill and 1.3 tok/s generation, 106 s for a trivial
call, which is either a real limit of 2 cores or thread starvation; find
out which here. Every later stage is sized by this number: how many
rounds Stage 3 can afford, how many regions Stage 2 can characterise,
whether generation calls are affordable at all.

**Answered when:** the suite runs, the fixture corpus exists with its
reference regions, `bge-small` produces vectors for them, and there is a
throughput figure on the record.

## Stage 1 — Structure, no model

`notes → similarity (bge-small ∥ TF-IDF) → kNN graph → community
detection → regions → representative selection → map.json`

No generation calls, per the spec: selection is a computation over the
corpus before any model is consulted. TF-IDF runs beside the encoder as
the control — if learned vectors do not beat bag-of-words on structure
match, they are not earning their place.

Regions are the graph's communities; the edges between them are the
cross-community edges, so both figures come from one computation.

**Tests pin:** every note has a home or is explicitly flagged
standalone; the region rule is deterministic on a fixed corpus; edges
are derived from the graph rather than hand-listed; selection makes no
model calls.

**Answered when:** the map holds together with no model involved — the
claim that structure does the global work.

## Stage 2 — Characterisation, one region at a time

Five representative notes → prompt → structured characterisation,
validated. Retry on malformed output, log the failures rather than
swallowing them.

Structured output goes through the model's native tool-call mechanism,
which the Stage 0 probe confirmed works at 0.5B: it emitted a correct
name and correct arguments with empty content. JSON-in-content stays
the fallback if a particular schema trips it. The model sits behind a
single interface so Stage 5 can swap it without rework.

Retries cost real seconds at measured throughput, so they are capped
and their cost logged alongside the failure.

**Tests pin:** parsing, retry and cap behaviour; what the model
actually gets wrong, recorded as observed failures rather than
expected ones.

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

Round budget is set by Stage 0's throughput figure, with a hard cap
regardless: at 1.3 tok/s an unbounded loop is not a bug, it is a hung
machine.

**Tests pin:** the loop terminates under adversarial tool output; tool
errors are recoverable; no path reaches a raw note; relations are
written between characterisations only. The model is stubbed with a
scripted call sequence so all of this runs without Ollama and without
nondeterminism.

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
