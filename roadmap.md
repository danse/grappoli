# roadmap

The build order for `grappoli`. `product.md` states what it is and why;
`architecture.md` pins the decisions. This file is when each step
happens, what it has to answer, and what its tests have to pin. Stages
run in order — a stage is not finished until its tests are in `tests/`
and describe the behaviour rather than merely exercise it. Finished
stages are removed entirely, not marked; what they learned stays in
the tests and in `benchmarks/`.

## Stage 6 — The document

`grappoli show` prints one map for a reader: a deterministic projection
of `map.json`, `characterisations` and `relations`, with no model call
after the relations are written. It writes to standard output and not
into `<branch>/.grappoli/`, which is a build directory rather than an
output.

The page is the corpus's, not the model's. How well the model understood
is what faithfulness judges, and the loop's trace is a
development artefact; neither belongs here. So the document carries the
model's words verbatim — no paraphrase, no compression — because a
paraphrase is our understanding laid over the reader's, and no longer
shows what the map says.

The layout is a presentational choice still to be made, but nothing
pends on it: a characterisation survives (`architecture.md`,
Measurements) and the map sits flat (`architecture.md`, Graph). The
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
- add a multilingual fixture and run benchmarks on it
- widen the model comparison beyond the two downloaded models, on the
  relation loop's tool choice. Both fail it — 0 of 6 pairs in the shipped
  loop (`benchmarks/relations.md`, "What is not settled") — and the
  failure is unassisted tool use, not the corpus, so a model trained for
  tools is the thing to try. `qwen3:0.6b` and `functiongemma:270m` are the
  cheapest informative pair: small, CPU-only, both carry Ollama's `tools`
  capability, and `functiongemma` is a Gemma 3 270M fine-tuned for
  function calling, against the `gemma3:270m` already on disk that failed.
  No machinery is needed — `scripts/benchmark_all.py` takes
  `--models`/`--judges` — only a run. It runs as a named follow-up run,
  not by extending `DEFAULT_MODELS`: growing the default would change
  what a resumed batch covers, and the batch that has been measured so
  far stands as it is.
- A `tune` tool for corpus-adaptive knobs (k, resolution, and whether
  the evidence ever makes mutual depend on the corpus). Not now, for
  two recorded reasons: mutual needs no picking — its best beats
  plain's best on both fixture shapes (0.652/1.000 vs 0.435/1.000) —
  while the knobs that do vary, k and resolution, have only two shapes
  to fit a rule from; and the reference-free saturation signal a tune
  would need is unestablished (`benchmarks/structure.md`, "Against
  deciding without a reference"). Revisit when structure match can
  validate a rule against more scored corpora. Note the
  standing decisions it would meet: no config layer, so its only
  output could be per-run flag advice; sweep machinery lives in
  `scripts/`.
- explore an NLI cross-encoder as the faithfulness judge, decoupled from
  the model under test. The rubric is entailment — "supported when the
  notes state or directly entail it" — so a natural-language-inference
  model scores (region notes, `key_claim`) straight to
  entailment/neutral/contradiction (`cross-encoder/nli-deberta-v3-base`,
  `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli`), and `measure(llm=...)`
  is already the judge's injection seam. Small, CPU-only and effectively
  deterministic, so it would also settle the number that swings with the
  judge (0.842 under the 0.5B judge against 0.684 under 3B on the same
  in-domain map, `benchmarks/measurement.md`).
  It is a new measurement, not a free swap: the premise is a whole
  region's notes against a one-clause claim, the "or contradicts" clause
  needs the contradiction label, and the entailment cut-off is another
  provisional threshold.
