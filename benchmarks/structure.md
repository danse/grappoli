# Structure

Record of `scripts/benchmark_structure.py` runs, one report per corpus.
A report is a decision input: the winning row, where a reference gives
one, is what `build_map`'s defaults should become (`map.py`). Re-run
the script when a corpus you can score suggests otherwise.

Reports per corpus:

- **in-domain** (`tests/fixtures/in-domain`) — this file, below
- **heterogeneous** (`tests/fixtures/heterogeneous`) —
  `structure-heterogeneous.md`

The two reports disagree about the winning rule; `build_map`'s
defaults are the best worst-case row across both reports, not either
winner — the reasoning and the alternative candidates are in
`architecture.md` (Graph).

## Scoring correction (2026-10-16)

The sweep used to score a candidate partition with its own labelling:
every louvain community was a region, so the edge-less singleton given
to a note no neighbour refers to counted as a one-note region, and such
a stray could read as agreement against a reference that folds its own
strays under one label. `measure.map_labels` never did that — it drops
those singletons to `standalone`. The sweep now builds and labels its
candidates the same way (`_parts_at`, `_map_labels`), so one
configuration reports one ARI from either instrument. The numbers below
are the corrected sweep; the report that chose the current defaults,
before the correction, is `benchmarks/history/2026-10-08/structure.md`.

# Structure sweep — 2026-10-16

14 notes, scored against the reference with adjusted Rand index (ARI; 1 is the reference itself).

## Similarity
| provider | mean intra-region | mean inter-region |
|---|---|---|
| bge | 0.707 | 0.636 |
| tfidf | 0.087 | 0.047 |

