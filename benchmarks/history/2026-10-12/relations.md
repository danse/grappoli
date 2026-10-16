# Relations — experiments, 2026-10-12

The relation-loop experiments run this date, in order. This is not the
current record — that is `benchmarks/relations.md` — but the trail behind
it: the whole-map one-shot, the bounded loop, and the unscaffolded and
native 3b loops. The loop is `src/grappoli/relations.py` and its behaviour
is pinned in `tests/test_relations.py`.

## Whole map in one `format` call (llama3.2:1b, 2026-10-12)

`scripts/probe_whole_map.py` asks for every relation at once: one
`format`-constrained object, `{"relations": [...]}`, with all regions and
pairs in the prompt. It is the cheap ceiling test for the shape — if one
call cannot hold the map, a multi-round loop cannot either.

It cannot hold it, but not by refusing: 1b *starts* the array —
`{"relations":[{"source":0,"target":1,"statement":"Temperature control
for optimal fermentation…` — and the JSON is still open when the
768-token cap hits at 709s. Six statements copied at `about` length do
not fit one generation. So the failure is one bounded generation, not a
model that cannot conceive the map, and the array shape is not the thing
to conclude on.

## The loop, bounded each round (llama3.2:1b, 2026-10-12)

`scripts/probe_relations_loop.py` keeps the map in the prompt (all
regions and characterisations, the touching pairs named) and bounds each
round instead: one relation, the one-relation `format` schema that worked
per edge, with the loop telling the model which pairs still lack one, a
pair already written refused (the resume guarantee the action-object run
showed was missing), and a stop when all six are covered.

One 12-round run, `llama3.2:1b`, 1030s (~86s a round), hit the cap with
**5 of 6 pairs covered**:

| round | emitted pair | statement |
|---|---|---|
| 1 | (887, 1) | `Region 0 and Region 1 do not touch.` |
| 2 | (1, 2) | `Region 2 and Region 3 touch, Region 0 and Region 1 do not touch…` |
| 3 | (0, 3) | `Region 0 and Region 3 touch, Region 1 and Region 3 touch` |
| 4 | (1, 3) | `Region 0 and Region 1 do not touch, Region 0 and Region 2 do not…` |
| 5 | (0, 2) | `Region 0 and Region 1 do not touch, Region 0 and Region 2 do not…` |
| 6 | (0, 1) | `(0,1) relate to Region 1, (0,3) relate to Region 3` |
| 7–12 | repeats | rewritten already-done pairs, each refused |

Five arrived in rounds 2–6; the last six rounds rewrote a pair that was
already written and were refused. (2,3), the only pair left, was never
written although the feedback named it as the only one.

The coverage is schema coverage, not content. Every statement is noise:
the model lists pairs, or echoes the remaining-pairs line, and round 1
invents id 887. Nothing relates the two regions it names. That is the
same content emptiness the per-edge `format` rows recorded as
shape-valid, now seen at the loop scale.

One confound this probe carries alone: the remaining-pairs line is
injected immediately before generation, so the echoes (`Region 2 and
Region 3 touch, Region 0 and Region 1 do not touch…`) may be the model
continuing that line rather than composing freely. It does not explain
the invented id or the statements that copy one region's own `about`,
which the per-edge probe saw with no feedback line at all, but the
statement-content question should be re-asked without the list in front
of the model.

Two readings:

- Feedback moves *coverage* — 5/6 against the unscaffolded
  action-object loop's 1/6, though the two runs are not confound-free —
  without moving the *content*. The failure is not only holding the map;
  it is composing a sentence about two regions.
- So 1b is out for relations on content grounds, not merely planning,
  and the next row is a bigger model on this same probe.

## The reduced loop at 3b (llama3.2:latest, 2026-10-12)

Same probe, bigger model. `llama3.2:latest` covered **all six pairs in
six rounds** and stopped on its own (a seventh round found nothing left),
1510s: round 1 590s with the model load, the rest ~170–215s a round.

| round | pair | statement |
|---|---|---|
| 1 | (1,2) | Both regions focus on the preservation of food through fermentation or salt preservation. |
| 2 | (1,3) | Both brine recipes use water as a primary ingredient. |
| 3 | (0,2) | Both regions focus on the microbiological aspects of food preservation, with lactobacilli and microorganisms playing key roles in the fermentation process. |
| 4 | (0,3) | Both regions discuss the physical properties and processes involved in food preservation, such as the role of water and salt in the preservation process. |
| 5 | (0,1) | Both regions discuss temperature control as a critical aspect of food preservation. |
| 6 | (2,3) | Both regions discuss the preservation of food through salt preservation and microbiological processes. |

