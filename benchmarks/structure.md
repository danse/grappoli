# Structure

Record of `scripts/benchmark_structure.py` runs, one report per corpus.
A report is a decision input: the winning row, where a reference gives
one, is what `build_map`'s defaults should become (`map.py`). Re-run
the script when a corpus you can score suggests otherwise.

Reports per corpus:

- **in-domain** (`tests/fixtures/in-domain`) — this file, below
- **heterogeneous** (`tests/fixtures/heterogeneous`) —
  `structure-heterogeneous.md`

The reports disagree about the winning rule; `build_map`'s defaults are
the best worst-case row across both, not necessarily either winner — the
reasoning and the alternative candidates are in `architecture.md`
(Graph). The sweep below is the multilingual one; the English sweep it
replaced, which chose the previous defaults, is under
`benchmarks/history/2026-10-16/`.

## Scoring correction (2026-10-16)

The sweep used to score a candidate partition with its own labelling:
every louvain community was a region, so the edge-less singleton given
to a note no neighbour refers to counted as a one-note region, and such
a stray could read as agreement against a reference that folds its own
strays under one label. `measure.map_labels` never did that — it drops
those singletons to `standalone`. The sweep now builds and labels its
candidates the same way (`_parts_at`, `_map_labels`), so one
configuration reports one ARI from either instrument. The English sweep
that carries the correction is under
`benchmarks/history/2026-10-16/structure.md`; an earlier report, before
the correction, is `benchmarks/history/2026-10-08/structure.md`.

# Structure sweep — 2026-10-16

14 notes, scored against the reference with adjusted Rand index (ARI; 1 is the reference itself).

## Similarity
| provider | mean intra-region | mean inter-region |
|---|---|---|
| e5 | 0.876 | 0.842 |
| tfidf | 0.090 | 0.049 |

