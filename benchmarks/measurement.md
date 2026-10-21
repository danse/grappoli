# Measurement

Record of `grappoli measure` runs: the four numbers for a candidate map,
and what each rests on. A run earns a row when it is a decision input.
Comprehensiveness and structure match are arithmetic and are pinned by
tests; the two model-backed numbers — redundancy and faithfulness — are
what a live run is for, because their thresholds and their judge are
still provisional.

The numbers are defined in `architecture.md` (Measurements) and
implemented in `grappoli.measure`.

## The run — both fixtures, both models, both judges (2026-10-13)

The `measure` step of the batch (`benchmarks/runs/2026-10-13/run.json`),
run by `uv run python scripts/benchmark_all.py`. Each corpus's map is read
once per model's characterisations, and those characterisations are read by
every judge named — both models plus the default `llama3.2:latest` — so
each map is scored by the model that wrote it and by the other. The map is
the same in all four rows of a corpus: it is built before any model runs,
and the models change only the prose. In-domain is 4 regions (3 + 3 + 1 + 3
members) with 4 of its 14 notes standalone; heterogeneous is 4 regions
(3 + 4 + 4 + 3) with none standalone.

| corpus | characteriser | judge | compr. | redundancy | faithfulness | structure |
|---|---|---|---|---|---|---|
| in-domain | qwen2.5:0.5b | qwen2.5:0.5b | 0.714 | 0.000 | 0.842 | 0.578 |
| in-domain | qwen2.5:0.5b | llama3.2:latest | 0.714 | 0.000 | 0.684 | 0.578 |
| in-domain | llama3.2:latest | qwen2.5:0.5b | 0.714 | 0.250 | 0.600 | 0.578 |
| in-domain | llama3.2:latest | llama3.2:latest | 0.714 | 0.250 | 0.800 | 0.578 |
| heterogeneous | qwen2.5:0.5b | qwen2.5:0.5b | 1.000 | 0.000 | 0.850 | 0.729 |
| heterogeneous | qwen2.5:0.5b | llama3.2:latest | 1.000 | 0.000 | 0.650 | 0.729 |
| heterogeneous | llama3.2:latest | qwen2.5:0.5b | 1.000 | 0.000 | 0.636 | 0.729 |
| heterogeneous | llama3.2:latest | llama3.2:latest | 1.000 | 0.000 | 0.636 | 0.729 |

Comprehensiveness and structure match do not move down a column's rows:
they are the map's, not the model's. Redundancy separates the models once —
the 3B in-domain characterisations repeat one pair (0.250), where the 0.5B
map and both heterogeneous maps repeat nothing. The larger model is the
more redundant one where the corpus is saturated, which is the cost this
number exists to show.

### The judge is the larger term

The same characterisations score differently under the two judges by more
than the two characterisers differ from each other. On the in-domain map
the 0.5B characterisations read 0.842 under the 0.5B judge and 0.684 under
the 3B one; the 3B characterisations read 0.600 under the 0.5B judge and
0.800 under the 3B one. The judge moves the number more than the map does.

The 0.5B judge is unusable, and this run shows it cleanly: every claim it
marked unsupported on the 3B characteriser — six in-domain, four
heterogeneous — is verbatim or near-verbatim in the region's own notes.

| corpus | claim the 0.5B judge refused (3B characteriser) | in the notes? |
|---|---|---|
| in-domain | Salt levels around 2-3% select for the lab community over spoilage organisms | yes — `kimchi-microbiology`: "Salt levels around 2-3% … select for the" |
| in-domain | The starter culture runs on a schedule, with yeast and lactic acid bacteria in a mixed community | yes — `sourdough-starter-rhythm`: "yeast and lactic acid bacteria in one jar … runs on a schedule" |
| in-domain | Salt is added to taste, not to preserve | yes — `quick-pickles-vinegar-ratio`: "Add salt to taste, not to preserve" |
| in-domain | Timing: three days for halves, a week for whole cucumbers | yes — `quick-pickles-vinegar-ratio`, verbatim |
| in-domain | A 5% brine draws moisture across the membrane, equalizing osmolarity and preventing spoilage | yes — `osmosis-and-salt`: "until the osmolarity equalises" |
| in-domain | The pH 4.6 line is the critical threshold for Clostridium botulinum growth | yes — `ph-and-spoilage`: "The line at pH 4.6 is the one that matters … botulinum cannot grow" |
| heterogeneous | Brake pads wear faster where you brake hardest | yes — `brake-pad-replacement`, verbatim |
| heterogeneous | most houseplants die from overcare | yes — `watering-houseplants`: "Most houseplants die from overcare" |
| heterogeneous | shading and ventilating are rotated weekly | yes — `community-garden-rota`: "Shading, ventilating … rotate weekly" |
| heterogeneous | The forecast is more reliable on the ridge at midday | yes — `route-planning-and-weather`: "ridge at midday rather than the one for the valley" |

Ten refusals, ten supported. The 0.5B judge does not check a claim against
its evidence; it marks supported prose unsupported. Its four numbers
(0.842, 0.850, 0.600, 0.636) are read as noise.

The 3B judge is better and still not trustworthy. On the 0.5B in-domain map
it refused six claims, and at least three are verbatim — "three days in,
smells right" (`cucumber-pickling-log`), "The sequence is predictable …
milky cloudiness" and "the smells are never wrong" (`lacto-fermentation-101`).
On the 0.5B heterogeneous map it refused seven, among them "Wipe the chain
dry after wet rides" (`bike-chain-care`) and "Three layers are enough until
the thermometer drops below freezing" (`hiking-gear-layering`), both
verbatim. Where the 0.5B judge is systematically wrong, the 3B judge is
wrong often enough that its numbers are floors too.