Every statement relates the two regions it names: no invented ids, no
echoed pair list, no copied `about`. No pair was rewritten, so the dedup
refusal never fired, and the loop stopped by itself rather than at the
cap.

Reading: the whole-map content problem is a **model-size** problem, not a
shape problem. Given the map and bounded to one relation a round, 3b
writes relations and 1b cannot. What this row does *not* test is the
agentic shape: the loop removes tool choice, so the only action is the
next relation. Whether 3b chooses tools well across rounds — reading what
it needs, advancing past one region — is the open question, and the next
probe.

## The agentic loop at 3b, unscaffolded (llama3.2:latest, 2026-10-12)

`scripts/probe_agent_loop.py`, the same run as the 1b action-object row
above, with the bigger model. 16 rounds, hit the cap, **0 of 6 edges**,
1414s.

| what the loop did | count |
|---|---|
| rounds returning `list_regions(region=0)` | 16/16 |
| distinct tools chosen | 1 |
| relations written | 0 |

Every round is the identical action, and every round the toolbox returns
the identical error — `list_regions() got an unexpected keyword argument
'region'` — which the model never acts on. It did not read a
characterisation, did not try another tool, did not even change the
argument.

Two candidate causes, both of the harness rather than the model, and both
untested:

- the flat action schema lists `region`, `source`, `target`, `statement`
  as shared properties, so a field that belongs to one tool can leak onto
  another — exactly the `list_regions(region=…)` shape. A per-tool
  argument shape has not been tried.
- the adapter deliberately sends no native `tools`, so the loop's results
  arrive as `role: "tool"` messages with no tool contract in the
  conversation. If the template does not render them, the error is never
  visible and the model cannot correct. Feeding results back as plain
  text has not been tried.

Until one of those is tested, this row says the *channel* cannot drive
3b, not that 3b cannot drive the tools. Read with the row above, it says
the map's **content** is within 3b's reach and its **interface** is not —
yet.

## Native tools in the loop at 3b (llama3.2:latest, 2026-10-12)

The channel every loop run so far had skipped: `--channel native` is
`model.converse`, the tool schemas sent to Ollama. Same unscaffolded
whole-map prompt, 16-round cap. 14 model turns, stopped, **4 of 6 edges**,
3578s.

| what the loop did | count |
|---|---|
| tool calls rejected for a schema-echo argument | 25 |
| first accepted call, `list_regions({})` | 1 (turn 8) |
| distinct pairs written | 4 — (0,1), (1,2), (1,3), (2,3) |
| of those, a duplicate append of (0,1) | 1 |
| statement on every relation | `Both regions concern the cold chain.` |
| how it stopped | content `{"name": "done", …}` — not a tool call |

Two things separate this from the action-object row, and both are the
channel:

- the loop **recovers**. For ~25 calls the model wrapped its arguments as
  a schema echo — `list_regions(tool="list_regions", parameters={})`,
  `read_characterisation(region=0, tool="read_characterisation")` — and
  got the same "unexpected keyword argument" error the action-object run
  did. Unlike that run, it varied the call each time and eventually
  dropped the wrapper: `list_regions({})` succeeded. So the result is
  visible when `tools` are sent, and the action-object fixation was the
  harness burying the error, not the model ignoring it.
- it **advances**. After `list_regions` succeeded it read regions and
  wrote relations, and it stopped by itself.

What it still cannot do:

- **content**: every statement is the prompt's worked example copied
  verbatim. The example is the obvious confound — the reduced loop, whose
  prompt carries no example, wrote real statements — so this row does not
  restate "3b fails content" until the example is removed.
- **stop**: it tried to call a `done` tool `TOOL_SCHEMAS` does not define,
  so the attempt arrived as content and the loop stopped for the wrong
  reason. The action-object schema had `done`; natively the stop is a
  message naming no tool (`architecture.md`, Agent tools), and the prompt
  says "call done", which no tool answers.
- **dedup**: (0,1) was appended twice — the resume gap again.

Reading: native is the channel that lets the loop work — the only
configuration where the model corrects from a tool error and advances
past a region. What remains is argument shape (the wrapper it took 25
calls to shed), an example it copies, and a `done` the prompt names but
no tool answers.

