# Structure — experiment, 2026-10-08

The sweep that first chose `build_map`'s defaults, reproduced by the
2026-10-13 batch. It scored every louvain community as a region,
including the edge-less singleton given to a note no neighbour refers
to — a labelling `measure` never used. On 2026-10-16 the sweep was
corrected to build and label its candidates as `build_map` does
(`benchmarks/structure.md`, "Scoring correction (2026-10-16)"). Keep
this report as the provenance of the defaults' choice; its ARI values and
region counts are the pre-correction ones.

# Structure sweep — 2026-10-08

14 notes, scored against the reference with adjusted Rand index (ARI; 1 is the reference itself).

## Similarity
| provider | mean intra-region | mean inter-region |
|---|---|---|
| bge | 0.707 | 0.636 |
| tfidf | 0.087 | 0.047 |

## Sweep
| provider | k | mutual | weighted | resolution | regions | ARI |
|---|---|---|---|---|---|---|
| **bge** | 5 | yes | no | 1 | 7 | 0.675 |
| bge | 5 | yes | yes | 1 | 7 | 0.675 |
| bge | 5 | yes | no | 1.5 | 8 | 0.588 |
| bge | 5 | yes | yes | 1.5 | 8 | 0.588 |
| bge | 5 | yes | no | 2 | 8 | 0.588 |
| bge | 5 | yes | yes | 2 | 8 | 0.588 |
| bge | 2 | no | no | 1.5 | 5 | 0.435 |
| bge | 4 | yes | no | 1 | 7 | 0.435 |
| bge | 4 | yes | yes | 1 | 7 | 0.435 |
| bge | 3 | yes | no | 1 | 8 | 0.412 |
| bge | 3 | yes | yes | 1 | 8 | 0.412 |
| bge | 3 | yes | no | 1.5 | 8 | 0.412 |
| bge | 3 | yes | yes | 1.5 | 8 | 0.412 |
| tfidf | 5 | yes | no | 1 | 5 | 0.398 |
| tfidf | 5 | yes | yes | 1 | 5 | 0.398 |
| tfidf | 4 | yes | yes | 1 | 6 | 0.372 |
| tfidf | 4 | yes | yes | 1.5 | 6 | 0.372 |
| tfidf | 5 | yes | yes | 1.5 | 6 | 0.372 |
| tfidf | 4 | yes | no | 1 | 5 | 0.357 |
| tfidf | 4 | yes | yes | 2 | 7 | 0.355 |
| tfidf | 4 | no | yes | 2 | 5 | 0.348 |
| bge | 2 | no | no | 1 | 4 | 0.343 |
| bge | 2 | no | yes | 1 | 4 | 0.343 |
| bge | 2 | no | yes | 1.5 | 4 | 0.343 |
| bge | 2 | no | no | 2 | 6 | 0.329 |
| bge | 2 | no | yes | 2 | 6 | 0.329 |
| bge | 3 | no | yes | 2 | 6 | 0.329 |
| bge | 4 | yes | no | 2 | 8 | 0.305 |
| bge | 4 | yes | yes | 2 | 8 | 0.305 |
| tfidf | 2 | yes | no | 1 | 8 | 0.305 |
| tfidf | 2 | yes | yes | 1 | 8 | 0.305 |
| tfidf | 2 | yes | no | 1.5 | 8 | 0.305 |
| tfidf | 2 | yes | yes | 1.5 | 8 | 0.305 |
| tfidf | 2 | yes | no | 2 | 8 | 0.305 |
| tfidf | 2 | yes | yes | 2 | 8 | 0.305 |
| tfidf | 5 | yes | no | 2 | 8 | 0.305 |
| bge | 4 | yes | no | 1.5 | 7 | 0.305 |
| bge | 4 | yes | yes | 1.5 | 7 | 0.305 |
| tfidf | 3 | no | yes | 1.5 | 4 | 0.304 |
| tfidf | 3 | no | yes | 2 | 4 | 0.304 |
| tfidf | 4 | no | yes | 1.5 | 4 | 0.304 |
| tfidf | 4 | yes | no | 1.5 | 6 | 0.282 |
| tfidf | 5 | yes | no | 1.5 | 7 | 0.279 |
| bge | 4 | no | no | 1 | 3 | 0.271 |
| tfidf | 5 | no | yes | 1.5 | 5 | 0.261 |
| bge | 4 | no | yes | 1 | 3 | 0.257 |
| tfidf | 3 | yes | yes | 1 | 7 | 0.255 |
| tfidf | 3 | yes | yes | 1.5 | 7 | 0.255 |
| tfidf | 3 | yes | yes | 2 | 7 | 0.255 |
| bge | 3 | yes | no | 2 | 9 | 0.248 |
| bge | 3 | yes | yes | 2 | 9 | 0.248 |
| bge | 4 | no | yes | 1.5 | 5 | 0.241 |
| tfidf | 2 | no | yes | 2 | 5 | 0.241 |
| tfidf | 2 | no | yes | 1 | 4 | 0.188 |
| tfidf | 2 | no | yes | 1.5 | 4 | 0.188 |
| tfidf | 3 | no | yes | 1 | 4 | 0.188 |
| bge | 5 | no | yes | 1 | 3 | 0.182 |
| bge | 2 | yes | no | 2 | 10 | 0.180 |
| bge | 4 | no | no | 2 | 7 | 0.176 |
| bge | 4 | no | yes | 2 | 7 | 0.176 |
| bge | 5 | no | yes | 2 | 8 | 0.176 |
| tfidf | 4 | no | yes | 1 | 3 | 0.158 |
| tfidf | 4 | yes | no | 2 | 7 | 0.156 |
| tfidf | 3 | no | no | 1 | 2 | 0.140 |
| tfidf | 3 | yes | no | 1 | 7 | 0.137 |
| tfidf | 3 | yes | no | 1.5 | 7 | 0.137 |
| bge | 2 | yes | no | 1 | 9 | 0.132 |
| bge | 2 | yes | yes | 1 | 9 | 0.132 |
| bge | 2 | yes | no | 1.5 | 9 | 0.132 |
| bge | 2 | yes | yes | 1.5 | 9 | 0.132 |
| bge | 2 | yes | yes | 2 | 9 | 0.132 |
| bge | 5 | no | no | 2 | 9 | 0.132 |
| tfidf | 5 | no | yes | 2 | 6 | 0.119 |
| tfidf | 3 | yes | no | 2 | 8 | 0.111 |
| tfidf | 4 | no | no | 1 | 3 | 0.100 |
| tfidf | 3 | no | no | 1.5 | 5 | 0.087 |
| tfidf | 2 | no | no | 1 | 3 | 0.081 |
| tfidf | 2 | no | no | 1.5 | 3 | 0.081 |
| tfidf | 4 | no | no | 2 | 7 | 0.074 |
| bge | 5 | no | yes | 1.5 | 5 | 0.072 |
| tfidf | 5 | no | yes | 1 | 3 | 0.071 |
| bge | 5 | no | no | 1 | 3 | 0.061 |
| tfidf | 3 | no | no | 2 | 6 | 0.057 |
| tfidf | 5 | yes | yes | 2 | 7 | 0.057 |
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
_Decided: bge, k=5, mutual=yes, weighted=no, resolution=1, ARI 0.675._

