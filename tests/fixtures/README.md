# Fixture corpora

Three corpora, written by hand, one fixture per shape. A fixture is a
measurement instrument: the defaults in `build_map`, the provider
choice, and the structure-match baseline are all decided on these
corpora. Their shape therefore *is* the assumed shape of the target
corpus, so the shape is stated here instead of silently assumed. The
measured sweep for each corpus lives in `benchmarks/` (`structure.md`
for in-domain, `structure-heterogeneous.md` for heterogeneous; the
multilingual fixture is measured by the next `benchmark_all` run).

## The axes

The corpora are the same shape — 14 notes, four intended regions of
three notes each, two strays, flat, body text with no headings — and
each varies one further axis. In-domain and heterogeneous differ on
**domain spread**; multilingual holds domain spread at the separable
setting and differs from heterogeneous on **language**, carrying both
English and Italian.

Domain spread is what the embedder actually feels. It shows up in the
similarity margin: mean intra-region similarity minus mean inter-region
similarity. Language shows up in the same place, but for the opposite
reason: the notes a reader groups by subject share meaning across a
language boundary rather than words, so only a provider that reads two
languages into one space can reach the reference.

| axis | in-domain (`in-domain/`) | heterogeneous (`heterogeneous/`) | multilingual (`multilingual/`) |
|---|---|---|---|
| domains | one family — food preservation | four unrelated — hiking, git, houseplants, bikes | four unrelated — beekeeping, film, kayaking, mushrooms |
| languages | English | English | English + Italian, every region split across both |
| e5 intra / inter | 0.876 / 0.842 (margin 0.03) | 0.858 / 0.812 (margin 0.05) | not yet measured (next batch) |
| bge intra / inter (English sweep) | 0.707 / 0.636 (margin 0.07) | 0.687 / 0.555 (margin 0.13) | — (English only) |
| tfidf intra / inter | 0.090 / 0.049 (margin 0.04) | 0.050 / 0.012 (margin 0.04) | not yet measured (next batch) |
| notes | 14 | 14 | 14 |
| regions | 4 × 3 | 4 × 3 | 4 × 3 |
| strays | 2 — one near, one far | 2 — one near, one far | 2 — one near, one far |
| headings | none | none | none |
| cross-region vocabulary | deliberate (names vinegar and jars) | naturally minimal between domains | naturally minimal between domains |
| nesting | flat | flat | flat |

**In-domain is the saturated case.** A margin of 0.03 is thin: the
encoder ranks notes from other regions almost as high as a note's own,
so plain neighbourhoods are mostly cross-region and the graph needs the
mutual filter to recover the structure that is there. This is the hard
case, and the baked defaults are chosen with it in view — the best
worst-case row across the two measured shapes (0.904 here, 0.783 on
heterogeneous; `benchmarks/`).

**Heterogeneous is the separable case.** Disjoint vocabularies between
domains widen the margin (0.05 vs 0.03) and structure match reaches the
reference exactly (ARI 1.000) — but at the opposite corner of the knob
space from in-domain: a small plain neighbourhood, not a mutual-filtered
one. The rule does not transfer outright — the in-domain winner (k=4,
mutual, resolution 2) scores 0.783 here
(`benchmarks/structure-heterogeneous.md`). Which shape the real corpus
has is a decision for the tool's owner; the defaults follow from it.

**Multilingual is the cross-lingual case.** Every region carries notes
in both languages, so the reference can only be reached by clustering
on subject across a language boundary. Bag-of-words cannot do it by
construction: the Italian and English notes of one region share almost
no terms, so the control is expected to fail here harder than anywhere
else, and the encoder wins only if it places a note near its counterpart
in the other language. The fixture exists to measure that; its sweep is
not yet recorded, and the next `benchmark_all` run scores it against the
defaults the other two fixed.

## Shared constraints

- **No headings.** The notes are body text only. Real corpora cannot
  be assumed to carry headings, and a heading is a region label in
  disguise — an embedder that clusters on them is not levelling up.
- **Four clear regions, two strays, and room to be wrong in both
  directions.** A map that omits regions, or that forces the strays
  into one, is wrong — which is what structure match needs to score.
- **Regions are separable by what the notes are about, not by
  exclusive keyword ownership.** Even in heterogeneous, the notes
  say things rather than list terms.
- **The strays do not stay far from home vocabulary.** In-domain:
  books and a garden arrangement share words with the corpus
  ("shelf", "plot", "season") without being about it. Heterogeneous:
  the garden rota names beds, watering and the greenhouse but is
  about organising people; the library note shares nothing.
  Multilingual: the rooftop herb garden borrows the hive's roof, wind
  and even a colony — of aphids — without being about bees; the
  library loan notice, in Italian, shares nothing.

The reference in each `reference-regions.json` is the map a careful
reader would write by hand. Structure match scores candidate maps
against it.
