# grappoli

A command that turns a branch of notes into a map: regions, their
characterisations, and the relations between them. Everything runs
locally — embeddings, a small local model, and arithmetic.

## Quickstart

```console
# install
uv sync
uv tool install .

# read a branch of notes
grappoli read notes/
```

## Where things live

- `product.md` — what it is and why
- `architecture.md` — the decisions, and which are still provisional
- `benchmarks/` — measured numbers (throughput, structure sweeps)
- `tests/` — the behaviour spec; each test names what it pins