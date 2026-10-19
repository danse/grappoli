# roadmap

Items to be done, delete once done:

- should qwen2.5 stay in benchmark_all? I think it proved not to be
  tool-capable?
- A `tune` tool for corpus-adaptive knobs (k, resolution, and whether
  the evidence ever makes mutual depend on the corpus). Not now, but the
  encoder swap sharpened what it would be for: mutual is a shape call,
  not a free choice — its best (0.904/0.783) wins the worst case only
  because plain (0.348/1.000) collapses on the saturated corpus, and
  loses outright on the separable one — while the knobs that do vary, k
  and resolution, have only two shapes to fit a rule from, and the
  reference-free saturation signal a tune would need is unestablished
  (`benchmarks/structure.md`, "Against deciding without a reference").
  Revisit when structure match can validate a rule against more scored
  corpora. Note the standing decisions it would meet: no config layer,
  so its only output could be per-run flag advice; sweep machinery lives
  in `scripts/`.
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
