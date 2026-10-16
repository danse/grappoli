# Structure — English (bge) sweep, superseded

The sweep with the English encoder (`bge-small-en`), corrected on
2026-10-16 and the reading in force until the encoder became the
multilingual `intfloat/multilingual-e5-small`. It is what chose the
defaults `build_map` carried until then — k=5, mutual, weighted,
resolution 2.0, best worst-case 0.578 in-domain / 0.729 heterogeneous.
The reading now in force is `benchmarks/structure.md`.

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

