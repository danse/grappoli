# Structure (heterogeneous) — experiment, 2026-10-15

The sweep extended below resolution 1.0. This is not the current
record — that is `benchmarks/structure-heterogeneous.md`. See
`benchmarks/history/2026-10-15/structure.md` for the experiment's
reading: coarser resolutions do not help, and the best worst-case
setting is unchanged.

# Structure sweep — 2026-10-15

14 notes, scored against the reference with adjusted Rand index (ARI; 1 is the reference itself).

## Similarity
| provider | mean intra-region | mean inter-region |
|---|---|---|
| bge | 0.687 | 0.555 |
| tfidf | 0.046 | 0.015 |

## Sweep
| provider | k | mutual | weighted | resolution | regions | ARI |
|---|---|---|---|---|---|---|
| **bge** | 2 | no | no | 1.5 | 5 | 1.000 |
| bge | 2 | no | yes | 1.5 | 5 | 1.000 |
| bge | 2 | no | no | 2 | 5 | 1.000 |
| bge | 2 | no | yes | 2 | 5 | 1.000 |
| bge | 3 | yes | no | 1.5 | 5 | 1.000 |
| bge | 3 | yes | yes | 1.5 | 5 | 1.000 |
| bge | 3 | yes | no | 2 | 5 | 1.000 |
| bge | 3 | yes | yes | 2 | 5 | 1.000 |
| bge | 2 | yes | no | 2 | 5 | 0.821 |
| bge | 2 | yes | yes | 2 | 5 | 0.821 |
| bge | 2 | no | no | 0.7 | 4 | 0.774 |
| bge | 2 | no | yes | 0.7 | 4 | 0.774 |
| bge | 2 | no | no | 1 | 4 | 0.774 |
| bge | 2 | no | yes | 1 | 4 | 0.774 |
| bge | 2 | yes | no | 0.5 | 4 | 0.774 |
| bge | 2 | yes | yes | 0.5 | 4 | 0.774 |
| bge | 2 | yes | no | 0.7 | 4 | 0.774 |
| bge | 2 | yes | yes | 0.7 | 4 | 0.774 |
| bge | 2 | yes | no | 1 | 4 | 0.774 |
| bge | 2 | yes | yes | 1 | 4 | 0.774 |
| bge | 2 | yes | no | 1.5 | 4 | 0.774 |
| bge | 2 | yes | yes | 1.5 | 4 | 0.774 |
| bge | 3 | yes | no | 1 | 4 | 0.774 |
| bge | 3 | yes | yes | 1 | 4 | 0.774 |
| bge | 4 | yes | yes | 1 | 4 | 0.774 |
| bge | 4 | yes | no | 1.5 | 4 | 0.774 |
| bge | 4 | yes | yes | 1.5 | 4 | 0.774 |
| bge | 4 | yes | no | 2 | 4 | 0.774 |
| bge | 4 | yes | yes | 2 | 4 | 0.774 |
| bge | 5 | yes | yes | 2 | 4 | 0.729 |
| bge | 4 | no | no | 2 | 6 | 0.641 |
| bge | 4 | no | yes | 2 | 6 | 0.641 |
| bge | 5 | no | yes | 2 | 5 | 0.609 |
| bge | 3 | no | no | 1.5 | 4 | 0.548 |
| bge | 3 | no | yes | 1.5 | 4 | 0.548 |
| bge | 3 | no | no | 2 | 4 | 0.548 |
| bge | 3 | no | yes | 2 | 4 | 0.548 |
| bge | 5 | yes | yes | 1.5 | 4 | 0.548 |
| bge | 2 | no | no | 0.5 | 3 | 0.545 |
| bge | 2 | no | yes | 0.5 | 3 | 0.545 |
| bge | 3 | yes | no | 0.5 | 3 | 0.545 |
| bge | 3 | yes | yes | 0.5 | 3 | 0.545 |
| bge | 3 | yes | no | 0.7 | 3 | 0.545 |
| bge | 3 | yes | yes | 0.7 | 3 | 0.545 |
| bge | 4 | yes | no | 0.5 | 3 | 0.545 |
| bge | 4 | yes | yes | 0.5 | 3 | 0.545 |
| bge | 4 | yes | no | 0.7 | 3 | 0.545 |
| bge | 4 | yes | yes | 0.7 | 3 | 0.545 |
| bge | 4 | yes | no | 1 | 3 | 0.545 |
| bge | 5 | yes | yes | 0.7 | 3 | 0.545 |
| tfidf | 2 | yes | no | 0.5 | 7 | 0.522 |
| tfidf | 2 | yes | yes | 0.5 | 7 | 0.522 |
| tfidf | 2 | yes | no | 0.7 | 7 | 0.522 |
| tfidf | 2 | yes | yes | 0.7 | 7 | 0.522 |
| tfidf | 2 | yes | no | 1 | 8 | 0.519 |
| tfidf | 2 | yes | yes | 1 | 8 | 0.519 |
| tfidf | 2 | yes | no | 1.5 | 8 | 0.519 |
| tfidf | 2 | yes | yes | 1.5 | 8 | 0.519 |
| tfidf | 2 | yes | no | 2 | 8 | 0.519 |
| tfidf | 2 | yes | yes | 2 | 8 | 0.519 |
| bge | 3 | no | no | 0.5 | 3 | 0.504 |
| bge | 3 | no | yes | 0.5 | 3 | 0.504 |
| bge | 3 | no | no | 0.7 | 3 | 0.504 |
| bge | 3 | no | yes | 0.7 | 3 | 0.504 |
| bge | 3 | no | no | 1 | 3 | 0.504 |
| bge | 3 | no | yes | 1 | 3 | 0.504 |
| bge | 4 | no | no | 1 | 3 | 0.504 |
| bge | 4 | no | yes | 1 | 3 | 0.504 |
| bge | 4 | no | no | 1.5 | 3 | 0.504 |
| bge | 4 | no | yes | 1.5 | 3 | 0.504 |
| bge | 5 | yes | no | 0.7 | 3 | 0.504 |
| bge | 5 | yes | yes | 1 | 3 | 0.504 |
| bge | 5 | no | yes | 1.5 | 4 | 0.478 |
| bge | 5 | yes | no | 1.5 | 4 | 0.420 |
| bge | 5 | yes | no | 2 | 4 | 0.420 |
| tfidf | 5 | yes | yes | 1 | 3 | 0.398 |
| bge | 5 | no | no | 2 | 5 | 0.386 |
| bge | 5 | yes | no | 1 | 3 | 0.381 |
| tfidf | 2 | no | yes | 1 | 4 | 0.377 |
| tfidf | 3 | no | yes | 1 | 4 | 0.377 |
| tfidf | 3 | yes | yes | 0.7 | 4 | 0.377 |
| tfidf | 3 | yes | no | 1 | 4 | 0.377 |
| tfidf | 3 | yes | yes | 1 | 4 | 0.377 |
| tfidf | 4 | yes | yes | 0.7 | 4 | 0.377 |
| tfidf | 4 | yes | yes | 1 | 4 | 0.377 |
| bge | 5 | no | yes | 1 | 3 | 0.364 |
| tfidf | 2 | no | yes | 2 | 6 | 0.355 |
| tfidf | 4 | no | yes | 2 | 6 | 0.355 |
| tfidf | 3 | no | yes | 2 | 5 | 0.348 |
| tfidf | 3 | yes | yes | 1.5 | 5 | 0.348 |
| tfidf | 3 | yes | yes | 2 | 5 | 0.348 |
| bge | 4 | no | no | 0.5 | 2 | 0.314 |
| bge | 4 | no | yes | 0.5 | 2 | 0.314 |
| bge | 4 | no | no | 0.7 | 2 | 0.314 |
| bge | 4 | no | yes | 0.7 | 2 | 0.314 |
| bge | 5 | no | no | 0.7 | 2 | 0.314 |
| bge | 5 | no | yes | 0.7 | 2 | 0.314 |
| bge | 5 | yes | no | 0.5 | 2 | 0.314 |
| tfidf | 5 | yes | no | 2 | 7 | 0.305 |
| bge | 5 | yes | yes | 0.5 | 2 | 0.280 |
| bge | 5 | no | no | 1 | 3 | 0.271 |
| tfidf | 3 | no | yes | 1.5 | 4 | 0.265 |
| tfidf | 4 | no | yes | 1.5 | 4 | 0.265 |
| tfidf | 4 | yes | yes | 1.5 | 4 | 0.265 |
| tfidf | 4 | yes | yes | 2 | 4 | 0.265 |
| tfidf | 5 | no | yes | 1.5 | 4 | 0.265 |
| tfidf | 5 | yes | yes | 1.5 | 4 | 0.265 |
| tfidf | 2 | no | yes | 0.7 | 3 | 0.263 |
| tfidf | 3 | yes | yes | 0.5 | 3 | 0.263 |
| tfidf | 4 | yes | yes | 0.5 | 3 | 0.263 |
| tfidf | 2 | no | no | 1.5 | 5 | 0.261 |
| tfidf | 2 | no | no | 2 | 5 | 0.261 |
| tfidf | 3 | no | no | 1.5 | 5 | 0.261 |
| tfidf | 4 | no | yes | 1 | 3 | 0.257 |
| tfidf | 3 | yes | no | 1.5 | 6 | 0.255 |
| tfidf | 3 | yes | no | 2 | 6 | 0.255 |
| tfidf | 5 | no | yes | 2 | 6 | 0.255 |
| bge | 5 | no | no | 1.5 | 4 | 0.252 |
| tfidf | 2 | no | yes | 1.5 | 4 | 0.247 |
| tfidf | 3 | no | no | 2 | 6 | 0.233 |
| tfidf | 5 | yes | yes | 2 | 6 | 0.233 |
| tfidf | 2 | no | no | 1 | 4 | 0.230 |
| tfidf | 2 | no | yes | 0.5 | 2 | 0.222 |
| tfidf | 4 | yes | no | 1 | 5 | 0.192 |
| tfidf | 4 | yes | no | 1.5 | 5 | 0.192 |
| tfidf | 3 | yes | no | 0.5 | 3 | 0.191 |
| tfidf | 3 | yes | no | 0.7 | 3 | 0.191 |
| tfidf | 5 | yes | yes | 0.5 | 3 | 0.191 |
| tfidf | 5 | yes | yes | 0.7 | 3 | 0.191 |
| tfidf | 3 | no | yes | 0.5 | 2 | 0.191 |
| tfidf | 3 | no | no | 0.7 | 3 | 0.158 |
| tfidf | 3 | no | no | 1 | 4 | 0.157 |
| tfidf | 5 | no | yes | 1 | 3 | 0.145 |
| tfidf | 4 | yes | no | 2 | 6 | 0.137 |
| tfidf | 5 | yes | no | 0.7 | 2 | 0.131 |
| tfidf | 3 | no | yes | 0.7 | 2 | 0.093 |
| tfidf | 4 | no | yes | 0.7 | 2 | 0.093 |
| tfidf | 5 | yes | no | 1.5 | 5 | 0.087 |
| tfidf | 5 | yes | no | 0.5 | 2 | 0.085 |
| tfidf | 2 | no | no | 0.5 | 2 | 0.069 |
| tfidf | 4 | yes | no | 0.7 | 3 | 0.061 |
| tfidf | 5 | no | yes | 0.7 | 2 | 0.019 |
| tfidf | 4 | no | no | 1 | 3 | 0.018 |
| tfidf | 5 | yes | no | 1 | 4 | 0.010 |
| bge | 5 | no | no | 0.5 | 1 | 0.000 |
| bge | 5 | no | yes | 0.5 | 1 | 0.000 |
| tfidf | 3 | no | no | 0.5 | 1 | 0.000 |
| tfidf | 4 | no | no | 0.5 | 1 | 0.000 |
| tfidf | 4 | no | yes | 0.5 | 1 | 0.000 |
| tfidf | 5 | no | no | 0.5 | 1 | 0.000 |
| tfidf | 5 | no | yes | 0.5 | 1 | 0.000 |
| tfidf | 2 | no | no | 0.7 | 2 | -0.007 |
| tfidf | 4 | yes | no | 0.5 | 2 | -0.010 |
| tfidf | 5 | no | no | 0.7 | 2 | -0.025 |
| tfidf | 5 | no | no | 2 | 7 | -0.043 |
| tfidf | 4 | no | no | 1.5 | 4 | -0.044 |
| tfidf | 4 | no | no | 0.7 | 2 | -0.093 |
| tfidf | 5 | no | no | 1 | 2 | -0.093 |
| tfidf | 5 | no | no | 1.5 | 4 | -0.129 |
| tfidf | 4 | no | no | 2 | 7 | -0.132 |

## Best map (by ARI)
_Decided: bge, k=2, mutual=no, weighted=no, resolution=1.5, ARI 1.000._

### bge at its own best
- r0: bike-chain-care.md, brake-pad-replacement.md, commuting-tyre-notes.md
- r1: commit-message-guide.md, pre-commit-hook-checklist.md, rebasing-git-history.md
- r2: community-garden-rota.md, library-shelving-notes.md
- r3: hiking-gear-layering.md, route-planning-and-weather.md, south-ridge-trail-log.md
- r4: houseplant-pests.md, propagating-by-cuttings.md, watering-houseplants.md

### tfidf at its own best
- r0: bike-chain-care.md, commuting-tyre-notes.md, hiking-gear-layering.md, route-planning-and-weather.md, south-ridge-trail-log.md
- r1: brake-pad-replacement.md
- r2: commit-message-guide.md, pre-commit-hook-checklist.md
- r3: community-garden-rota.md
- r4: houseplant-pests.md, propagating-by-cuttings.md, watering-houseplants.md
- r5: library-shelving-notes.md
- r6: rebasing-git-history.md
