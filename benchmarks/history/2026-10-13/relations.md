# Relations — experiments, 2026-10-13

The relation-loop experiment run this date: the first live `grappoli read`
runs of the shipped loop. This is not the current record — that is
`benchmarks/relations.md`. The loop is `src/grappoli/relations.py` and its
behaviour is pinned in `tests/test_relations.py`.

## The shipped loop, live (llama3.2:latest, 2026-10-13)

Every row above drove `run_agent` from `scripts/`; these are the first
runs of `grappoli read` itself — the map, characterisation resumed from
disk, then the shipped relation prompt and budget (16 rounds), writing
`NOTES/.grappoli/relations`. Same fixture, same characterisations.

Both named `list_regions` natively and then stopped, **0 of 6**:

| run | rounds | what it called | how it stopped | seconds |
|---|---|---|---|---|
| task + tools, no example | 2 | `list_regions()` → ok | content (stop reason not yet traced) | 873 |
| one tool a turn, procedure | 2 | `list_regions()` → ok | content: three bare `write_relation` objects | 660 |

The tightened run's stop is the one to read. It did not end in prose. The
message was three JSON argument objects concatenated, one per relation,
with no `tool_calls` and no tool name:

```
{"source": 0, "target": 2, "statement": "Region 0 is characterised and Region 2 is characterised and Region 2 is a member of Region 0."}
{"source": 0, "target": 3, "statement": "… Region 3 is a member of Region 0."}
{"source": 1, "target": 3, "statement": "… Region 3 is a member of Region 1."}
```

It had read no characterisation, and the statements relate a region to
itself by membership — the same content emptiness the per-edge rows
recorded. The channel is the new part: 3b calls `list_regions` natively
(so the interface is open), then serialises its *writes* as content JSON,
several at once, which is neither a native call nor one parseable object.
The loop reads that as the stop, correctly, and the tool-call trace shows
it.

Reading: this drops the two confounds the native probe row carried — the
worked example it copied (there is none here) and the `done` tool no tool
answers (the stop is a message naming no tool, and the model does stop on
its own). What is left is the failure that row was reaching for: at 3b
the map's **content** is reachable (the reduced loop, 6/6) but the model
does not drive the whole-map tools **unassisted** — it lists the map, then
writes in the wrong channel without reading. Whole-map autonomous native
is out of this model's reach on this hardware; guided to one pair a round
it is not. That is the row the model decision settles, and it is now a
measurement rather than a hope about size.