## The run — the decoupled judge (2026-10-20)

The `measure` step of the batch (`benchmarks/runs/2026-10-20/run.json`),
with the NLI cross-encoder as the only judge: one row per corpus and
characteriser, the judge named `nli` in the record. The map is the map's —
`build_map` calls no model — so the two rows of a corpus share their
comprehensiveness and their structure match, and differ only in the prose
the characteriser wrote, the redundancy of that prose, and the number that
scores it.

| corpus | characteriser | judge | compr. | redundancy | faithfulness | structure |
|---|---|---|---|---|---|---|
| in-domain | qwen2.5:0.5b | nli | 0.857 | 0.800 | 0.478 | 0.904 |
| in-domain | llama3.2:latest | nli | 0.857 | 0.800 | 0.800 | 0.904 |
| heterogeneous | qwen2.5:0.5b | nli | 1.000 | 0.800 | 0.857 | 0.783 |
| heterogeneous | llama3.2:latest | nli | 1.000 | 0.800 | 0.765 | 0.783 |
| multilingual | qwen2.5:0.5b | nli | 1.000 | 0.750 | 0.950 | -0.044 |
| multilingual | llama3.2:latest | nli | 1.000 | 0.500 | 0.750 | -0.044 |

### The first NLI column was an artefact

The 2026-10-19 run judged the same way and scored 0.000 to 0.235, with 95
of its 112 claims rejected — every one of them below 0.46 entailment, mean
0.11 — and 31 of those 95 were claims the region's own notes state
verbatim (7 of 21 in-domain, 3 of 13, 7 of 18, 5 of 14, 8 of 18, 1 of 11).
A judge that rejects "check the water level every two weeks", which is the
note's own sentence, is not judging the claim; it is measuring the
premise. That column of the 2026-10-19 record is invalid and is kept only
as the record of that run; the 2026-10-20 column is the one to read.

The cause is the premise. A region's evidence is a note or two of prose,
and the cross-encoder is trained on sentence pairs: given the whole note,
the same claim scores 0.06, and given the sentence that carries it, 0.97.
Entailment drifts to neutral as the premise grows to cover more than the
claim. So the evidence is now cut into sentences and adjacent pairs — a
pair keeps an anaphor and its antecedent together — and the claim is
supported when any premise entails it. A span longer than the model's
input is still cut by tokens, so no note is truncated.

The same claim, on the same notes: 0.08 before, 0.99 after.

The 2026-10-20 run re-characterised the corpora, so its claims are not the
2026-10-19 run's claims and the two columns are not one map scored twice.
What the two runs share is the verdict: 26 claims remain unsupported, and
one of them is in its region's notes verbatim — "turning back is still an
easy decision", at 0.48 against a 0.50 threshold, a hair under the line.
The rest are the character's: some are claims the notes do not make at all
— "always use soap to clean" (the note says never soap), "a dry airlock"
(the note calls it an open door for mould), "fruits are best at 25°C" (the
note gives 25°C to vinegar ferments), "jars are chosen based on taste" —
and some are true in substance but not in a form the judge can credit,
such as "always replace the bung" against the note's "Replace the bung
with the year", or a claim written as a bare fragment. What is left of the
0.5B's in-domain cell is the model, not the judge.

### The judge ran in float16 on CPU

The checkpoint declares `torch_dtype: float16` and the loader honours it.
On CPU that is emulated, and it is not cheap: one short pair took 28.8 s
in float16 and 2.0 s in float32, so the judge was fourteen times slower
than it needed to be, and the sentence-level premises would have cost the
run a day. The weights are raised on CPU now, and the six cells of the
2026-10-20 run were measured in the last two hours of it.

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

## Reading (2026-10-20)

- **The decoupled judge does not separate the two models.** qwen2.5:0.5b
  scores 0.478, 0.857 and 0.950 against llama3.2:latest's 0.800, 0.765 and
  0.750 over the three corpora: behind on the saturated in-domain corpus,
  ahead on the other two, level on the average (0.762 against 0.772). The LLM
  judges could not rank them at all
  ("The judge is the larger term"); this judge can rank them and finds
  them the same, which is the answer the row was waiting for. What it does
  not settle is which model ships: the smaller one is three times the
  throughput, and the step this record does not measure separates them —
  asked one pair at a time, the smaller model writes one region's notes
  where a relation belongs (`benchmarks/relations.md`, "What the shape
  rests on"). The shipped model is decided on that, not on these numbers
  (`architecture.md`, Provisional). Note what the level is made of: the
  judge is strict on paraphrase and on a claim written as a fragment —
  "always replace the bung" against the note's
  "Replace the bung with the year" scores 0.03 — so this is the level of
  the claims, not a ceiling on what a claim can earn.
- **The redundancy threshold is calibrated on the wrong text.** It is set
  on short prose pairs, but the run scores whole `characterisation_text` —
  `about`, `topics` and `key_claims` concatenated. The 0.250 above is one
  grouped pair, and the record carries no pair score, so the threshold
  cannot be re-read from this run; it should be re-set on the distribution
  it is actually applied to, and the report should name the grouped pair
  the way the faithfulness side names its verdicts, so the 0.25 is readable
  rather than only numerate. The 2026-10-20 run shows what that costs:
  0.800, 0.800, 0.800, 0.800, 0.750 and 0.500, which is most
  characterisations flagged as repeating another region. The threshold was
  also calibrated on the old encoder — the logit scale quoted above is
  `ms-marco-MiniLM-L-6-v2`'s, and the run has used
  `mmarco-mMiniLMv2-L12-H384-v1` since 2026-10-16 with the same 0.0, so
  it is uncalibrated on both counts. The number is not usable until it is
  set again.
