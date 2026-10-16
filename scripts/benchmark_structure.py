"""Sweep the structure rule over a corpus and print the report.

The map's rule has knobs — similarity provider (bge-small, or TF-IDF as
the control), neighbourhood size, reciprocal-edge filtering, louvain
resolution and weighting — and they decide whether a map holds
together. This script sweeps them and reports the whole space.

With a reference map (the same shape as
tests/fixtures/in-domain/reference-regions.json) every setting is scored with
adjusted Rand index and the winning row is printed — that row is what
the built-in defaults in `grappoli/map.py` should become, the same way
measurement has driven them so far. Without a reference the sweep is
reported and nothing decided: the measures that need no reference
(silhouette, leave-one-out stability) demonstrably do not reproduce
structure match (`benchmarks/structure.md`), so they are not trusted
to choose.

Usage:
    uv run python scripts/benchmark_structure.py NOTES [--reference REF]
        [--ks 2,3,4,5] [--resolutions 1.0,1.5,2.0] [--out REPORT.md]
"""

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np
from sklearn.metrics import adjusted_rand_score

from grappoli.graph import knn_edges, mutual_edges, partition
from grappoli.measure import map_labels
from grappoli.measure import reference_labels as _reference_labels
from grappoli.similarity import build_vectors

PROVIDERS = ("bge", "tfidf")
KS = (2, 3, 4, 5)
RESOLUTIONS = (1.0, 1.5, 2.0)


def sweep(notes: dict[str, str], reference: Path | None,
          ks=KS, resolutions=RESOLUTIONS) -> dict:
    names = list(notes)
    texts = [notes[n] for n in names]
    ref_labels = _reference_labels(reference, names) if reference is not None else None

    rows = []
    partitions: dict[str, list[list[str]]] = {}
    standalone: dict[str, list[str]] = {}
    similarity = {}
    for provider in PROVIDERS:
        vectors = build_vectors(texts, provider)
        similarity[provider] = _similarity_stats(vectors @ vectors.T, ref_labels)
        provider_best = None
        for k in ks:
            for mutual in (False, True):
                edges = mutual_edges(vectors, k) if mutual else knn_edges(vectors, k)
                for resolution in resolutions:
                    for weighted in (False, True):
                        parts, stray = _parts_at(
                            vectors, names, k, mutual, resolution, weighted
                        )
                        row = {
                            "provider": provider, "k": k, "mutual": mutual,
                            "weighted": weighted, "resolution": resolution,
                            "regions": len(parts),
                        }
                        if ref_labels is not None:
                            labels = _map_labels(parts, stray, names)
                            row["ari"] = float(adjusted_rand_score(ref_labels, labels))
                            if provider_best is None or row["ari"] > provider_best["ari"]:
                                provider_best = row
                        rows.append(row)
        if ref_labels is not None:
            best = provider_best
            partitions[provider], standalone[provider] = _parts_at(
                vectors, names, best["k"], best["mutual"],
                best["resolution"], best["weighted"],
            )

    return {
        "date": date.today().isoformat(),
        "notes": len(names),
        "reference": ref_labels is not None,
        "similarity": similarity,
        "rows": rows,
        "best": max(rows, key=lambda r: r["ari"]) if ref_labels is not None else None,
        "partitions": partitions,
        "standalone": standalone,
    }


def _parts_at(vectors, names, k, mutual, resolution, weighted):
    """Communities as `build_map` keeps them, and the notes it leaves out.

    `build_map` drops the edge-less singleton Louvain hands every note with
    no neighbourhood, reporting it as standalone; the sweep must drop it
    too, or it scores a partition the map would never build — one where
    each stray is its own region, which reads higher against a reference
    that folds its own strays. The strays come back so the caller can
    label them `STANDALONE`, the way `map_labels` labels a built map.
    """
    edges = mutual_edges(vectors, k) if mutual else knn_edges(vectors, k)
    touched = {a for a, b, _ in edges} | {b for a, b, _ in edges}
    parts = [
        c for c in partition(edges, len(names), resolution, weighted)
        if c and any(m in touched for m in c)
    ]
    parts.sort(key=min)
    stray = [names[m] for m in range(len(names)) if m not in touched]
    return [[names[m] for m in sorted(c)] for c in parts], stray


def _map_labels(parts: list[list[str]], stray: list[str], names: list[str]) -> np.ndarray:
    """Label a candidate partition as `measure.map_labels` labels a map.

    The same rule on purpose: the sweep chooses the defaults and
    `measure` scores the map those defaults build, so both must read the
    same partition the same way (`benchmarks/structure.md`).
    """
    mapping = {
        "regions": [
            {"id": cid, "members": members} for cid, members in enumerate(parts)
        ],
        "standalone": stray,
    }
    return map_labels(mapping, names)


