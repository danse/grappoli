"""The model interface: how a structured answer is read out of a reply.

`model.structured` is the single seam the model comparison swaps
(architecture.md, Provisional). It must turn either a native tool call or a JSON answer in
content into arguments, and call everything else a malformed attempt so
the retry in `characterise` can count it. These tests inject a fake
`ollama` into `sys.modules` — never the real one — so pinning the
reading does not pull generation machinery into the test process
(test_structure.py pins that it stays out).
"""

import sys
import types

import pytest

from grappoli import model


class FakeChat:
    """Stands in for `ollama.chat`, returning one canned reply."""

    def __init__(self, message):
        self.message = message
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return {"message": self.message}


@pytest.fixture
def ollama_chat(monkeypatch):
    module = types.ModuleType("ollama")

    def install(message):
        fake = FakeChat(message)
        module.chat = fake
        return fake

    # `structured` does `import ollama` at call time, so the fake only
    # has to live in sys.modules until then; monkeypatch removes it.
    monkeypatch.setitem(sys.modules, "ollama", module)
    return install


def test_tool_call_arguments_are_returned(ollama_chat):
    """The native tool call is the primary path the probe confirmed."""
    ollama_chat({"role": "assistant", "content": "", "tool_calls": [
        {"function": {"name": "characterise_region", "arguments": {"about": "a"}}},
    ]})
    assert model.structured("prompt", {"type": "function"}) == {"about": "a"}


def test_string_tool_arguments_are_parsed(ollama_chat):
    """Some servers hand arguments back as JSON text; it is still the answer."""
    ollama_chat({"role": "assistant", "content": "", "tool_calls": [
        {"function": {"name": "characterise_region", "arguments": '{"about": "a"}'}},
    ]})
    assert model.structured("prompt", {"type": "function"}) == {"about": "a"}


def test_non_object_tool_arguments_are_malformed(ollama_chat):
    """Arguments that are not an object cannot be a characterisation."""
    ollama_chat({"role": "assistant", "content": "", "tool_calls": [
        {"function": {"name": "characterise_region", "arguments": "not json"}},
    ]})
    with pytest.raises(model.ModelError):
        model.structured("prompt", {"type": "function"})


@pytest.mark.parametrize("content", [
    '{"about": "a"}',
    '```json\n{"about": "a"}\n```',
    'Here is the answer:\n{"about": "a"}\nHope that helps.',
])
def test_json_in_content_is_the_fallback(ollama_chat, content):
    """A model that answers in content still has its JSON read.

    The fence and the prose are what 0.5B actually emits around JSON
    (benchmarks/characterisation.md); parsing only a bare object would
    reject real answers and burn retries.
    """
    ollama_chat({"role": "assistant", "content": content})
    assert model.structured("prompt", {"type": "function"}) == {"about": "a"}


# Captured from qwen2.5:0.5b on the in-domain fixture's first region, real
# five-note prompt, tool offered: the tool is ignored and the answer is
# prose, not JSON (benchmarks/characterisation.md). This is the failure
# the `format` constraint in `structured` exists to prevent.
OBSERVED_PROSE = (
    "The region of notes you've provided covers a wide range of topics related "
    "to food preservation and fermentation. Let's break it down into key claims "
    "and topics:\n\n1. The cellar holds 14-16\u00b0C through the year.\n   Key "
    "claim: This is a measure of the average temperature in the cellar.\n\n"
    "2. The corner near the boiler drifts to 18\u00b0C and is the shelf for "
    "anything that wants speed.\n   Key claim: This locates a temperature range "
    "around the boiler.\n\n3. Ferments want three different temperatures and "
    "this is the whole game:\n   Key claim: This explains why the cellar and "
    "the corner around the boiler serve different purposes for different types "
    "of fermented foods.\n\n4. Vegetables at 18-22\u00b0C for the quick first "
    "phase, then cooler for storage.\n   Key claim: This indicates how quickly "
    "vegetables can be picked and stored.\n\n5. Vinegar ferments like it warm "
    "\u2014 25\u00b0C is not wasted on them.\n   Key claim: This explains why "
    "vinegar is often used to preserve foods.\n\n6. Nothing wants the fridge "
    "except the finished kimchi and the quick pickles.\n   Key claim: This "
    "explains the reason why the fridge is considered a suitable storage "
    "medium.\n\n7. The kimchi ferment is"
)


