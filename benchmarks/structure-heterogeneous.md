# Structure sweep — 2026-10-16

14 notes, scored against the reference with adjusted Rand index (ARI; 1 is the reference itself).

## Similarity
| provider | mean intra-region | mean inter-region |
|---|---|---|
| e5 | 0.858 | 0.812 |
| tfidf | 0.050 | 0.012 |

## Sweep
| provider | k | mutual | weighted | resolution | regions | ARI |
|---|---|---|---|---|---|---|
| **e5** | 2 | no | no | 2 | 5 | 1.000 |
| e5 | 2 | no | yes | 2 | 5 | 1.000 |
| e5 | 2 | no | no | 1.5 | 5 | 0.783 |
| e5 | 2 | no | yes | 1.5 | 5 | 0.783 |
| e5 | 3 | yes | no | 1.5 | 5 | 0.783 |
| e5 | 3 | yes | yes | 1.5 | 5 | 0.783 |
| e5 | 3 | yes | no | 2 | 5 | 0.783 |
| e5 | 3 | yes | yes | 2 | 5 | 0.783 |
| e5 | 4 | yes | no | 2 | 5 | 0.783 |
| e5 | 4 | yes | yes | 2 | 5 | 0.783 |
| e5 | 2 | yes | no | 1.5 | 5 | 0.712 |
| e5 | 2 | yes | yes | 1.5 | 5 | 0.712 |
| e5 | 2 | yes | no | 2 | 5 | 0.712 |
| e5 | 2 | yes | yes | 2 | 5 | 0.712 |
| e5 | 4 | yes | no | 1.5 | 4 | 0.687 |
| e5 | 4 | yes | yes | 1.5 | 4 | 0.687 |
| e5 | 2 | yes | no | 1 | 4 | 0.682 |
| e5 | 2 | yes | yes | 1 | 4 | 0.682 |
| e5 | 4 | no | no | 2 | 5 | 0.641 |
| e5 | 4 | no | yes | 2 | 5 | 0.641 |
| e5 | 4 | no | yes | 1.5 | 4 | 0.624 |
| e5 | 5 | no | no | 1.5 | 4 | 0.548 |
| e5 | 2 | no | no | 1 | 3 | 0.545 |
| e5 | 2 | no | yes | 1 | 3 | 0.545 |
| e5 | 3 | yes | no | 1 | 3 | 0.545 |
| e5 | 3 | yes | yes | 1 | 3 | 0.545 |
| e5 | 4 | yes | no | 1 | 3 | 0.545 |
| e5 | 4 | yes | yes | 1 | 3 | 0.545 |
| e5 | 3 | no | no | 1 | 3 | 0.504 |
| e5 | 3 | no | yes | 1 | 3 | 0.504 |
| e5 | 3 | no | no | 1.5 | 3 | 0.504 |
| e5 | 3 | no | yes | 1.5 | 3 | 0.504 |
| e5 | 4 | no | yes | 1 | 3 | 0.504 |
| e5 | 3 | no | no | 2 | 5 | 0.494 |
| e5 | 3 | no | yes | 2 | 5 | 0.494 |
| tfidf | 2 | yes | yes | 1 | 4 | 0.494 |
| tfidf | 2 | yes | yes | 1.5 | 4 | 0.494 |
| e5 | 5 | yes | no | 2 | 4 | 0.473 |
| e5 | 5 | yes | yes | 2 | 4 | 0.473 |
| e5 | 5 | no | yes | 1.5 | 5 | 0.468 |
| e5 | 5 | yes | yes | 1 | 3 | 0.442 |
| e5 | 5 | yes | no | 1.5 | 3 | 0.442 |
| e5 | 5 | yes | yes | 1.5 | 3 | 0.442 |
| tfidf | 5 | no | yes | 1.5 | 5 | 0.420 |
| tfidf | 3 | no | yes | 1 | 4 | 0.398 |
| e5 | 5 | no | yes | 2 | 6 | 0.397 |
| tfidf | 4 | no | yes | 1.5 | 6 | 0.397 |
| tfidf | 3 | no | yes | 1.5 | 4 | 0.377 |
| e5 | 5 | yes | no | 1 | 3 | 0.335 |
| tfidf | 2 | yes | no | 2 | 5 | 0.329 |
| tfidf | 3 | yes | no | 1.5 | 5 | 0.329 |
| tfidf | 3 | yes | no | 2 | 5 | 0.329 |
| tfidf | 4 | yes | no | 2 | 5 | 0.329 |
| tfidf | 2 | yes | no | 1 | 4 | 0.325 |
| tfidf | 2 | yes | no | 1.5 | 4 | 0.325 |
| tfidf | 2 | yes | yes | 2 | 4 | 0.325 |
| tfidf | 3 | yes | no | 1 | 4 | 0.325 |
| tfidf | 3 | yes | yes | 1.5 | 4 | 0.325 |
| tfidf | 3 | yes | yes | 2 | 4 | 0.325 |
| tfidf | 4 | yes | yes | 1.5 | 4 | 0.325 |
| tfidf | 4 | yes | yes | 2 | 4 | 0.325 |
| tfidf | 5 | yes | yes | 1.5 | 4 | 0.325 |
| e5 | 4 | no | no | 1.5 | 4 | 0.323 |
| tfidf | 5 | yes | yes | 1 | 3 | 0.320 |
| tfidf | 3 | yes | yes | 1 | 3 | 0.303 |
| tfidf | 4 | yes | yes | 1 | 3 | 0.303 |
| tfidf | 4 | no | yes | 1 | 3 | 0.303 |
| tfidf | 5 | no | yes | 1 | 3 | 0.303 |
| tfidf | 2 | no | no | 1 | 5 | 0.282 |
| tfidf | 2 | no | no | 1.5 | 5 | 0.282 |
| tfidf | 2 | no | no | 2 | 5 | 0.282 |
| tfidf | 5 | yes | no | 2 | 6 | 0.279 |
| e5 | 5 | no | no | 1 | 2 | 0.279 |
| tfidf | 2 | no | yes | 1.5 | 4 | 0.265 |
| tfidf | 2 | no | yes | 2 | 4 | 0.265 |
| e5 | 4 | no | no | 1 | 3 | 0.257 |
| e5 | 5 | no | no | 2 | 7 | 0.255 |
| tfidf | 3 | no | yes | 2 | 6 | 0.255 |
| tfidf | 5 | no | yes | 2 | 6 | 0.255 |
| tfidf | 2 | no | yes | 1 | 3 | 0.242 |
| tfidf | 4 | yes | no | 1 | 4 | 0.241 |
| tfidf | 4 | yes | no | 1.5 | 4 | 0.241 |
| tfidf | 5 | yes | no | 1.5 | 4 | 0.241 |
| tfidf | 5 | yes | yes | 2 | 5 | 0.233 |
| e5 | 5 | no | yes | 1 | 2 | 0.176 |
| tfidf | 4 | no | yes | 2 | 5 | 0.174 |
| tfidf | 5 | yes | no | 1 | 3 | 0.104 |
| tfidf | 3 | no | no | 2 | 5 | 0.087 |
| tfidf | 3 | no | no | 1 | 3 | 0.081 |
| tfidf | 4 | no | no | 1.5 | 5 | 0.072 |
| tfidf | 5 | no | no | 1.5 | 6 | 0.000 |
| tfidf | 5 | no | no | 2 | 7 | -0.043 |
| tfidf | 4 | no | no | 1 | 3 | -0.053 |
| tfidf | 3 | no | no | 1.5 | 6 | -0.055 |
| tfidf | 4 | no | no | 2 | 7 | -0.055 |
| tfidf | 5 | no | no | 1 | 2 | -0.098 |

