# Relations

What the model actually does when asked to state how two regions touch,
one run per configuration. The loop's granularity is settled: one
conversation over the whole map, so the model owns the choice of tool.
This file holds the costings behind that shape, then the questions the
choice leaves open — the prompt shape that makes a model name a tool, and
whether native tool calls are the channel worth building on.
`scripts/benchmark_relations.py` costs the granularities and compares the
two channels, and `scripts/probe_tool_calls.py` sweeps prompt shapes; both
keep the raw reply, because the pipeline's retry is exactly what hides
the failure being recorded. Rows are decision inputs, not every probe.

## Granularity cost (2026-10-09)

`qwen2.5:0.5b`, the in-domain fixture (4 regions, 6 edges,
characterisations ≈640 tokens), one first call per approach. This is a
floor for the loop — one call, not the several a full loop makes — so it
compares the shapes, not the final bill.

| approach | prompt tok | gen tok | tool calls | seconds |
|---|---|---|---|---|
| per edge (2 characterisations) | 238 | 92 | 0 | 210 |
| per region (region + neighbours) | 683 | 120 | 0 | 514 |
| whole map (all regions + edges) | 714 | 84 | 0 | 334 |

Every row narrates instead of calling the tool; the raw replies are the
same prose as below. The cost ordering (whole map cheapest of the three)
is real, but it is moot until the tool channel works.

## The tool-call gap (2026-10-09)

The saved characterisation probe had `qwen2.5:0.5b` emit a tool call, and
the real prompts never did. `scripts/probe_tool_calls.py --suite length`
holds the phrasing fixed and adds one note at a time.

| what was sent | prompt tok | tool calls | done |
|---|---|---|---|
| `Call the characterise_region tool with about='quick pickles' …` | 251 | 1 | stop |
| `You are mapping a corpus. Characterise this region: cucumbers …` | 258 | 0–1 | stop/length |
| real region prompt: header + 1 note | 471 | 0 | length |
| real region prompt: header + 2 notes | 613 | 0 | length |
| real region prompt: header + 3 notes | 753 | 0 | length |
| `Call the write_relation tool with source=0, target=1, statement='…'` | 191 | 1 | stop |
| `State in one sentence how region 0 and region 1 touch. Use the … tool.` | 201 | 0 | stop |

### Reading

The switch is the **instruction form, not the conversation size**. The
two relation rows are 191 and 201 prompt tokens — the same size — and
they sit either side of it; adding notes changes nothing but the prose.
The model emits `<tool_call>` when the prompt is a near-literal command
to call a named tool, and otherwise completes the prompt as prose and
stops (`done=stop`, tens of tokens; it does not ramble to the cap). Even
the one task-like hit passed wrong arguments (`region=` where the schema
wants `about`/`topics`), so it was never usable.

The harness is not at fault: the model advertises the `tools` capability
and Ollama's template renders the signatures and the
`<tool_call>{"name": …, "arguments": …}</tool_call>` contract. 0.5B
simply does not follow it when it has content to work on.

### Cue sweep

`--suite cues` sends many imperative shapes over one small edge (two
short characterisation snippets) at temperature 0. An imperative cue
does open the channel on real content: `arguments-related` over the
regions' *topics*, `arguments-object`, `imperative-now`, `fill-template`,
`react-tool-list` and a system message all returned a `write_relation`
call, where the plain task prompt did not. A first pass at cap 64 showed
the longer cues returning empty content *at the cap*; at cap 128 they
fire, so that was truncation, not refusal. "Call the write_relation tool
with arguments related to this text: …" over both regions' `about` fires
at 128.

What they return is another matter. Every one filled `statement` with the
about text, the topic list, a placeholder or the echoed prompt — never a
relation drawn from the two regions. The channel and the content are
separate problems; this records the channel. The `characterise_region`
cue is refused even at cap 128 (128 tokens of content that renders
empty), but characterisation does not need it natively: `format` already
reaches it.

Two consequences for the loop. A cue that *names* the tool tells the
model what to do but removes the choice the loop exists to make; the one
cue that let the model pick (`react-tool-list`) is untested across
rounds. And the reliable structured path stays `format`-constrained JSON
in content — what characterisation ran 4/4 on, and what a `few-shot` cue
here put in content rather than a tool call.

## A bigger model, native (2026-10-09)

`llama3.2:1b` on the same three plain-task prompts, native tools only,
`num_predict` 256. It is here because the loop stays native if *some*
local model names the tools on a task prompt rather than only on a cue.

