# Fixture corpus

Fourteen notes under `notes/`, written by hand for this project. The
reference regions in `reference-regions.json` are the map a careful
reader would write by hand; Stage 4's structure match scores candidate
maps against them.

Design constraints:

- **No headings.** The notes are body text only. Real corpora cannot be
  assumed to carry headings, and a heading is a region label in
  disguise — an embedder that clusters on them is not levelling up.
- **Four clear regions, two strays.** `notes/` holds three notes in
  each of four topics — brine and pickling, fermentation biology,
  preservation chemistry, equipment and storage — plus two notes that
  belong to none of them. A map that omits four regions, or that forces
  the strays into one, is wrong; there is room to be wrong in both
  directions, which is what structure match needs.
- **Cross-region vocabulary is deliberate.** The pickling log names
  vinegar and ferment; the chemistry notes name brine and jars. The
  regions are separable by what the notes are about, not by exclusive
  keyword ownership.
- **The strays do not stay near home.** Books and a garden arrangement
  share vocabulary with the corpus ("shelf", "plot", "season") without
  being about it.