## Sweep
| provider | k | mutual | weighted | resolution | regions | ARI |
|---|---|---|---|---|---|---|
| **e5** | 4 | yes | no | 2 | 5 | 0.904 |
| e5 | 4 | yes | yes | 2 | 5 | 0.904 |
| e5 | 4 | yes | no | 1 | 4 | 0.783 |
| e5 | 4 | yes | yes | 1 | 4 | 0.783 |
| e5 | 4 | yes | no | 1.5 | 4 | 0.783 |
| e5 | 4 | yes | yes | 1.5 | 4 | 0.783 |
| e5 | 5 | yes | no | 1 | 4 | 0.783 |
| e5 | 5 | yes | no | 1.5 | 5 | 0.712 |
| e5 | 5 | yes | yes | 1.5 | 5 | 0.712 |
| e5 | 5 | yes | no | 2 | 5 | 0.712 |
| e5 | 5 | yes | yes | 2 | 5 | 0.712 |
| e5 | 3 | yes | no | 1 | 3 | 0.652 |
| e5 | 3 | yes | yes | 1 | 3 | 0.652 |
| e5 | 3 | yes | no | 1.5 | 3 | 0.652 |
| e5 | 3 | yes | yes | 1.5 | 3 | 0.652 |
| e5 | 5 | yes | yes | 1 | 4 | 0.609 |
| tfidf | 2 | yes | yes | 1 | 4 | 0.435 |
| e5 | 3 | yes | no | 2 | 5 | 0.397 |
| e5 | 3 | yes | yes | 2 | 5 | 0.397 |
| tfidf | 5 | yes | no | 2 | 6 | 0.382 |
| e5 | 3 | no | no | 2 | 5 | 0.348 |
| e5 | 3 | no | yes | 2 | 5 | 0.348 |
| tfidf | 5 | yes | no | 1.5 | 4 | 0.348 |
| e5 | 4 | no | no | 1.5 | 4 | 0.338 |
| e5 | 4 | no | yes | 1.5 | 4 | 0.338 |
| e5 | 2 | no | yes | 1 | 3 | 0.335 |
| e5 | 3 | no | no | 1 | 3 | 0.335 |
| e5 | 3 | no | yes | 1 | 3 | 0.335 |
| e5 | 4 | no | no | 1 | 3 | 0.335 |
| e5 | 4 | no | yes | 1 | 3 | 0.335 |
| tfidf | 5 | no | yes | 1 | 3 | 0.335 |
| e5 | 4 | no | no | 2 | 5 | 0.304 |
| e5 | 4 | no | yes | 2 | 5 | 0.304 |
| e5 | 2 | yes | no | 1 | 3 | 0.304 |
| e5 | 2 | yes | no | 1.5 | 3 | 0.304 |
| tfidf | 5 | yes | no | 1 | 3 | 0.304 |
| tfidf | 5 | yes | yes | 1 | 3 | 0.304 |
| e5 | 3 | no | no | 1.5 | 4 | 0.265 |
| e5 | 3 | no | yes | 1.5 | 4 | 0.265 |
| e5 | 2 | no | no | 2 | 5 | 0.261 |
| e5 | 2 | no | yes | 2 | 5 | 0.261 |
| tfidf | 2 | yes | no | 1 | 4 | 0.261 |
| tfidf | 2 | yes | no | 1.5 | 4 | 0.261 |
| tfidf | 2 | yes | yes | 1.5 | 4 | 0.261 |
| tfidf | 2 | yes | no | 2 | 4 | 0.261 |
| tfidf | 2 | yes | yes | 2 | 4 | 0.261 |
| tfidf | 4 | yes | yes | 1 | 4 | 0.261 |
| tfidf | 4 | yes | yes | 1.5 | 4 | 0.261 |
| e5 | 2 | no | no | 1.5 | 4 | 0.247 |
| e5 | 2 | no | yes | 1.5 | 4 | 0.247 |
| tfidf | 4 | no | yes | 1.5 | 5 | 0.241 |
| e5 | 2 | yes | yes | 1 | 3 | 0.230 |
| e5 | 2 | yes | yes | 1.5 | 3 | 0.230 |
| e5 | 2 | yes | no | 2 | 4 | 0.222 |
| e5 | 2 | no | no | 1 | 3 | 0.195 |
| tfidf | 4 | no | yes | 1 | 3 | 0.195 |
| tfidf | 4 | no | yes | 2 | 6 | 0.192 |
| tfidf | 5 | yes | yes | 1.5 | 4 | 0.192 |
| tfidf | 3 | no | yes | 1.5 | 4 | 0.188 |
| tfidf | 3 | no | yes | 2 | 5 | 0.174 |
| tfidf | 4 | yes | no | 1 | 4 | 0.174 |
| tfidf | 4 | yes | no | 1.5 | 4 | 0.174 |
| tfidf | 3 | yes | no | 1 | 3 | 0.172 |
| tfidf | 3 | yes | no | 1.5 | 3 | 0.172 |
| tfidf | 5 | no | yes | 1.5 | 4 | 0.172 |
| tfidf | 2 | no | yes | 1.5 | 4 | 0.157 |
| e5 | 5 | no | no | 1.5 | 5 | 0.157 |
| e5 | 5 | no | yes | 1.5 | 5 | 0.157 |
| tfidf | 3 | yes | yes | 1.5 | 4 | 0.157 |
| tfidf | 3 | yes | yes | 2 | 4 | 0.157 |
| e5 | 5 | no | no | 2 | 7 | 0.156 |
| e5 | 5 | no | yes | 2 | 7 | 0.156 |
| tfidf | 4 | yes | no | 2 | 5 | 0.156 |
| tfidf | 4 | yes | yes | 2 | 5 | 0.156 |
| tfidf | 5 | no | yes | 2 | 7 | 0.156 |
| tfidf | 5 | no | no | 1 | 3 | 0.145 |
| e5 | 2 | yes | yes | 2 | 4 | 0.140 |
| e5 | 5 | no | no | 1 | 2 | 0.131 |
| tfidf | 2 | no | no | 1.5 | 5 | 0.087 |
| tfidf | 2 | no | yes | 2 | 5 | 0.087 |
| tfidf | 3 | no | no | 1.5 | 5 | 0.087 |
| tfidf | 4 | no | no | 1.5 | 5 | 0.087 |
| tfidf | 3 | yes | yes | 1 | 3 | 0.084 |
| e5 | 5 | no | yes | 1 | 3 | 0.081 |
| tfidf | 2 | no | yes | 1 | 3 | 0.081 |
| tfidf | 3 | no | yes | 1 | 3 | 0.081 |
| tfidf | 5 | yes | yes | 2 | 6 | 0.074 |
| tfidf | 5 | no | no | 1.5 | 5 | 0.058 |
| tfidf | 2 | no | no | 2 | 6 | 0.057 |
| tfidf | 3 | no | no | 2 | 6 | 0.057 |
| tfidf | 3 | yes | no | 2 | 5 | 0.026 |
| tfidf | 3 | no | no | 1 | 3 | 0.018 |
| tfidf | 2 | no | no | 1 | 3 | 0.000 |
| tfidf | 5 | no | no | 2 | 8 | -0.015 |
| tfidf | 4 | no | no | 2 | 6 | -0.077 |
| tfidf | 4 | no | no | 1 | 3 | -0.172 |

