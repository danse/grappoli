# Benchmarks

The decision record. Each file holds the reading in force behind one
pipeline step: a run earns a row only when it changed what we send or
settled a choice, and a later run replaces the reading rather than piling
onto it. The experiments that produced a reading are kept by the date they
were run, under `history/<date>/<step>.md` — the relation loop's are
`history/2026-10-*/relations.md`. What the numbers drive is in
`architecture.md` (Graph, Measurements, Provisional).

| record | step | instrument |
|---|---|---|
| `structure.md`, `structure-heterogeneous.md` | the map's rule | `scripts/benchmark_structure.py` |
| `throughput.md` | generation speed | `scripts/benchmark_throughput.py` |
| `characterisation.md` | the characteriser | `scripts/benchmark_characterisation.py` |
| `relations.md` | the relation loop | `scripts/benchmark_relations.py` |
| `measurement.md` | the four numbers | `grappoli measure` |

Each record is read on its own. A decision that needs several of them at
once — which model, whether a step earns its cost — is settled with the
batch below.

## The batch

`scripts/benchmark_all.py` reruns every step in one pass under the
current defaults and writes the lot to a single JSON under `runs/<date>/`.
That JSON is the raw record of one run, pretty-printed and committed for
reference; the per-step `.md` files above are written from it. It computes
no number of its own: every value is its script's or `measure`'s, and
nothing in the batch picks a model or a default.

Three things sit in different places on purpose. A step file is the reading
in force behind a step, and the source and the docs cite it by path, so it
stays at the top and keeps its name. A run's raw JSON is a snapshot of one
batch, so it goes under `runs/<date>/run.json`. The experiments behind a
reading are kept by the date they were run, under
`history/<date>/<step>.md` — the batch does not run them, so they do
not belong in `runs/`. Each is dated by its directory, not its filename.
`tests/test_docs.py` holds the citations to all of them in place.

In order, it runs:

1. **structure** — the sweep per corpus, against the reference beside
   the notes (arithmetic; no model).
2. **throughput** — one row per model.
3. **characterisation** — one first attempt per region, per model.
4. **read** — a real `grappoli read` per model, on a copy of the corpus,
   recording what it left behind.
5. **relations** — the granularity probe at each conversation size, both
   channels, per model.
6. **measure** — the four numbers once per judge; each model's
   characterisations are read by every judge named, so a map is scored by
   a judge decoupled from the model that wrote it.

```
uv run python scripts/benchmark_all.py
    [--corpus tests/fixtures/in-domain/notes] [--corpus …/heterogeneous/notes]
    [--corpus …/multilingual/notes]
    [--models qwen2.5:0.5b,llama3.2:latest,qwen3:0.6b,functiongemma:270m]
    [--judges qwen2.5:0.5b,llama3.2:latest]
    [--work /tmp/opencode/suite]
    [--out benchmarks/runs/YYYY-MM-DD/run.json]
    [--force]
```

`--models` and `--judges` default independently: the first is what the
batch runs, the second is what scores their maps, and a model added to
the batch is not thereby made a judge of it.

A corpus is copied under `--work` before it is built in: a fixture is
never written to, and each model gets its own copy, so two models'
characterisations do not mix.

**It is built to run overnight.** The structure sweep is arithmetic and
done in seconds; every other step needs Ollama and takes hours. The JSON
is written after every entry, and an entry already present is skipped, so
an interrupted run resumes at the first missing one — re-run the same
command and it picks up where it stopped. `--force` throws the record
away and runs the lot again. Progress goes to stderr; redirect it to keep
a log.

The JSON is keyed by step, then corpus, then model, then judge for
`measure`. A `meta` block records the run's date, its command, the
`build_map` defaults it ran under, the models and judges, and each
corpus's path, reference and note count, so the record reads without
another file beside it. The record's shape and its resume are pinned in
`tests/test_suite.py`; the model calls behind the steps are not run under
pytest.

The `probe_*.py` scripts are not part of the batch: they pin phrasing
questions rather than decide anything, and their findings live under
`history/<date>/relations.md`.
