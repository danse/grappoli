# grappoli

## What it is

A local command that reads a branch of notes and produces a map of what it
holds: which regions there are, what each one is about, and how they touch.

`grappoli` does not answer questions about a corpus, and the
difference is the point of it: for a corpus too large to read, an
answer is the wrong artefact.

## The problem

A branch grows past the point where it can be read, and the usual remedies
all fail in the same way. Searching finds what you already named. Skimming
the file list finds what you already remember. Both require knowing what you
are looking for, which is the thing a forgotten corpus cannot supply.

What is missing is not a better search. It is a statement of what is here,
what it touches, and what nothing else refers to.

## What it produces

Regions of the corpus, each characterised from the notes it holds, with the
relations between regions stated rather than implied. The two figures a
reader can act on are which regions are worth opening and which notes stand
alone.

The output is meant to be read rather than queried. It should be legible in
one pass and useful without following any instruction.

## Approach

Tentative, and stated as a hypothesis rather than a design.

Divide the corpus into regions. For each region, select a small set of notes
that represents it, then characterise the region from those notes alone.
Characterise the relations between regions from the characterisations rather
than from the notes, so that no step has to hold the whole corpus in view.

The claim underneath is that the structure does the global work and a
model does only the local parts. Characterising one region from five
notes is a small task; holding sixteen regions in view at once is not,
and it is the step where earlier attempts failed. Whether the
structure earns its keep is what the measurement has to decide, not
this paragraph.

Selection of representatives is a computation over the corpus rather than a
judgement, and it happens before any model is consulted. A model that runs
after the structure is fixed is answering a small question inside a decided
frame, which is the only shape this hardware supports.

## Measured

Four, and the second one exists because of the first.

**Comprehensiveness** — what share of the corpus has a home in the map.
**Redundancy** — how much of the map says the same thing twice. These are
measured together because redundancy reads as comprehensiveness: a summary
that repeats itself five ways covers five regions and says two things, and
measuring coverage alone optimises straight into it.

**Faithfulness** — whether any characterisation claims something its notes do
not support. This is the one a small model fails at while sounding fluent,
and a judge without an explicit rubric rewards the fluency.

**Structure match** — whether the regions agree with what a reader would
write by hand from reading the notes.

None of the four can weigh whether to produce a characterisation at all:
two read only the map, redundancy is `0` when there are none, and
faithfulness scores one that exists. They police the characterisation;
they do not justify it (`architecture.md`, Measurements).

Reference metrics are not used. ROUGE scores copying, so it ranks extractive
output above the abstraction the project exists to produce.

## Decided

The build order and the reasoning behind each step are in `roadmap.md`.
The decisions taken before any code exists:

**Regions are communities in a note-similarity graph.** Build a k-nearest
neighbour graph over the notes, run community detection, and the regions
are what falls out. The relations between regions are the cross-community
edges, so the map's two figures come from one computation rather than two.

**The map sits flat.** Structure match cannot settle nesting: it scores
a flat partition, so a level above the regions is invisible to it and a
level below only ever splits the reference's own regions. Coarsening the
cut was measured worse on both fixtures, so flat is the shape the
measurements reach (`architecture.md`, Graph; `benchmarks/structure.md`,
"Coarser resolution (2026-10-15)").

**Representative selection is deterministic** — centrality within the
region, redundancy reduced by marginal gain. It makes no model calls.

**The model is qwen2.5:0.5b, run locally through Ollama.** Small enough
that its failures are visible rather than rare, which is what the
faithfulness measurement exists to catch. It sits behind a single
interface so that larger models can be compared without rework.

**The agent is a hand-rolled tool loop,** roughly a hundred and fifty
lines, with no framework. Its tools expose characterisations and never
raw notes: the restriction that the corpus is never held in view is
enforced by what the agent can ask for, not by what it is told.
