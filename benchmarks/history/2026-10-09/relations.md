# Relations — experiments, 2026-10-09

The relation-loop experiments run this date, in order. This is not the
current record — that is `benchmarks/relations.md` — but the trail behind
it: the granularity costings, the prompt-shape sweep, and the first channel
comparison. The loop is `src/grappoli/relations.py` and its behaviour is
pinned in `tests/test_relations.py`.

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

