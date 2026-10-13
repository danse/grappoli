# roadmap

The build order for `grappoli`. `product.md` states what it is and why;
`architecture.md` pins the decisions. This file is when each step
happens, what it has to answer, and what its tests have to pin. Stages
run in order — a stage is not finished until its tests are in `tests/`
and describe the behaviour rather than merely exercise it. Finished
stages are removed entirely, not marked; what they learned stays in
the tests and in `benchmarks/`.

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

## Stage 6 — The document

`grappoli show` prints one map for a reader: a deterministic projection
of `map.json`, `characterisations` and `relations`, with no model call
after Stage 3. It writes to standard output and not into
`<branch>/.grappoli/`, which is a build directory rather than an output.

The page is the corpus's, not the model's. How well the model understood
is what Stage 4's faithfulness judges, and the loop's trace is a
development artefact; neither belongs here. So the document carries the
model's words verbatim — no paraphrase, no compression — because a
paraphrase is our understanding laid over the reader's, and no longer
shows what the map says.

The layout is left open until Stage 5 settles the map it has to show:
flat or nested, and whether a characterisation survives at all. The
content contract is fixed now — every region; its characterisation where
one exists; every relation, once, between characterised regions; and the
notes that stand alone. An input missing a characterisation or a relation
is rendered as a gap rather than filled in, so a partial build reads as
partial.

**Tests pin:** the document is a function of the three inputs; each
region, each stored relation exactly once however the pair is keyed, and
each standalone note appear; relation statements are verbatim; a missing
characterisation or relation is rendered as incomplete rather than
invented.

**Answered when:** `grappoli show` prints a page a reader can act on
without opening `.grappoli/`.

# Agenda

Items to be done after the stages

- corpus.load_corpus: change so that notes can be text files
  regardless of extension
- make multilingual with `stopwordsiso`
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
