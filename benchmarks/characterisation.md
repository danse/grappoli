# Characterisation

Record of what a model actually returns when asked to characterise a
region, one run per configuration. The characteriser's question is what
the chosen model gets wrong; `scripts/benchmark_characterisation.py` sends
each
region's prompt once and keeps the raw reply, because the pipeline's
retry is precisely what hides the failure being recorded. Rows are
decision inputs, not every probe — a run earns one when it changed what
we send.

## Reading (2026-10-09)

`qwen2.5:0.5b`, the four in-domain fixture regions, first attempt each.
The prompt is the region's five representatives and nothing else.

| # | what was sent | result |
|---|---|---|
| 1 | tool only, no `format`, no cap | 0/3 valid. No tool call ever fired; every answer was prose. Region 0 ran 381s and was still going. |
| 2 | tool, no `format`, `num_predict=256` | 0/1 valid. Still prose, now cut at the cap; region 0 took 241s. |
| 3 | tool + `format`, verbose prompt, `num_predict=384` | 0/1 valid. JSON shape, but the answer pasted whole notes and overran the cap, so the object was never closed; 237s. |
| 4 | tool + `format` + brief prompt + `maxItems` + `num_predict=384` | 1/1 valid, 258s. |
| 5 | as 4, the whole pipeline (`grappoli read`) | 4/4 regions valid first attempt, exit 0, ≈4 min/region. |

### Failure modes

1. **The tool is ignored on a real prompt.** A native tool call fired
   only on short toy prompts ("Call the characterise_region tool with
   …"), never on the five-note region prompt. For 0.5B the content path
   is the normal path; the tool is offered first for a larger model that
   may take it, not because 0.5B does.
2. **Without `format`, the content is prose.** The model narrates
   ("Let's break it down into key claims and topics: 1. …") and no JSON
   object appears, so both extraction paths fail. The exact captured
   string is pinned in `tests/test_model.py` as
   `test_observed_prose_answer_is_malformed`.
3. **Unbounded, the answer overruns.** Even constrained to JSON, the
   model quotes whole notes into `key_claims`; uncapped that is many
   minutes of generation, and under a cap it truncates mid-object. The
   captured truncated object is pinned as
   `test_observed_truncated_answer_is_malformed`.

### Behind the fix

- `format` is the schema's parameters, so Ollama constrains a content
  answer to valid JSON rather than prose. It is load-bearing: without it
  the normal path produces nothing parseable.
- The prompt asks for one sentence, three to five short topics, and at
  most five one-clause claims in the model's own words; the schema adds
  `maxItems`. Both keep the answer short enough to close inside the cap,
  and a cap keeps a runaway answer bounded at the record's cost rather
  than the context limit.

### What this says for the rest of the pipeline

- A capped attempt is ≈4 minutes, so the three-attempt cap is ≈12
  minutes for a region that fails all of them. The relation loop's round
  budget inherits this.
- The "fluent prose that is not the asked-for shape" failure is exactly
  what the faithfulness measurement exists to catch; the model reaches
  the shape here, but not by itself.

**Reproduced (2026-10-13).** The batch re-ran the shipped prompt once per
region, first attempt, for both models on both corpora: 4 of 4 valid in
every case — 16 regions — all through the content path the tool never wins,
none failed. The fix holds off the fixture it was found on. 0.5B took about
four minutes a region (997 s in-domain, 1294 s heterogeneous) and 3B about
ten (2535 s, 2513 s), the same roughly three-times factor generation speed
shows in `benchmarks/throughput.md` (`benchmarks/runs/2026-10-13/run.json`).