## Sweep
| provider | k | mutual | weighted | resolution | regions | ARI |
|---|---|---|---|---|---|---|
| **bge** | 5 | yes | no | 1 | 3 | 0.652 |
| bge | 5 | yes | yes | 1 | 3 | 0.652 |
| bge | 5 | yes | no | 1.5 | 4 | 0.578 |
| bge | 5 | yes | yes | 1.5 | 4 | 0.578 |
| bge | 5 | yes | no | 2 | 4 | 0.578 |
| bge | 5 | yes | yes | 2 | 4 | 0.578 |
| bge | 4 | yes | no | 1 | 3 | 0.450 |
| bge | 4 | yes | yes | 1 | 3 | 0.450 |
| tfidf | 5 | yes | no | 1 | 3 | 0.450 |
| tfidf | 5 | yes | yes | 1 | 3 | 0.450 |
| bge | 2 | no | no | 1.5 | 5 | 0.435 |
| bge | 3 | yes | no | 1 | 4 | 0.435 |
| bge | 3 | yes | yes | 1 | 4 | 0.435 |
| bge | 3 | yes | no | 1.5 | 4 | 0.435 |
| bge | 3 | yes | yes | 1.5 | 4 | 0.435 |
| tfidf | 4 | yes | yes | 1 | 4 | 0.435 |
| tfidf | 4 | yes | yes | 1.5 | 4 | 0.435 |
| tfidf | 5 | yes | yes | 1.5 | 4 | 0.435 |
| tfidf | 4 | yes | yes | 2 | 5 | 0.425 |
| tfidf | 4 | yes | no | 1 | 3 | 0.408 |
| tfidf | 5 | yes | no | 2 | 6 | 0.382 |
| tfidf | 5 | yes | no | 1.5 | 5 | 0.355 |
| bge | 4 | yes | no | 2 | 4 | 0.348 |
| bge | 4 | yes | yes | 2 | 4 | 0.348 |
| tfidf | 4 | no | yes | 2 | 5 | 0.348 |
| tfidf | 4 | yes | no | 1.5 | 4 | 0.348 |
| bge | 2 | no | no | 1 | 4 | 0.343 |
| bge | 2 | no | yes | 1 | 4 | 0.343 |
| bge | 2 | no | yes | 1.5 | 4 | 0.343 |
| bge | 4 | yes | no | 1.5 | 3 | 0.343 |
| bge | 4 | yes | yes | 1.5 | 3 | 0.343 |
| bge | 2 | no | no | 2 | 6 | 0.329 |
| bge | 2 | no | yes | 2 | 6 | 0.329 |
| bge | 3 | no | yes | 2 | 6 | 0.329 |
| bge | 3 | yes | no | 2 | 5 | 0.305 |
| bge | 3 | yes | yes | 2 | 5 | 0.305 |
| tfidf | 3 | no | yes | 1.5 | 4 | 0.304 |
| tfidf | 3 | no | yes | 2 | 4 | 0.304 |
| tfidf | 4 | no | yes | 1.5 | 4 | 0.304 |
| tfidf | 3 | yes | yes | 1 | 4 | 0.282 |
| tfidf | 3 | yes | yes | 1.5 | 4 | 0.282 |
| tfidf | 3 | yes | yes | 2 | 4 | 0.282 |
| bge | 4 | no | no | 1 | 3 | 0.271 |
| tfidf | 2 | yes | no | 1 | 4 | 0.261 |
| tfidf | 2 | yes | yes | 1 | 4 | 0.261 |
| tfidf | 2 | yes | no | 1.5 | 4 | 0.261 |
| tfidf | 2 | yes | yes | 1.5 | 4 | 0.261 |
| tfidf | 2 | yes | no | 2 | 4 | 0.261 |
| tfidf | 2 | yes | yes | 2 | 4 | 0.261 |
| tfidf | 5 | no | yes | 1.5 | 5 | 0.261 |
| bge | 4 | no | yes | 1 | 3 | 0.257 |
| bge | 4 | no | yes | 1.5 | 5 | 0.241 |
| tfidf | 2 | no | yes | 2 | 5 | 0.241 |
| tfidf | 4 | yes | no | 2 | 5 | 0.233 |
| tfidf | 2 | no | yes | 1 | 4 | 0.188 |
| tfidf | 2 | no | yes | 1.5 | 4 | 0.188 |
| tfidf | 3 | no | yes | 1 | 4 | 0.188 |
| bge | 5 | no | yes | 1 | 3 | 0.182 |
| bge | 4 | no | no | 2 | 7 | 0.176 |
| bge | 4 | no | yes | 2 | 7 | 0.176 |
| bge | 5 | no | yes | 2 | 8 | 0.176 |
| bge | 2 | yes | no | 2 | 5 | 0.174 |
| tfidf | 3 | yes | no | 1 | 4 | 0.174 |
| tfidf | 3 | yes | no | 1.5 | 4 | 0.174 |
| tfidf | 4 | no | yes | 1 | 3 | 0.158 |
| tfidf | 3 | yes | no | 2 | 5 | 0.156 |
| bge | 2 | yes | no | 1 | 4 | 0.140 |
| bge | 2 | yes | yes | 1 | 4 | 0.140 |
| bge | 2 | yes | no | 1.5 | 4 | 0.140 |
| bge | 2 | yes | yes | 1.5 | 4 | 0.140 |
| bge | 2 | yes | yes | 2 | 4 | 0.140 |
| tfidf | 3 | no | no | 1 | 2 | 0.140 |
| tfidf | 5 | yes | yes | 2 | 5 | 0.137 |
| bge | 5 | no | no | 2 | 9 | 0.132 |
| tfidf | 5 | no | yes | 2 | 6 | 0.119 |
| tfidf | 4 | no | no | 1 | 3 | 0.100 |
| tfidf | 3 | no | no | 1.5 | 5 | 0.087 |
| tfidf | 2 | no | no | 1 | 3 | 0.081 |
| tfidf | 2 | no | no | 1.5 | 3 | 0.081 |
| tfidf | 4 | no | no | 2 | 7 | 0.074 |
| bge | 5 | no | yes | 1.5 | 5 | 0.072 |
| tfidf | 5 | no | yes | 1 | 3 | 0.071 |
| bge | 5 | no | no | 1 | 3 | 0.061 |
| tfidf | 3 | no | no | 2 | 6 | 0.057 |
| bge | 3 | no | no | 2 | 6 | 0.041 |
| tfidf | 2 | no | no | 2 | 6 | 0.041 |
| bge | 3 | no | no | 1 | 2 | 0.039 |
| bge | 3 | no | yes | 1 | 2 | 0.039 |
| tfidf | 4 | no | no | 1.5 | 4 | 0.033 |
| bge | 5 | no | no | 1.5 | 4 | 0.022 |
| tfidf | 5 | no | no | 1 | 3 | 0.000 |
| bge | 3 | no | no | 1.5 | 5 | -0.012 |
| bge | 3 | no | yes | 1.5 | 5 | -0.012 |
| bge | 4 | no | no | 1.5 | 5 | -0.012 |
| tfidf | 5 | no | no | 1.5 | 5 | -0.096 |
| tfidf | 5 | no | no | 2 | 8 | -0.122 |

## Best map (by ARI)
_Decided: bge, k=5, mutual=yes, weighted=no, resolution=1, ARI 0.652._

