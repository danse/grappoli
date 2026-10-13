# Measurement

Record of `grappoli measure` runs: the four numbers for a candidate map,
and what each rests on. A run earns a row when it is a decision input.
Comprehensiveness and structure match are arithmetic and are pinned by
tests; the two model-backed numbers — redundancy and faithfulness — are
what a live run is for, because their thresholds and their judge are
still provisional.

The numbers are defined in `architecture.md` (Measurements) and
implemented in `grappoli.measure`.

## The run — in-domain fixture, 2026-10-13

```
uv run grappoli measure /tmp/opencode/read-fixture \
    --reference tests/fixtures/in-domain/reference-regions.json
```

The branch is the 14-note in-domain corpus; the map in
`.grappoli/map.json` is 4 regions (3 + 3 + 1 + 3 members) with 4
standalone notes, and records the current defaults (bge, k=5, mutual,
weighted, resolution 2.0). The judge is `qwen2.5:0.5b`, the model the
pipeline currently uses; redundancy uses the cached
`cross-encoder/ms-marco-MiniLM-L-6-v2`.

| number | value | rests on |
|---|---|---|
| comprehensiveness | 0.714 | 10 of 14 notes homed; 4 standalone |
| redundancy | 0.250 | 4 characterisations, one pair grouped |
| faithfulness | 0.667 | 18 claims: 12 supported, 6 unsupported, 0 undecided |
| structure match | 0.578 | ARI against `reference-regions.json` |

### The judge's verdicts

Six of the eighteen claims came back unsupported:

| region | claim |
|---|---|
| r0 | Fermentation is a complex process involving temperature and time control |
| r1 | The brine smells right — clean sour, no off notes. |
| r1 | The brine stays clear if the jar is not opened, but if opened, it clouds but the pickles are fine for weeks. |
| r2 | anaerobic |
| r2 | pH reduction |
| r3 | at that point most spoilage organisms can no longer multiply |

The calls are not uniform: the first two regions alone gave four
supported and three unsupported, so the judge is discriminating rather
than agreeing with everything — the main risk with a 0.5B judge. Whether
each call is *right* still needs a reading by eye; the verdicts are
recorded here so it can be done. Two of the six are fragments, not claims
("anaerobic", "pH reduction"), which `benchmarks/characterisation.md`
already shows 0.5B produces as `key_claims`; a fragment cannot be stated
by the notes, so the judge is marking the characterisation's shape as
much as the map. The remaining four are checkable sentences the judge
declined. None exhausted its attempts, so `undecided` is 0 and the 0.667
is the judge's own reading rather than a failure to answer.

## The threshold behind redundancy

`ms-marco-MiniLM-L-6-v2` is a raw-logit model (Identity activation), so
`REDUNDANCY_THRESHOLD` is set on logits, not a probability. When it was
chosen these pairs were scored (higher order kept):

| pair | score |
|---|---|
| identical text | 8.09 |
| a paraphrase | 5.60 |
| overlapping but distinct | −1.21 |
| unrelated | −11.07 |
| six real in-domain pairs | −2.14 … −8.87 |

`0.0` was placed between the paraphrase and the overlapping-but-distinct
cases, so "another phrasing of this" groups and "something else" does
not. The six real pairs all fell below it, so on that calibration the
threshold is conservative on real text.

## Reading (2026-10-13)

- **The judge is usable at 0.5B, with its verdicts read.** It answers,
  it discriminates, and it records disagreement instead of smoothing it
  away, which was the fear with a model this small. It is still the model
  under test, so the faithful number belongs beside the verdicts, not
  alone; the two fragments it flagged are a true fact about the
  characterisations.
- **The redundancy threshold is calibrated on the wrong text.** The run
  scores whole `characterisation_text` — `about`, `topics` and
  `key_claims` concatenated — but the calibration pairs were short prose,
  and here one concatenated pair cleared `0.0` where every calibrated
  pair was negative. The threshold should be re-set on the distribution
  it is actually applied to, and the report should name the grouped pair
  the way the faithfulness side names its verdicts, so the 0.25 is
  readable rather than only numerate.
