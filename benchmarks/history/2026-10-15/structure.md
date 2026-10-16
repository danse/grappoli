# Structure — experiment, 2026-10-15

The sweep extended below resolution 1.0, to test whether the in-domain
over-fragmentation (eight regions against a reference of four) is the
rule's granularity. This is not the current record — that is
`benchmarks/structure.md`; the space here is a superset of the record's.

The command, run once per corpus:

```
uv run python scripts/benchmark_structure.py <notes> --reference <ref> \
    --resolutions 0.5,0.7,1.0,1.5,2.0
```

Result: no row below resolution 1.0 improves either shape. In-domain the
best stays 0.675 (bge k=5 mutual resolution 1, seven regions); res 0.7
merges to six regions and *drops* to 0.429. Heterogeneous keeps 1.000 at
resolution 1.5-2 and falls to 0.774 (four regions) at 0.5-0.7. The best
worst-case setting across both shapes is therefore unchanged: bge, k=5,
mutual, weighted, resolution 2.0 — 0.588 / 0.729 — which is what
`build_map` already carries.

# Structure sweep — 2026-10-15

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
| bge | 3 | yes | no | 0.7 | 7 | 0.435 |
| bge | 4 | yes | no | 1 | 7 | 0.435 |
| bge | 4 | yes | yes | 1 | 7 | 0.435 |
| bge | 5 | yes | no | 0.7 | 6 | 0.429 |
| bge | 5 | yes | yes | 0.7 | 6 | 0.429 |
| bge | 3 | yes | no | 1 | 8 | 0.412 |
| bge | 3 | yes | yes | 1 | 8 | 0.412 |
| bge | 3 | yes | no | 1.5 | 8 | 0.412 |
| bge | 3 | yes | yes | 1.5 | 8 | 0.412 |
| tfidf | 5 | yes | yes | 0.7 | 5 | 0.398 |
| tfidf | 5 | yes | no | 1 | 5 | 0.398 |
| tfidf | 5 | yes | yes | 1 | 5 | 0.398 |
| tfidf | 4 | yes | yes | 1 | 6 | 0.372 |
| tfidf | 4 | yes | yes | 1.5 | 6 | 0.372 |
| tfidf | 5 | yes | yes | 1.5 | 6 | 0.372 |
| tfidf | 4 | yes | no | 0.7 | 5 | 0.357 |
| tfidf | 4 | yes | yes | 0.7 | 5 | 0.357 |
| tfidf | 4 | yes | no | 1 | 5 | 0.357 |
| tfidf | 4 | yes | yes | 2 | 7 | 0.355 |
| tfidf | 2 | yes | yes | 0.5 | 7 | 0.348 |
| tfidf | 2 | yes | yes | 0.7 | 7 | 0.348 |
| tfidf | 4 | no | yes | 2 | 5 | 0.348 |
| bge | 2 | no | no | 1 | 4 | 0.343 |
| bge | 2 | no | yes | 1 | 4 | 0.343 |
| bge | 2 | no | yes | 1.5 | 4 | 0.343 |
| bge | 2 | no | no | 2 | 6 | 0.329 |
| bge | 2 | no | yes | 2 | 6 | 0.329 |
| bge | 3 | no | yes | 2 | 6 | 0.329 |
| tfidf | 4 | yes | no | 0.5 | 4 | 0.315 |
| tfidf | 4 | yes | yes | 0.5 | 4 | 0.315 |
| tfidf | 5 | yes | no | 0.5 | 4 | 0.315 |
| tfidf | 5 | yes | no | 0.7 | 4 | 0.315 |
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
| bge | 4 | yes | no | 0.5 | 6 | 0.304 |
| bge | 4 | yes | yes | 0.5 | 6 | 0.304 |
| bge | 4 | yes | no | 0.7 | 6 | 0.304 |
| bge | 4 | yes | yes | 0.7 | 6 | 0.304 |
| tfidf | 3 | no | yes | 1.5 | 4 | 0.304 |
| tfidf | 3 | no | yes | 2 | 4 | 0.304 |
| tfidf | 4 | no | yes | 1.5 | 4 | 0.304 |
| tfidf | 4 | yes | no | 1.5 | 6 | 0.282 |
| tfidf | 4 | no | yes | 0.7 | 2 | 0.280 |
| tfidf | 5 | yes | no | 1.5 | 7 | 0.279 |
| bge | 2 | no | no | 0.7 | 3 | 0.274 |
| bge | 2 | no | yes | 0.7 | 3 | 0.274 |
| bge | 4 | no | no | 1 | 3 | 0.271 |
| bge | 3 | yes | yes | 0.7 | 7 | 0.261 |
| tfidf | 5 | no | yes | 1.5 | 5 | 0.261 |
| bge | 4 | no | yes | 1 | 3 | 0.257 |
| tfidf | 3 | yes | yes | 1 | 7 | 0.255 |
| tfidf | 3 | yes | yes | 1.5 | 7 | 0.255 |
| tfidf | 3 | yes | yes | 2 | 7 | 0.255 |
| bge | 3 | yes | no | 2 | 9 | 0.248 |
| bge | 3 | yes | yes | 2 | 9 | 0.248 |
| bge | 4 | no | yes | 1.5 | 5 | 0.241 |
| tfidf | 2 | no | yes | 2 | 5 | 0.241 |
| bge | 2 | yes | no | 0.5 | 8 | 0.212 |
| bge | 2 | yes | yes | 0.5 | 8 | 0.212 |
| bge | 2 | yes | no | 0.7 | 8 | 0.212 |
| bge | 2 | yes | yes | 0.7 | 8 | 0.212 |
| tfidf | 2 | no | yes | 1 | 4 | 0.188 |
| tfidf | 2 | no | yes | 1.5 | 4 | 0.188 |
| tfidf | 3 | no | yes | 1 | 4 | 0.188 |
| bge | 5 | no | yes | 1 | 3 | 0.182 |
| bge | 2 | yes | no | 2 | 10 | 0.180 |
| bge | 4 | no | no | 2 | 7 | 0.176 |
| bge | 4 | no | yes | 2 | 7 | 0.176 |
| bge | 5 | no | yes | 2 | 8 | 0.176 |
| tfidf | 4 | no | no | 0.7 | 2 | 0.176 |
| tfidf | 2 | yes | no | 0.5 | 7 | 0.174 |
| tfidf | 2 | yes | no | 0.7 | 7 | 0.174 |
| bge | 3 | yes | no | 0.5 | 6 | 0.169 |
| bge | 3 | yes | yes | 0.5 | 6 | 0.169 |
| tfidf | 3 | no | yes | 0.7 | 3 | 0.158 |
| tfidf | 4 | no | yes | 1 | 3 | 0.158 |
| tfidf | 3 | yes | no | 0.5 | 5 | 0.157 |
| tfidf | 3 | yes | no | 0.7 | 5 | 0.157 |
| tfidf | 4 | yes | no | 2 | 7 | 0.156 |
| tfidf | 5 | no | yes | 0.7 | 2 | 0.150 |
| tfidf | 3 | yes | yes | 0.5 | 6 | 0.140 |
| tfidf | 3 | yes | yes | 0.7 | 6 | 0.140 |
| tfidf | 3 | no | no | 0.7 | 2 | 0.140 |
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
| bge | 5 | yes | no | 0.5 | 5 | 0.114 |
| bge | 5 | yes | yes | 0.5 | 5 | 0.114 |
| tfidf | 3 | yes | no | 2 | 8 | 0.111 |
| tfidf | 4 | no | no | 1 | 3 | 0.100 |
| tfidf | 3 | no | no | 1.5 | 5 | 0.087 |
| tfidf | 5 | yes | yes | 0.5 | 3 | 0.086 |
| tfidf | 2 | no | yes | 0.5 | 3 | 0.081 |
| tfidf | 2 | no | no | 1 | 3 | 0.081 |
| tfidf | 2 | no | no | 1.5 | 3 | 0.081 |
| tfidf | 4 | no | no | 2 | 7 | 0.074 |
| bge | 5 | no | yes | 1.5 | 5 | 0.072 |
| tfidf | 2 | no | yes | 0.7 | 3 | 0.071 |
| tfidf | 5 | no | yes | 1 | 3 | 0.071 |
| bge | 5 | no | no | 1 | 3 | 0.061 |
| tfidf | 3 | no | no | 2 | 6 | 0.057 |
| tfidf | 5 | yes | yes | 2 | 7 | 0.057 |
| bge | 3 | no | no | 2 | 6 | 0.041 |
| tfidf | 2 | no | no | 2 | 6 | 0.041 |
| bge | 3 | no | no | 0.7 | 2 | 0.039 |
| bge | 3 | no | yes | 0.7 | 2 | 0.039 |
| bge | 3 | no | no | 1 | 2 | 0.039 |
| bge | 3 | no | yes | 1 | 2 | 0.039 |
| tfidf | 4 | no | no | 1.5 | 4 | 0.033 |
| bge | 5 | no | no | 1.5 | 4 | 0.022 |
| tfidf | 2 | no | no | 0.5 | 2 | 0.019 |
| tfidf | 2 | no | no | 0.7 | 2 | 0.019 |
| bge | 2 | no | no | 0.5 | 1 | 0.000 |
| bge | 2 | no | yes | 0.5 | 1 | 0.000 |
| bge | 3 | no | no | 0.5 | 1 | 0.000 |
| bge | 3 | no | yes | 0.5 | 1 | 0.000 |
| bge | 4 | no | no | 0.5 | 1 | 0.000 |
| bge | 4 | no | yes | 0.5 | 1 | 0.000 |
| bge | 4 | no | no | 0.7 | 1 | 0.000 |
| bge | 4 | no | yes | 0.7 | 1 | 0.000 |
| bge | 5 | no | no | 0.5 | 1 | 0.000 |
| bge | 5 | no | yes | 0.5 | 1 | 0.000 |
| bge | 5 | no | no | 0.7 | 1 | 0.000 |
| bge | 5 | no | yes | 0.7 | 1 | 0.000 |
| tfidf | 3 | no | no | 0.5 | 1 | 0.000 |
| tfidf | 3 | no | yes | 0.5 | 1 | 0.000 |
| tfidf | 4 | no | no | 0.5 | 1 | 0.000 |
| tfidf | 4 | no | yes | 0.5 | 1 | 0.000 |
| tfidf | 5 | no | no | 0.5 | 1 | 0.000 |
| tfidf | 5 | no | yes | 0.5 | 1 | 0.000 |
| tfidf | 5 | no | no | 0.7 | 1 | 0.000 |
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