| approach | prompt tok | gen tok | tool calls | valid relation | seconds |
|---|---|---|---|---|---|
| per edge | 244 | 45 | 1 | no | 46 |
| per region | 683 | 54 | 0 | no | 183 |
| whole map | 714 | 43 | 1 | no | 24 |

1B does name the tool on the plain prompt — the channel 0.5B never opened
— but what it passes is not a relation. Per edge it passed the *tool
schema itself* as the arguments (`{'type': 'object', 'properties': {…
'statement': 'to cover'}}`); whole map passed `source='Region 0'`,
`target='Region 1'` (labels, not ids) and a copied key claim as the
statement; per region named no tool and echoed the schema in content. A
"valid relation" here is the storage layer's shape check — three fields,
integer ids, a non-empty sentence — and 1B fails it every time. The
`valid` column in an earlier draft of this file was a weaker check
(arguments of any shape) and is superseded.

So model size moves the *channel* (native calls appear) without moving
the *content* (the arguments are still not a relation). That separates
two questions the project had been treating as one, and turns the loop's
channel decision into a measurement rather than a hope about model size.

## The channel: native against structured (2026-10-09)

Same prompts, `--channel structured`: the characterisation path — a tool
schema *and* a JSON `format`, native call preferred, content JSON
otherwise. `format` constrains the answer to the schema, so the shape
failures that sank the native runs cannot occur, and the numbers bear
that out.

| model | approach | valid relation | seconds |
|---|---|---|---|
| qwen2.5:0.5b | per edge | yes | 116 |
| qwen2.5:0.5b | whole map | yes | 257 |
| llama3.2:1b | per edge | yes | 87 |
| llama3.2:1b | whole map | no | 380 |

With `format`, **0.5B produces a valid relation per edge** — the weakest
local model, on the real task, first attempt. That is the strongest
single result in this file: the channel, not the model size, was the
blocker, and it matches characterisation's 4/4.

| channel | many relations in one conversation? | valid arguments? |
|---|---|---|
| native (tools only) | yes | no — schema echo, region labels, copied claims |
| structured (one-relation `format`) | no, one per call | yes |

Whole map is the bad cell for `format`, and for a structural reason: the
schema is *one* relation, so a whole-map prompt can only get one back.
0.5B wrote the (0,1) relation and described the rest in prose inside the
statement; 1B overflowed the 256-token cap trying to say them all and the
JSON never closed.

So the two channels fail in opposite directions. A loop that keeps the
model choosing tools (the whole-map shape) *and* gets valid arguments
needs both at once: a `format`-constrained **action** object
(`{"tool": …, …}`) read out of content, with a native call accepted when
one appears. That combination was then measured in the real loop.

## The action object in the loop (llama3.2:1b, 2026-10-09)

`scripts/probe_agent_loop.py` drives the shipped `run_agent` + `Toolbox`
with a real model and no prompt scaffolding: the model must find the
regions, read what it wants, and write each pair. It is asked for an
action object (`{"tool": …, …}`) under `format`, and the adapter turns
that into the tool call `run_agent` already runs; `done` is the action
loop's equivalent of a native message naming no tool.

One 16-round run, `llama3.2:1b`, 893s (~56s a round), hit the cap having
written **1 of 6 edges**:

| what the loop did | count |
|---|---|
| rounds that returned an action object (not native, not prose) | 16/16 |
| `list_regions` calls, all with arguments the tool does not take | 3 |
| reads of region 0, never another region | 3 |
| `write_relation` calls, all on the pair (0, 1) | 10 |
| of those, accepted and appended (all duplicates of the pair) | 5 |
| of those, rejected for a stray `region` argument | 5 |
| distinct pairs written | 1 |

Reading: the action object fixes the **serialisation** where a native
call did not — every round arrived as parseable JSON with a known tool
name. It does not fix the **content**: the model treated every tool as
having the same fields (`list_regions(region=0, target=1)`,
`write_relation(region=0, …)`), never advanced past region 0, and its
accepted statements reproduce one region's own `about` rather than
relating two. So the serialisation problem and the competence problem
are separate, and this channel only solves the first.

Two things the run also exposes, for the orchestration still to build:

- the loop wrote (0, 1) repeatedly. Storage keys relations by pair but
  does not refuse a duplicate append, so a model that loops rewrites a
  done pair; the resume guarantee ("never regenerates a completed
  relation") has to be enforced by the orchestration or the toolbox, and
  currently is not.
- the same run makes the model question concrete: at 1b the whole-map
  loop does not carry, which is the row the model decision settles. The
  equivalent
  `qwen2.5:0.5b` run was stopped for a machine shutdown at round 8 and
  is not recorded here; it should be rerun.

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