def _similarity_stats(similarities: np.ndarray, ref_labels) -> dict:
    n = len(similarities)
    if ref_labels is None:
        off_diag = similarities[~np.eye(n, dtype=bool)]
        return {
            "mean": float(off_diag.mean()),
            "p10": float(np.percentile(off_diag, 10)),
            "p90": float(np.percentile(off_diag, 90)),
        }
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    intra = [similarities[i, j] for i, j in pairs if ref_labels[i] == ref_labels[j]]
    inter = [similarities[i, j] for i, j in pairs if ref_labels[i] != ref_labels[j]]
    return {
        "mean_intra": float(np.mean(intra)) if intra else float("nan"),
        "mean_inter": float(np.mean(inter)) if inter else float("nan"),
    }


def render(report: dict) -> str:
    lines = [f"# Structure sweep — {report['date']}"]
    if report["reference"]:
        lines.extend([
            "",
            f"{report['notes']} notes, scored against the reference "
            "with adjusted Rand index (ARI; 1 is the reference itself).",
        ])
    else:
        lines.extend(["", f"{report['notes']} notes, no reference — ARI is "
                           "impossible, so rows are a behaviour table only."])
    lines.extend(["", "## Similarity"])
    if report["reference"]:
        lines.append("| provider | mean intra-region | mean inter-region |")
        lines.append("|---|---|---|")
        for provider, stats in report["similarity"].items():
            lines.append(f"| {provider} | {stats['mean_intra']:.3f} | {stats['mean_inter']:.3f} |")
    else:
        lines.append("| provider | mean similarity | p10 | p90 |")
        lines.append("|---|---|---|---|")
        for provider, stats in report["similarity"].items():
            lines.append(f"| {provider} | {stats['mean']:.3f} | {stats['p10']:.3f} | {stats['p90']:.3f} |")

    lines.extend(["", "## Sweep"])
    lines.append("| provider | k | mutual | weighted | resolution | regions | ARI |")
    lines.append("|---|---|---|---|---|---|---|")
    rows = report["rows"]
    if report["reference"]:
        rows = sorted(rows, key=lambda r: r["ari"], reverse=True)
    for row in rows:
        bold = "**" if report["reference"] and row is rows[0] else ""
        ari = f"{row['ari']:.3f}" if "ari" in row else ""
        lines.append(
            f"| {bold}{row['provider']}{bold} | {row['k']} | "
            f"{'yes' if row['mutual'] else 'no'} | "
            f"{'yes' if row['weighted'] else 'no'} | {row['resolution']:g} | "
            f"{row['regions']} | {ari} |"
        )

    if report["reference"] and report["best"] is not None:
        lines.extend(["", "## Best map (by ARI)"])
        best = report["best"]
        lines.append(f"_Decided: {best['provider']}, k={best['k']}, "
                     f"mutual={'yes' if best['mutual'] else 'no'}, "
                     f"weighted={'yes' if best['weighted'] else 'no'}, "
                     f"resolution={best['resolution']:g}, "
                     f"ARI {best['ari']:.3f}._")
        for provider, parts in report["partitions"].items():
            lines.append("")
            lines.append(f"### {provider} at its own best")
            for cid, members in enumerate(parts):
                lines.append(f"- r{cid}: {', '.join(members)}")
            stray = report.get("standalone", {}).get(provider, [])
            if stray:
                lines.append(f"- standalone: {', '.join(stray)}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notes", help="path to the branch of notes")
    parser.add_argument("--reference", default=None,
                        help="reference regions to score against (same shape as "
                             "tests/fixtures/in-domain/reference-regions.json)")
    parser.add_argument("--ks", default="2,3,4,5", help="neighbourhood sizes to sweep")
    parser.add_argument("--resolutions", default="1.0,1.5,2.0",
                        help="louvain resolutions to sweep")
    parser.add_argument("--out", default=None, help="write the report here instead of stdout")
    args = parser.parse_args()

    from grappoli.corpus import load_corpus

    notes = load_corpus(args.notes)
    if not notes:
        print(f"{args.notes}: no markdown notes found", file=sys.stderr)
        sys.exit(1)
    ks = tuple(int(x) for x in args.ks.split(","))
    resolutions = tuple(float(x) for x in args.resolutions.split(","))
    reference = Path(args.reference) if args.reference else None

    report = sweep(notes, reference=reference, ks=ks, resolutions=resolutions)
    text = render(report)
    if args.out is None:
        print(text, end="")
    else:
        Path(args.out).write_text(text)

    if reference is None:
        print("(no reference: nothing to score against, nothing decided)", file=sys.stderr)
        return

    best = report["best"]
    print(f"decided: {best['provider']}, k={best['k']}, mutual={best['mutual']}, "
          f"resolution={best['resolution']:g}, weighted={best['weighted']}, "
          f"ARI {best['ari']:.3f} — bake these into build_map's defaults if this "
          "corpus is representative", file=sys.stderr)


if __name__ == "__main__":
    main()