def test_observed_prose_answer_is_malformed():
    """The model's real first answer on a region is prose, not JSON.

    Captured from qwen2.5:0.5b on the in-domain fixture (the whole string
    is in benchmarks/characterisation.md). The tool is ignored and no JSON
    object appears, so both extraction paths fail; `structured`'s `format`
    constraint is what turns this into parseable content.
    """
    with pytest.raises(model.ModelError):
        model.parse_content(OBSERVED_PROSE)


# Captured from qwen2.5:0.5b on the same region once `format` was added but
# the answer was still unbounded: valid JSON shape, but the model pasted
# whole notes into key_claims and ran past the token cap, so the object was
# never closed (benchmarks/characterisation.md). The fix is the shortened
# prompt and the schema's maxItems, not a parser that guesses at the tail.
OBSERVED_TRUNCATED = (
    '{"about":"Notes about the temperature control in a cellar for different types '
    'of food,","topics":["temperature control","food preservation"],"key_claims":'
    '["The cellar holds 14-16\u00b0C through the year; the corner near the boiler '
    'drifts to 18\u00b0C and is the shelf for anything that wants speed.","Ferments '
    'want three different temperatures and this is the whole game: vegetables at '
    '18-22\u00b0C for the quick first phase, then cooler for storage. Vinegar ferments '
    'like it warm \u2014 25\u00b0C is not wasted on them.","Log: jars in the corner '
    'ferment visibly faster; jars by the outer wall take twice as long and taste '
    'cleaner at the end. The wall wins for flavor, the corner wins for impatience.",'
    '"The kimchi ferment is a succession, not a single culture. Early on, Leuconostoc '
    'species dominate \u2014 they tolerate cold and start working in the fridge. Later '
    'Weissella and Lactobacillus take over as the acid climb.","This is why kimchi '
    'develops in stages rather than all at once: what you taste on day three is not '
    'what you taste in week three. The community replaces itself as the environment '
    'turns more acidic.","Salt levels around 2-3% keep the vegetables crisp and select '
    'for the lab community over spoilage organisms. Gochugaru is mostly about flavour '
    'and colour; the preservation is the salt and the cold.","The starter is a small '
    'mixed community \u2014 yeast and lactic acid bacteria in one jar \u2014 and it '
    'runs on a schedule. Feed once a day at room temperature; twice a day if the '
    'kitchen is warm.","What you are stabilising is the ratio between the yeasts '
    '(which make gas, the rise) and the bacteria (which make acid, the flavour). Too '
    'little food and the yeast outruns the bacteria; too much and the acid wins'
)


def test_observed_truncated_answer_is_malformed():
    """A cut-off JSON object is a failed attempt, not a partial one.

    Captured from qwen2.5:0.5b with `format` set and no length bound. The
    parser must not try to salvage a missing tail: a half answer is a
    retry, and the real fix is to keep the answer short enough to finish.
    """
    with pytest.raises(model.ModelError):
        model.parse_content(OBSERVED_TRUNCATED)


def test_request_forces_json_format_and_bounds_tokens(ollama_chat):
    """The request carries the tool, a JSON format, and a token cap.

    The format is what makes a content answer JSON rather than prose —
    the failure the region probe exposed — and the cap is what stops an
    uncapped ramble from running for many minutes per attempt.
    """
    fake = ollama_chat({"role": "assistant", "content": '{"about": "a"}'})
    schema = {"type": "function", "function": {"name": "x", "parameters": {"type": "object"}}}
    model.structured("prompt", schema)
    call = fake.calls[0]
    assert call["tools"] == [schema]
    assert call["format"] == {"type": "object"}
    assert call["options"]["num_predict"] == model.DEFAULT_MAX_TOKENS


@pytest.mark.parametrize("message", [
    {"role": "assistant", "content": ""},
    {"role": "assistant", "content": "I cannot help with that."},
    {"role": "assistant", "content": "[1, 2, 3]"},
])
def test_unusable_replies_are_malformed(ollama_chat, message):
    """Empty or non-object output is a failed attempt, not an empty map."""
    ollama_chat(message)
    with pytest.raises(model.ModelError):
        model.structured("prompt", {"type": "function"})
