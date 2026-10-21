# Relations

The loop that states, in words, how two regions touch. Its shape is
settled: the orchestration names each touching pair and the model is
asked for one relation in one call, from the two characterisations and
nothing else. The whole-map conversation, in which the model names the
tools and chooses what to read and which pair to relate, is still there
and still selectable (`--relation-channel native`); it writes no
relations on either model.

The loop is `src/grappoli/relations.py` (`relate_pairs`), its tool
surface and resume guarantee are in `architecture.md` (Agent tools), and
its behaviour is pinned in `tests/test_relations.py`. A relation is one
appended line keyed by the unordered pair, so a resumed run retries only
the pairs still missing and never regenerates a completed one.

## What the shape rests on

The channel was the decisive measurement, and the 2026-10-20 batch settled
it (`benchmarks/runs/2026-10-20/run.json`). The probe sends the task at
three conversation sizes — per edge, per region, whole map — in both
channels, over the three corpora and the two models: eighteen calls a
channel.

| channel | valid relation | seconds a call |
|---|---|---|
| native (tools only) | 0 of 18 | 84–986 |
| structured (one-relation `format`) | 18 of 18 | 81–645 |

On the shape that ships — one pair a call — the structured channel took
81–269 s. What that decided is not which channel parses: the shape was
never the blocker, and a `format`-constrained schema returns a valid
relation in every cell. It decided what the shipped step is, because a
map whose relations do not exist is not a map with relations in it. On
the native channel a `grappoli read` wrote no relations at all, in any of
the six cells of that batch: eleven touching pairs across the three
corpora, none of them related on either model, every read exiting
non-zero — the 0.5B naming no tool at all, and the 3B's arguments
malformed every time.

The probe asks one pair per cell, so it also says what the answers are
worth. Of the six structured statements at the pair size, the 3B's three
are relations — "The region focusing on temperature control for
fermentation differs from the refrigerator pickling method…", "The region
of bicycle maintenance touches the region of git commit hooks…" — while
the 0.5B's three are one relation, one falsehood ("Region 0 touches
Region 1, as both are involved in managing and reviewing code changes",
where region 0 is the drivetrain) and one juxtaposition of two sentences
that never says how the regions touch. The channel makes the model
answer; the model still has to be one that answers. The shipped prompt
carries the reduced loop's block — each region's about, topics and
claims — and no worked example, which was the confound that made the
native loop copy its example verbatim; that loop at 3B covered six
pairs of six, every statement about the two regions it named
(`benchmarks/history/2026-10-12/relations.md`).

The cost of the split is the model's choice of what to relate. On the
native channel the model chooses which region to read and which pair to
relate; on the pair loop the orchestration enumerates the pairs, so every
touching pair is related rather than the ones the model got to. The
product's own claim is that the structure does the global work and a
model does only the local parts (`product.md`, Approach), and one
question about two regions is local in the way a sixteen-region
conversation is not. The native channel stays selectable, because the
choice is what it exists to produce and is worth being able to run.

Two cautions for any change to the prompt, both recorded as failures
first: a model will reach for a `done` tool the schemas do not define
(the stop is a message naming no tool), and it copies a worked example
verbatim — the shipped prompt carries none, and should keep it that way.

One live run of the shipped path (2026-10-21, the multilingual corpus at
0.5B, both touching pairs) puts a number on the shipped prompt: 480 s
and 352 s a pair, against 84–106 s for the probe's pair-size prompt,
because the shipped prompt carries both regions' topics and claims and
the model answers at length. What it wrote is worse than long. The (0,1)
statement paraphrases region 0's kayak and film notes in Italian, and
region 1's mushrooms and honey are nowhere in it; the (2,3) statement is
the forward stroke, with region 3's bees and mushrooms nowhere in it.
Both are about notes rather than about the two regions they name, and
neither says how those regions touch. The shape is right, and the 0.5B
fills it with one region's material instead of a relation between two.

The shipped model writes the relation. Asked the same (0,1) pair the
same day, with its own characterisations of the same map,
llama3.2:latest answered in 861 s: "Region 0, which focuses on boat
handling, photography, and mycology, shares the common ground of
recognizing edible fungi, while differing in its emphasis on keeping the
center of gravity low compared to Region 1, which prioritizes mushroom
conservation and honey production methods…" — the common ground and the
difference, named for both regions, which is what the step asks for. It
is one long sentence rather than a short one, and it costs about twice
what the 0.5B's answer cost.

## What is not settled

What the loop writes, read for truth. The probe measures whether a call
comes back well-formed, not whether the relation it returns is true of
the notes, and those are different questions: a sentence can parse
perfectly and say something the notes do not hold — the 0.5B's statement
about code changes is one, and the live run above is what truth looks
like at 0.5B on two pairs: well-formed, and about one region. The
batch's `relation_loop` step is the instrument for it
(`scripts/benchmark_relation_loop.py`): it runs the shipped loop over
every touching pair of a cell, judges each statement against the notes
of the two regions it names — the notes that would have to bear it out,
the same evidence the faithfulness judge uses for a claim — and records
the cost of each pair and the page the relations render. The numbers
land in the batch's record under `relation_loop`, and the reading they
produce belongs in this file.

## The trail

Every configuration that led here is under `history/<date>/relations.md`,
by the date it was run — 2026-10-09, 2026-10-12, 2026-10-13 — with the
numbers and the raw replies. The batch in `benchmarks/README.md` reruns
`scripts/benchmark_relations.py`, both channels, under the current
defaults, and the shipped loop through
`scripts/benchmark_relation_loop.py`; this file is replaced by that
reading, not appended to.