### bge at its own best
- r0: airlock-checks.md
- r1: book-recommendations.md
- r2: cellar-temperature-notes.md, kimchi-microbiology.md, lacto-fermentation-101.md, sourdough-starter-rhythm.md
- r3: cucumber-pickling-log.md, quick-pickles-vinegar-ratio.md, salt-brine-basics.md
- r4: jar-inventory.md
- r5: neighbour-garden-trade.md
- r6: osmosis-and-salt.md, ph-and-spoilage.md, vinegar-chemistry.md

### tfidf at its own best
- r0: airlock-checks.md, cellar-temperature-notes.md, jar-inventory.md
- r1: book-recommendations.md
- r2: cucumber-pickling-log.md, kimchi-microbiology.md, osmosis-and-salt.md, quick-pickles-vinegar-ratio.md, salt-brine-basics.md
- r3: lacto-fermentation-101.md, ph-and-spoilage.md, sourdough-starter-rhythm.md, vinegar-chemistry.md
- r4: neighbour-garden-trade.md

## Reading (2026-10-08)

Mutual filtering rescues the rule. Plain kNN at k=5 — the default before
this run — scored ARI 0.061, indistinguishable from chance. The same
neighbourhood size with only reciprocal edges kept scores 0.675. One-way
edges were the problem, not the neighbourhood size: a popular note pulls
its would-be neighbours in with it, and louvain merged the result. This
decision is baked into `build_map`'s defaults (`mutual = true`); the
sweep is what revisits it.

bge beats tfidf but not cleanly. Both providers peak on mutual-filtered
graphs at 0.675 vs 0.398. bge separates brine, chemistry and both
strays exactly but shreds equipment-and-storage — cellar-temperature's
top neighbours are biology notes, so the equipment region splits into
singletons. tfidf finds the equipment region perfectly and mangles the
rest. The embedder's weakness is localised, and scoring it is exactly
what structure match exists for.
