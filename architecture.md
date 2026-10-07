# architecture

`product.md` holds what the project is and the decisions taken before
any code existed. `roadmap.md` holds the build order. This file holds
what sits behind those decisions: the actual components, and which
choices are still waiting on a measurement.

## Build pipeline

The map is built once, offline, in one direction:

```
notes ──(Stage 1, arithmetic)──▶ regions + edges
      ──(Stage 2, one call per region)──▶ characterisations
      ──(Stage 3, agent loops)──▶ relations
      ──(render)──▶ document          ← no model after this point
```

Each arrow is a component named for the artefact it produces, with the
`roadmap.md` stage that builds it; the artefact names and the stage
numbers are two ways of referencing the same work, and are not to be
confused. No model runs after Stage 3 — making the document from
`relations` is deterministic formatting. The agent of Stage 3 is a
build-time worker: it walks the graph once while the map is being made,
and is gone before anything is read.

## Similarity

Note vectors from `BAAI/bge-small-en-v1.5` — small, fast on CPU, strong
for its size. Its weights being in the local cache is convenience, not
reasoning; they are re-fetchable anywhere.

**TF-IDF cosine runs alongside as a control.** If the encoder does not
beat bag-of-words on structure match, the encoder is not earning its
keep and the simpler one wins.

Two cached cross-encoders — `ms-marco-MiniLM-L-6-v2`,
`mmarco-mMiniLMv2-L12-H384` — are held for Stage 4, where redundancy
has to judge whether two characterisations say the same thing.

## Graph

Cosine similarity → k-nearest neighbour graph → community detection →
regions; cross-community edges become the relations. This is the rule
`product.md` states, worked out: one computation produces both the
regions and how they touch.

Graph construction makes no model calls of any kind. Cosine similarity
is arithmetic over vectors; regions, edges and representatives are all
fixed before Ollama is asked anything.

The model meets this structure only afterwards, in Stage 3 — and only
to state, in words, what the graph's edges already assert.

## Agent tools

The tools are Python functions in our own process; Ollama only ever
names one. It returns a `<tool_call>` block, the loop matches the name,
runs the function, appends the result and calls again — generation
produces the tokens, our code does the work.

- `list_regions` — read the regions from the map structure
- `read_characterisation` — read a stored characterisation
- `compare_regions` — a computation over two characterisations
- `write_relation` — append a relation to the output

The loop itself is `product.md`'s decision; the tool list is what makes
its central constraint real. No tool returns a raw note, because no
such function was ever written — the agent cannot reach the corpus
however it asks.

## Provisional

Choices taken to get moving, with the measurement that can overturn
them:

| Decision | Overturned by |
|---|---|
| Communities as regions | structure match, Stage 4 |
| Flat map | structure match, Stage 5 |
| bge-small over TF-IDF | structure match, Stage 4 |
| qwen2.5:0.5b | faithfulness, Stage 5 |

## Environment

Python 3.12 under `uv`; `sentence-transformers`, `ollama`,
`scikit-learn`, `pytest`. CPU-only — there is no GPU, and no framework
for the agent.

Generation goes through Ollama (`qwen2.5:0.5b`). Its server has no
embedding support and is left as it is.
