"""Assemble the map.

`build_map` runs the whole map pipeline — similarity, graph,
regions, representatives — and returns the map without a single
generation call. The structure of what it returns:

    {
      "similarity": provider,
      "k": neighbourhood size,
      "mutual": reciprocal-edge filter,
      "resolution": louvain resolution,
      "weighted": louvain on edge strengths,
      "regions": [{id, members, representatives}],
      "edges": [{source, target, weight}],   # cross-community, count
      "standalone": [note, ...],             # notes nothing refers to
    }

The rule parameters appear in the map so the artefact says which rule
produced it. The defaults are the best worst-case setting across both
fixture shapes under the multilingual encoder: k=4, mutual, weighted,
resolution 2.0 scores 0.904 in-domain and 0.783 heterogeneous — no
single setting has a better guarantee, and this one is also the
saturated corpus's own winner. `mutual` stays true because it wins the
worst case (its best 0.904/0.783 against plain's 0.348/1.000): it
carries the saturated shape, where plain graphs over-merge, at the cost
of a little on the separable one. The sweep re-decides all of these on
any corpus you can score (`benchmarks/structure.md`,
`benchmarks/structure-heterogeneous.md`).
`progress` is a callback (label, done, total) for the per-item display
that every step must provide (architecture.md, Progress and logging).
"""

import numpy as np

from . import graph as _graph
from .similarity import build_vectors


def build_map(
    notes: dict[str, str],
    provider: str = "e5",
    k: int = 4,
    target: int = 5,
    mutual: bool = True,
    resolution: float = 2.0,
    weighted: bool = True,
    progress=None,
) -> dict:
    names = list(notes)
    texts = [notes[name] for name in names]

    vectors = build_vectors(texts, provider, progress)
    edges = _graph.mutual_edges(vectors, k) if mutual else _graph.knn_edges(vectors, k)
    progress("clusters", 0, 1) if progress else None

    # A note with no edges has no neighbourhood to belong to. It is
    # reported as standing alone rather than forced into a region it
    # was never near. Louvain still hands every node a community, so
    # the edge-less singletons it makes are dropped here — otherwise a
    # note would be listed twice, once as region, once as standalone.
    touched = {a for a, b, _ in edges} | {b for a, b, _ in edges}
    communities = [
        c for c in _graph.partition(edges, len(names), resolution, weighted)
        if c and any(m in touched for m in c)
    ]
    progress("clusters", 1, 1) if progress else None

    regions = []
    index: dict[int, int] = {}
    for region_id, members in enumerate(sorted(communities, key=lambda c: min(c))):
        reps = _graph.representatives(members, vectors, target)
        region = {
            "id": region_id,
            "members": [names[m] for m in sorted(members)],
            "representatives": [names[m] for m in reps],
        }
        regions.append(region)
        for member in members:
            index[member] = region_id

    # Cross-community edges: aggregate the base graph's note-level
    # edges by the two regions they touch. Weight is the count of
    # note-level edges — how much the regions touch, in edges not in
    # words.
    touch: dict[tuple[int, int], int] = {}
    for a, b, _ in edges:
        ra, rb = index.get(a), index.get(b)
        if ra is not None and rb is not None and ra != rb:
            low, high = (ra, rb) if ra < rb else (rb, ra)
            touch[(low, high)] = touch.get((low, high), 0) + 1

    return {
        "similarity": provider,
        "k": k,
        "mutual": mutual,
        "resolution": resolution,
        "weighted": weighted,
        "notes": len(names),
        "regions": regions,
        "edges": [
            {"source": a, "target": b, "weight": w}
            for (a, b), w in sorted(touch.items())
        ],
        "standalone": [names[m] for m in range(len(names)) if m not in touched],
    }