## Best map (by ARI)
_Decided: e5, k=4, mutual=yes, weighted=no, resolution=2, ARI 0.904._

### e5 at its own best
- r0: airlock-checks.md, jar-inventory.md
- r1: cellar-temperature-notes.md
- r2: cucumber-pickling-log.md, quick-pickles-vinegar-ratio.md, salt-brine-basics.md
- r3: kimchi-microbiology.md, lacto-fermentation-101.md, sourdough-starter-rhythm.md
- r4: osmosis-and-salt.md, ph-and-spoilage.md, vinegar-chemistry.md
- standalone: book-recommendations.md, neighbour-garden-trade.md

### tfidf at its own best
- r0: cellar-temperature-notes.md, jar-inventory.md
- r1: cucumber-pickling-log.md, quick-pickles-vinegar-ratio.md, salt-brine-basics.md
- r2: kimchi-microbiology.md, sourdough-starter-rhythm.md
- r3: lacto-fermentation-101.md, ph-and-spoilage.md, vinegar-chemistry.md
- standalone: airlock-checks.md, book-recommendations.md, neighbour-garden-trade.md, osmosis-and-salt.md

## Reading (2026-10-16)

The multilingual encoder lifts the rule well past where the English one
left it. Its best row is mutual-filtered k=4 at resolution 2, ARI 0.904 —
up from the English 0.652 — reached from the corner that sweep also
favoured (a reciprocal-edge neighbourhood), just smaller: at k=5 the
mutual graph over-merges and the same rule drops to 0.712. Mutual
filtering still does the work here — plain k=4 at resolution 2 scores
0.304 against 0.904 mutual-filtered, so one-way edges were the problem
again.

The encoder beats tfidf on both shapes, and by more than before (0.904
against 0.435 in-domain). It holds brine, biology and chemistry whole
and leaves both true strays alone; what it still misses is
equipment-and-storage, which it splits — `cellar-temperature` gathers no
reciprocal neighbour and stands alone while `airlock-checks` and
`jar-inventory` pair — the same region the English encoder dismantled.
The embedder's weakness stays localised, which is what scoring the
control is for.

## Against deciding without a reference

The sweep needs a reference because nothing else reproduces structure
match. Measured on the English sweep: silhouette correlates with ARI at
+0.27 overall (−0.02 for the English encoder, +0.75 for tfidf) and its
best pick scores 0.13 (the English encoder) / 0.31 (tfidf) against the
reference-best 0.68 / 0.40; leave-one-out stability correlates +0.40 and
its picks over-fragment (k=2 mutual gave 8–9 regions). Report them all —
decide by none. A reference is cheap for a fourteen-note corpus and worth
writing for anything you will base conclusions on.

**Saturation detection does not escape this (2026-10-08).** The
intra/inter similarity margin that separates the two fixture shapes
(0.07 in-domain vs 0.13 heterogeneous, fixtures/README.md) is a
labeled measure — it needs the reference to know which pairs are
same-region. The reference-free proxies checked on both shapes do not
reproduce it: overall mean similarity points the expected way (0.646
saturated vs 0.574 separable), but the p10–p90 spread is *wider* on
the saturated corpus (0.221 vs 0.196), confounded by strays whose low
pairs widen the tail, and the labeled margin itself moves opposite for
tfidf (0.040 in-domain → 0.031 heterogeneous, where the English encoder's grows
0.07 → 0.13). Two shapes, one ambiguous scalar, one inverted sign — a
reference-free saturation signal is unestablished, same verdict as the
criteria above.

**Reproduced (2026-10-13).** The batch reran the English sweep and
returned the same best rows — bge k=5 mutual at 0.675, tfidf 0.398 at
its own best (the pre-correction scoring; the corrected values are the
reading above) — so the rule's shape is unchanged by a fresh run. It is the
reproduction behind closing the region-rule and embedder rows in
`architecture.md` (`benchmarks/runs/2026-10-13/run.json`).


## Coarser resolution (2026-10-15)

The in-domain map splits equipment-and-storage rather than homing it, so
coarser granularity was the obvious repair, and the sweep had never gone
below resolution 1.0. On the English sweep it did not help: in-domain's
best stayed at resolution 1.0 (0.652) and merged to two regions at 0.7;
the separable corpus fell from 1.000 to 0.774 over the same range. The
direction is closed in that measurement; the multilingual sweep keeps to
1.0 and above, and its winner sits at 2.0 on both shapes
(`benchmarks/history/2026-10-15/structure.md`).
