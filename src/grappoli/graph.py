"""The graph step. No generation here — arithmetic only.

Three computations in one neighbourhood graph (architecture.md):

* `knn_edges` — a k-nearest-neighbour graph over the note vectors.
* `communities` — the regions, as communities of that graph.
* `representatives` — a deterministic selection within a region:
  centrality, with maximal marginal reduction of redundancy against
  the target count. No model is consulted before this step is fixed.

Edges are (left, right, strength) triples, with left <= right and
strength the similarity of the stronger of the two directions.
"""

from collections.abc import Iterable

import networkx as nx
import numpy as np
from sklearn.neighbors import NearestNeighbors


def knn_edges(vectors: np.ndarray, k: int) -> list[tuple[int, int, float]]:
    n = len(vectors)
    if n < 2:
        return []
    neighbours = NearestNeighbors(n_neighbors=min(k + 1, n), metric="cosine").fit(vectors)
    distances, indices = neighbours.kneighbors(vectors)

    strength: dict[tuple[int, int], float] = {}
    for i in range(n):
        for j, distance in zip(indices[i], distances[i]):
            if j == i:
                continue
            a, b = (i, j) if i < j else (j, i)
            # Similarity of the more similar direction wins; keeps the
            # graph unweighted-and-weighted in one table.
            strength[(a, b)] = max(strength.get((a, b), 0.0), 1.0 - distance)
    return [(a, b, w) for (a, b), w in sorted(strength.items())]


def mutual_edges(vectors: np.ndarray, k: int) -> list[tuple[int, int, float]]:
    """kNN edges kept only where the link is reciprocal.

    The plain graph keeps every directed neighbourhood link, so one
    popular note pulls its would-be neighbours in with it. Mutual
    filtering keeps only edges both ends name — the standard way to
    thin a clique back into structure. `build_map` does not use this
    (the decided rule is plain kNN); `scripts/benchmark_structure.py`
    sweeps it.
    """
    n = len(vectors)
    if n < 2:
        return []
    similarities = vectors @ vectors.T
    directed = set()
    for i in range(n):
        for j in map(int, np.argsort(-similarities[i])[1 : min(k + 1, n)]):
            directed.add((i, j))
    edges = []
    for i, j in directed:
        if (j, i) in directed:
            a, b = (i, j) if i < j else (j, i)
            edges.append((a, b, float(similarities[i, j])))
    return sorted(set(edges))


def partition(
    edges: list[tuple[int, int, float]],
    n_notes: int,
    resolution: float = 1.0,
    weighted: bool = False,
) -> list[set[int]]:
    """Communities of the neighbourhood graph — the regions.

    `weighted` lets louvain use the edge strengths instead of treating
    every edge alike; `resolution` above 1 biases toward finer regions.
    The map uses the defaults; `scripts/benchmark_structure.py` sweeps
    both to find what a foreign corpus needs.
    """
    graph = nx.Graph()
    graph.add_nodes_from(range(n_notes))
    graph.add_edges_from((a, b, {"w": w}) for a, b, w in edges)
    communities = nx.community.louvain_communities(
        graph, weight="w" if weighted else None, resolution=resolution, seed=0
    )
    return [set(c) for c in communities]


def representatives(members: Iterable[int], vectors: np.ndarray, target: int = 5) -> list[int]:
    """Pick the notes that stand for the region.

    A note's centrality is its mean similarity to the other members;
    the pick is greedy, subtracting the strongest similarity to any
    already-chosen note so a second note saying the same thing as the
    first is not picked for saying it again (MMR, lambda 0.85).
    """
    member_list = list(members)
    if not member_list:
        return []
    selected = min(target, len(member_list))
    if selected == len(member_list):
        return sorted(member_list)

    sims = vectors[member_list] @ vectors[member_list].T
    centrality = sims.mean(axis=1)

    chosen: list[int] = []
    remaining = list(range(len(member_list)))
    lam = 0.85
    for _ in range(selected):
        best_idx = max(
            remaining,
            key=lambda i: lam * centrality[i] - (1.0 - lam) * _max_over(sims[i], chosen),
        )
        chosen.append(best_idx)
        remaining.remove(best_idx)
    return sorted(member_list[i] for i in chosen)


def _max_over(similarities: np.ndarray, chosen: list[int]) -> float:
    return max((similarities[c] for c in chosen), default=-1.0)