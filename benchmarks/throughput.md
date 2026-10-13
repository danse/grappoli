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

## Reading (2026-10-08)

Default thread count is the right setting. One thread starves prefill
(3.1 → 1.9 tok/s); four threads oversubscribe two cores and collapse
decode (2.3 → 0.5 tok/s). So ~3 tok/s prefill and ~2.3 tok/s generation
are the numbers to size against — it is a hardware floor, not a config
mistake.

One region characterisation (≈450-token prompt, ≈150-token answer) is
roughly four minutes; sixteen regions is about an hour of generation.
The relation agent's round budget derives from these figures.