### bge at its own best
- r0: cellar-temperature-notes.md, kimchi-microbiology.md, lacto-fermentation-101.md, sourdough-starter-rhythm.md
- r1: cucumber-pickling-log.md, quick-pickles-vinegar-ratio.md, salt-brine-basics.md
- r2: osmosis-and-salt.md, ph-and-spoilage.md, vinegar-chemistry.md
- standalone: airlock-checks.md, book-recommendations.md, jar-inventory.md, neighbour-garden-trade.md

### tfidf at its own best
- r0: airlock-checks.md, cellar-temperature-notes.md, jar-inventory.md
- r1: cucumber-pickling-log.md, kimchi-microbiology.md, osmosis-and-salt.md, quick-pickles-vinegar-ratio.md, salt-brine-basics.md
- r2: lacto-fermentation-101.md, ph-and-spoilage.md, sourdough-starter-rhythm.md, vinegar-chemistry.md
- standalone: book-recommendations.md, neighbour-garden-trade.md

## Reading (2026-10-16)

Mutual filtering rescues the rule. Plain kNN at k=5 — the default before
this run — scored ARI 0.061, indistinguishable from chance. The same
neighbourhood size with only reciprocal edges kept scores 0.652. One-way
edges were the problem, not the neighbourhood size: a popular note pulls
its would-be neighbours in with it, and louvain merged the result. This
decision is baked into `build_map`'s defaults (`mutual = true`); the
sweep is what revisits it.

bge beats tfidf but not cleanly. Both providers peak on mutual-filtered
graphs at 0.652 vs 0.450. bge gets brine and chemistry exactly and
leaves both true strays alone, but shreds equipment-and-storage —
cellar-temperature's top neighbours are biology notes, so it joins the
biology region and airlock-checks and jar-inventory stand alone. tfidf
finds the equipment region perfectly and mangles the rest. The
embedder's weakness is localised, and scoring it is exactly what
structure match exists for.

## Against deciding without a reference

The sweep needs a reference because nothing else reproduces structure
match. Measured on this corpus: silhouette correlates with ARI at +0.27
overall (−0.02 for bge, +0.75 for tfidf) and its best pick scores 0.13
(bge) / 0.31 (tfidf) against the reference-best 0.68 / 0.40;
leave-one-out stability correlates +0.40 and its picks over-fragment
(k=2 mutual gave 8–9 regions). Report them all — decide by none. A
reference is cheap for a fourteen-note corpus and worth writing for
anything you will base conclusions on.

**Saturation detection does not escape this (2026-10-08).** The
intra/inter similarity margin that separates the two fixture shapes
(0.07 in-domain vs 0.13 heterogeneous, fixtures/README.md) is a
labeled measure — it needs the reference to know which pairs are
same-region. The reference-free proxies checked on both shapes do not
reproduce it: overall mean similarity points the expected way (0.646
saturated vs 0.574 separable), but the p10–p90 spread is *wider* on
the saturated corpus (0.221 vs 0.196), confounded by strays whose low
pairs widen the tail, and the labeled margin itself moves opposite for
tfidf (0.040 in-domain → 0.031 heterogeneous, where bge's grows
0.07 → 0.13). Two shapes, one ambiguous scalar, one inverted sign — a
reference-free saturation signal is unestablished, same verdict as the
criteria above.

**Reproduced (2026-10-13).** The batch reran the sweep and returned the
same best rows — bge k=5 mutual at 0.675, tfidf 0.398 at its own best
(the pre-correction scoring; the corrected values are the reading
above) — so the rule's shape is unchanged by a fresh run. It is the
reproduction behind closing the region-rule and embedder rows in
`architecture.md` (`benchmarks/runs/2026-10-13/run.json`).

## Coarser resolution (2026-10-15)

The in-domain map makes four regions, as the reference does, but not the
same four: `cellar-temperature` joins the biology notes and
`airlock-checks` and `jar-inventory` stand alone, so equipment-and-storage
is dismantled rather than split by granularity. Going coarser was the
obvious repair, and the sweep had never gone below resolution 1.0.
Extending it there does not help. In-domain's best remains at resolution
1.0 (0.652); at 0.7 the same rule merges to two regions and falls to
0.442. The separable corpus is the same story from the other side: 1.000
at 1.5–2, 0.774 at 0.5–1.0. The best worst-case setting across both
shapes is unchanged — bge, k=5, mutual, weighted, resolution 2.0, at
0.578 / 0.729 — so `build_map`'s defaults stand
(`benchmarks/history/2026-10-15/structure.md`).