## Best map (by ARI)
_Decided: e5, k=2, mutual=no, weighted=no, resolution=2, ARI 1.000._

### e5 at its own best
- r0: bike-chain-care.md, brake-pad-replacement.md, commuting-tyre-notes.md
- r1: commit-message-guide.md, pre-commit-hook-checklist.md, rebasing-git-history.md
- r2: community-garden-rota.md, library-shelving-notes.md
- r3: hiking-gear-layering.md, route-planning-and-weather.md, south-ridge-trail-log.md
- r4: houseplant-pests.md, propagating-by-cuttings.md, watering-houseplants.md

### tfidf at its own best
- r0: bike-chain-care.md, community-garden-rota.md, commuting-tyre-notes.md
- r1: brake-pad-replacement.md, commit-message-guide.md, pre-commit-hook-checklist.md
- r2: hiking-gear-layering.md, rebasing-git-history.md, route-planning-and-weather.md, south-ridge-trail-log.md
- r3: houseplant-pests.md, propagating-by-cuttings.md, watering-houseplants.md
- standalone: library-shelving-notes.md

## Reading (2026-10-16)

The rule still does not transfer, though the multilingual encoder makes
both corners easier. e5 reaches the reference exactly (ARI 1.000, five
regions: the four intended plus both strays together) with a small plain
neighbourhood, k=2 at resolution 2 — the same shape the English sweep
found, so the shape-dependence is the rule's, not the encoder's. The
in-domain decision — k=4, mutual, resolution 2 — scores 0.783 here,
against 0.473 at k=5: shrinking the neighbourhood is what carries the
rule across both shapes, and is why k=4 is the best worst-case row.

e5 beats tfidf by more on this shape than on the saturated one (1.000
against 0.494) even though its mean margin is comparable (0.046 vs
0.034). Disjoint domains clean up the *ranking* of neighbours far more
than they move mean similarity, and bag-of-words still fragments. Both
strays stay clear of the four intended regions under both providers —
grouped as one small region by e5, left standalone by tfidf.

## Coarser resolution (2026-10-15)

Extending the sweep below resolution 1.0 costs this shape: on the English
sweep 1.000 at 1.5–2 became 0.774 at 0.5–1.0. Coarser does not survive
the separable corpus any better than it helps the saturated one
(`benchmarks/history/2026-10-15/structure-heterogeneous.md`).
