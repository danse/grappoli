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

- **The judge, not the model, is what the model decision is waiting on.**
  The 0.5B judge marks verbatim claims unsupported — ten of ten here — and
  the 3B judge does so too, less systematically, in both directions. The
  only judge that has never been caught misreading a claim is the map's own
  writer, which is the one judge a model comparison cannot use. So neither
  the 0.5B-judged nor the 3B-judged column can rank the two models: the
  numbers are floors, and the deciding measurement is a judge decoupled
  from the model under test. That judge is now built — the NLI
  cross-encoder, `grappoli measure --judge nli` — so the model row stays
  open only until a run scores on it (`architecture.md`, Provisional);
  qwen2.5:0.5b is kept in the meantime, nothing here putting the 3B
  ahead.
- **The redundancy threshold is calibrated on the wrong text.** It is set
  on short prose pairs, but the run scores whole `characterisation_text` —
  `about`, `topics` and `key_claims` concatenated. The 0.250 above is one
  grouped pair, and the record carries no pair score, so the threshold
  cannot be re-read from this run; it should be re-set on the distribution
  it is actually applied to, and the report should name the grouped pair
  the way the faithfulness side names its verdicts, so the 0.25 is readable
  rather than only numerate.
