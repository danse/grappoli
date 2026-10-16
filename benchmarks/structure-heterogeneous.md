# Structure sweep — 2026-10-16

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
| bge | 2 | no | no | 1 | 4 | 0.774 |
| bge | 2 | no | yes | 1 | 4 | 0.774 |
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
| bge | 4 | yes | no | 1 | 3 | 0.545 |
| bge | 3 | no | no | 1 | 3 | 0.504 |
| bge | 3 | no | yes | 1 | 3 | 0.504 |
| bge | 4 | no | no | 1 | 3 | 0.504 |
| bge | 4 | no | yes | 1 | 3 | 0.504 |
| bge | 4 | no | no | 1.5 | 3 | 0.504 |
| bge | 4 | no | yes | 1.5 | 3 | 0.504 |
| bge | 5 | yes | yes | 1 | 3 | 0.504 |
| bge | 5 | no | yes | 1.5 | 4 | 0.478 |
| tfidf | 2 | yes | no | 1 | 4 | 0.435 |
| tfidf | 2 | yes | yes | 1 | 4 | 0.435 |
| tfidf | 2 | yes | no | 1.5 | 4 | 0.435 |
| tfidf | 2 | yes | yes | 1.5 | 4 | 0.435 |
| tfidf | 2 | yes | no | 2 | 4 | 0.435 |
| tfidf | 2 | yes | yes | 2 | 4 | 0.435 |
| bge | 5 | yes | no | 1.5 | 4 | 0.420 |
| bge | 5 | yes | no | 2 | 4 | 0.420 |
| tfidf | 5 | yes | yes | 1 | 3 | 0.398 |
| bge | 5 | no | no | 2 | 5 | 0.386 |
| bge | 5 | yes | no | 1 | 3 | 0.381 |
| tfidf | 2 | no | yes | 1 | 4 | 0.377 |
| tfidf | 3 | no | yes | 1 | 4 | 0.377 |
| tfidf | 3 | yes | no | 1 | 4 | 0.377 |
| tfidf | 3 | yes | yes | 1 | 4 | 0.377 |
| tfidf | 4 | yes | yes | 1 | 4 | 0.377 |
| bge | 5 | no | yes | 1 | 3 | 0.364 |
| tfidf | 2 | no | yes | 2 | 6 | 0.355 |
| tfidf | 4 | no | yes | 2 | 6 | 0.355 |
| tfidf | 3 | no | yes | 2 | 5 | 0.348 |
| tfidf | 3 | yes | yes | 1.5 | 5 | 0.348 |
| tfidf | 3 | yes | yes | 2 | 5 | 0.348 |
| tfidf | 5 | yes | no | 2 | 7 | 0.305 |
| bge | 5 | no | no | 1 | 3 | 0.271 |
| tfidf | 3 | no | yes | 1.5 | 4 | 0.265 |
| tfidf | 4 | no | yes | 1.5 | 4 | 0.265 |
| tfidf | 4 | yes | yes | 1.5 | 4 | 0.265 |
| tfidf | 4 | yes | yes | 2 | 4 | 0.265 |
| tfidf | 5 | no | yes | 1.5 | 4 | 0.265 |
| tfidf | 5 | yes | yes | 1.5 | 4 | 0.265 |
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
| tfidf | 4 | yes | no | 1 | 5 | 0.192 |
| tfidf | 4 | yes | no | 1.5 | 5 | 0.192 |
| tfidf | 3 | no | no | 1 | 4 | 0.157 |
| tfidf | 5 | no | yes | 1 | 3 | 0.145 |
| tfidf | 4 | yes | no | 2 | 6 | 0.137 |
| tfidf | 5 | yes | no | 1.5 | 5 | 0.087 |
| tfidf | 4 | no | no | 1 | 3 | 0.018 |
| tfidf | 5 | yes | no | 1 | 4 | 0.010 |
| tfidf | 5 | no | no | 2 | 7 | -0.043 |
| tfidf | 4 | no | no | 1.5 | 4 | -0.044 |
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
- r0: bike-chain-care.md, commuting-tyre-notes.md, hiking-gear-layering.md
- r1: commit-message-guide.md, pre-commit-hook-checklist.md
- r2: houseplant-pests.md, propagating-by-cuttings.md, watering-houseplants.md
- r3: route-planning-and-weather.md, south-ridge-trail-log.md
- standalone: brake-pad-replacement.md, community-garden-rota.md, library-shelving-notes.md, rebasing-git-history.md

## Reading (2026-10-16)

The rule does not transfer, which is exactly what this second corpus
exists to find out. bge reaches the reference exactly (ARI 1.000, five
regions: the four intended, plus both strays together) but from the
opposite corner of the knob space: k=2, a plain graph with no
reciprocal filter, resolution 1.5–2. The in-domain decision — k=5,
mutual, resolution 1 — scores 0.381 here, merged to 3 regions: at
resolution 1 the wider mutual-filtered neighbourhood's edges glue the
four clusters together. The perfect partition is otherwise easy to
reach (eight bge rows and two knob corners land on it), so the failure
of the in-domain defaults is the rule's shape-dependence, not bge.

No single setting serves both shapes well: the saturated corpus needs
a mutual-filtered neighbourhood (its best: bge k=5 mutual res 1,
0.652), the separable one wants a small plain neighbourhood at higher
resolution (bge k=2 plain res 1.5, 1.000). Neither fixture's winner is
the transferable rule, so `map.py` carries the best worst-case row
across both reports — k=5, mutual, weighted, resolution 2.0 (0.578 /
0.729) — rebakeable when a scored corpus more representative than the
fixtures appears. Which shape the real corpus has is the tool owner's
call, and that corpus's sweep is what will settle it.

bge beats tfidf by more on this shape than on the saturated one
(1.000 vs 0.435) even though TF-IDF's mean margin is comparable (0.03
vs 0.04). Disjoint domains clean up the *ranking* of neighbours far
more than they move mean similarity, and bag-of-words still
fragments: bikes, git and hiking each split, with one hiking note
glued to the bike pair; only houseplants — where the vocabulary is
exactly the object names — comes out whole. Both strays stay clear of
the four intended regions under both providers — grouped as one small
region by bge, left standalone by tfidf.

**Reproduced (2026-10-13).** The batch reran the sweep and returned the
same best row — bge k=2 plain at 1.000, tfidf 0.519 at its own best (the
pre-correction scoring; corrected, 0.435) — so the second shape is
unchanged by a fresh run, and the reading above is what the region-rule
and embedder rows in `architecture.md` are closed on
(`benchmarks/runs/2026-10-13/run.json`).

## Coarser resolution (2026-10-15)

Extending the sweep below resolution 1.0 costs this shape: 1.000 at
1.5–2 becomes 0.774 at 0.5–1.0. Coarser does not survive the separable
corpus any better than it helps the saturated one
(`benchmarks/history/2026-10-15/structure-heterogeneous.md`).
