"""The model interface — the one place generation is called.

Stage 5 compares models by replacing the function here, not by editing
the stages (`architecture.md`, Provisional: qwen2.5:0.5b). Nothing else
in the package imports `ollama`; `build_map` never does, and this module
imports it lazily inside `structured`, so importing the package still
pulls no generation machinery into the process.

Structured output is read from the model either way: a native tool call
is preferred, but on a real region prompt 0.5B answers in content and
never calls the tool, so the content path is the normal one. The request
carries a JSON `format`, which keeps that content a JSON object rather
than prose; a content answer is still parsed whether the JSON is bare or
fenced, and anything else is called malformed
(`benchmarks/characterisation.md`).
"""

import json

DEFAULT_MODEL = "qwen2.5:0.5b"

# A characterisation is ≈150 tokens (throughput.md), but 0.5B answers
# verbosely when it does not call the tool, so this bounds a rambling
# answer while leaving room for a complete one. It matters: with no cap
# the 0.5B answer that does not stop runs to the context limit — minutes
# of generation for one attempt (benchmarks/characterisation.md).
DEFAULT_MAX_TOKENS = 384


class ModelError(Exception):
    """The model produced nothing usable: no tool call and no JSON."""


def structured(prompt: str, schema: dict, model: str = DEFAULT_MODEL,
               max_tokens: int = DEFAULT_MAX_TOKENS) -> dict:
    """Ask `model` to fill `schema` and return its arguments, unvalidated.

    `schema` is an Ollama tool description. The native tool call wins;
    if the model puts the answer in content instead — which 0.5B does on
    a real multi-note prompt — that JSON is parsed as the fallback. The
    request also carries `format`, which is the schema's parameters, so
    a content answer is constrained to valid JSON rather than prose; the
    tool mechanism is still offered and still preferred. Either way the
    result is untrusted — `characterise` validates it, so a malformed
    shape is a retry, not a bad map.
    """
    import ollama

    parameters = schema.get("function", {}).get("parameters", schema)
    reply = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        tools=[schema],
        format=parameters,
        options={"num_predict": max_tokens},
    )
    message = reply["message"]
    calls = message.get("tool_calls")
    if calls:
        arguments = calls[0]["function"].get("arguments")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as err:
                raise ModelError(f"tool-call arguments were not JSON: {err}") from err
        if isinstance(arguments, dict):
            return arguments
        raise ModelError(f"tool-call arguments were {type(arguments).__name__}, not an object")
    return parse_content(message.get("content"))


def parse_content(content) -> dict:
    """Read the JSON object out of a content answer, or raise ModelError.

    Models wrap JSON in prose and code fences whatever they are told, so
    the whole string is tried first and then the span from its first `{`
    to its last `}`. Anything that does not yield an object is a
    malformed attempt, which the retry in `characterise` counts.
    """
    if content is None or not content.strip():
        raise ModelError("no tool call and empty content")
    text = content.strip()
    parsed = _load(text)
    if parsed is None:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            parsed = _load(text[start : end + 1])
    if parsed is None:
        raise ModelError(f"content held no JSON object: {text[:200]!r}")
    return parsed


def _load(text: str):
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None
