# Throughput

Record of measured generation speed, one row per run. The figure decides
how many regions characterisation can afford and how many rounds the
relation agent may run. Rows are produced by
`scripts/benchmark_throughput.py`; not every run of the script earns a
row — a row is a decision input.

| date | model | prompt_tok | prompt tok/s | gen_tok | gen tok/s | wall s |
|---|---|---|---|---|---|---|
| 2026-10-07 | qwen2.5:0.5b (probe, tool-call, no num_predict) | 171 | 2.1 | 28 | 1.3 | 106 |
| 2026-10-08 | qwen2.5:0.5b (default threads) | 278 | 3.1 | 112 | 2.3 | 144.0 |
| 2026-10-08 | qwen2.5:0.5b (num_thread=1) | 278 | 1.9 | 256 | 1.5 | 324.0 |
| 2026-10-08 | qwen2.5:0.5b (num_thread=4) | 278 | 3.3 | 212 | 0.5 | 517.9 |
| 2026-10-13 | qwen2.5:0.5b (batch) | 278 | 2.4 | 256 | 1.9 | 252.0 |
| 2026-10-13 | llama3.2:latest (batch) | 268 | 1.1 | 123 | 0.6 | 473.6 |

## Reading (2026-10-13)

Default thread count is the right setting (2026-10-08). One thread
starves prefill (3.1 → 1.9 tok/s); four threads oversubscribe two cores
and collapse decode (2.3 → 0.5 tok/s). It is a hardware floor, not a
config mistake, and the batch reproduces it at defaults: 2.4 tok/s
prefill and 1.9 tok/s generation for qwen2.5:0.5b.

The second model is roughly a third of the first: llama3.2:latest
prefills at 1.1 tok/s and generates at 0.6, on the same prompt. Note
that it stopped at 123 of the 256 requested tokens — it hit its own
answer end, not the cap — so its rate is over a full generation.

At these rates one region characterisation (≈450-token prompt,
≈150-token answer) is about four minutes under 0.5B and about eleven
under 3B; sixteen regions is an hour and three hours respectively. The
relation agent's round budget derives from these figures.

The 1.9 here is the figure to size against, not the 2.3 of the
2026-10-08 row. Same model, prompt and thread setting; the rows differ
in how much they generated (112 against 256 tokens) and in when they
ran, and the difference is not attributed — the batch's figure is the
one the pipeline's defaults are measured with
(`benchmarks/runs/2026-10-13/run.json`).