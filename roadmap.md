# roadmap

Items to be done, delete once done:

- Should the shipped relation loop move to the structured channel? The
  native one is the loop's settled shape — the model, not the
  orchestration, chooses what to read and which pair to relate — and it
  writes nothing: `grappoli read` left every pair missing on both models
  in all six cells of the 2026-10-20 batch, the 0.5B naming no tool at
  all and the 3B's arguments malformed every time
  (`benchmarks/relations.md`, "What is not settled"). The structured
  channel is valid in all 18 cells of the same batch, at a call per pair
  (81–269 s each) against a native whole-map call that returns nothing
  (225–986 s). What it costs is the shape: one relation per call, so the
  orchestration has to enumerate the pairs and the model's choice of what
  to read goes with it. So the question is not which channel parses but
  what the loop is for — a map with no relations, or a map whose relations
  the orchestration enumerated. Settle it by building the structured loop
  and reading what it writes: the probe measures whether a call parses,
  not whether the relation it returns is true to the notes. Note the
  standing decision it would meet: the native channel shipped because it
  is the only one where the loop recovers
  (`benchmarks/relations.md`, "What the shape rests on").
- Improve the multilingual map. The default rule scores ARI -0.044 on the
  mixed Italian/English corpus and nothing in the sweep beats 0.212, so
  the rule is not the whole of it: the encoder's margin collapses there
  (mean intra 0.798 against inter 0.774, a 0.024 gap, against 0.034
  in-domain and 0.045 heterogeneous), and what it clusters is legible —
  the three Italian notes into one region whatever their topic (the
  kayak note with the two photography ones), the English kayak notes with
  the English beekeeping notes, both reference standalones pulled inside
  regions, the one Italian fungus pair right. The reference cuts across
  languages and the encoder cuts along them. What settles it is a
  structure reading for this corpus — whether any rule the pipeline can
  use reproduces that partition, or the reference is the wrong target
  (`benchmarks/structure.md`, "Reading (2026-10-16)") — and, whatever the
  answer, what a third shape does to the tune tool, which now has a shape
  it fails (`benchmarks/structure.md`, "Against deciding without a
  reference").
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
