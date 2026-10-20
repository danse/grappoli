"""The four measurements of a candidate map.

Four numbers, each answering a different question about the same map:

* `comprehensiveness` — the share of the corpus with a home in the map.
  A region is a home; a note the map leaves standing alone has none, so
  a map that explains little of the corpus scores low however tidy its
  regions are.
* `redundancy` — the share of characterisations that repeat something
  another region already says. Measured beside comprehensiveness because
  redundancy reads as coverage: a map that repeats itself five ways has
  five homes and says two things, and covering the corpus alone rewards
  exactly that.
* `faithfulness` — the share of atomic claims, each a `key_claim`,
  supported by the notes of its own region. The judge works under an
  explicit rubric, because free-form scoring rewards fluency and fluency
  is precisely how a small model fails (`architecture.md`, Measurements).
* `structure match` — adjusted Rand index of the map's regions against a
  reference map, the same score `scripts/benchmark_structure.py` sweeps
  the rule with, so a candidate map is judged by the ground the rule was
  chosen on.

Reference-free scores are deliberately absent: ROUGE scores copying,
and the measures that need no reference — silhouette, leave-one-out
stability — demonstrably do not reproduce structure match
(`benchmarks/structure.md`).

The two model-backed measures take their model as an argument: the
redundancy `compare` is the cross-encoder the architecture holds for it,
and the faithfulness judge is either the `structured` interface
characterisation runs through (`llm`) or a decoupled NLI cross-encoder
(`judge`). All are injected, so every rule here is pinned by a test with
a stub and the real models are exercised only in live runs
(`benchmarks/measurement.md`). The model-backed judge is the model under
test, a known limit rather than a hidden one: an undecided or wrong
verdict is recorded as found, and the rubric is not tuned until the
number improves. The NLI judge exists to lift that limit — it is
decoupled by construction and effectively deterministic — and is the
judge the model decision has been waiting on.
"""

import json
import re
from pathlib import Path

import numpy as np
from sklearn.metrics import adjusted_rand_score

from .model import ModelError, structured

# Labels in the two label spaces the structure score compares. The map's
# standalone list has no region id, and a note a candidate map never
# places is not the same as one it deliberately leaves alone, so both
# get a name of their own rather than being folded together.
STANDALONE = "standalone"
UNMAPPED = "unmapped"

# A cross-encoder answers a query/passage relevance question. Neither of
# two characterisations is the other's query, so both orders are scored
# and the higher kept (`cross_encoder`). `mmarco` is the multilingual
# counterpart of the English ms-marco and is raw-logit the same way (its
# config declares Identity activation): near-identical text scores high
# positive, unrelated text several points negative, and 0 is the boundary
# between "another phrasing of this" and "something else". That boundary
# was measured on the English model's pairs
# (`benchmarks/measurement.md`) and is carried to the multilingual one
# unmeasured.
# It is provisional, like every threshold this project has set, and the
# fixture is what would move it.
REDUNDANCY_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
REDUNDANCY_THRESHOLD = 0.0

# The decoupled faithfulness judge: an NLI cross-encoder scores (region
# notes, claim) straight to entailment/neutral/contradiction, so the
# judge is not the model under test. `mDeBERTa` is the multilingual
# counterpart of the English `cross-encoder/nli-deberta-v3-base`, chosen
# for the same reason `REDUNDANCY_MODEL` is the multilingual mmarco — one
# of the corpora is Italian, and a judge that cannot read it cannot score
# it. The entailment cut-off is provisional, like every threshold here:
# 0.5 is the model's own decision boundary, and the fixture is what would
# move it.
NLI_MODEL = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
NLI_THRESHOLD = 0.5

# Judging a claim is a structured answer, like characterising a region,
# so a malformed one is retried the same way rather than read as a
# verdict. A claim that exhausts the retries is recorded undecided and
# left out of the score, so a judge that fails on a claim cannot move the
# number it exists to report.
MAX_JUDGE_ATTEMPTS = 3

# The cross-encoders are held in memory by name, so measuring twice in a
# process (a test of the whole command, a report) loads the weights once.
_CROSS_ENCODERS: dict[str, object] = {}


def _cpu_float32(encoder):
    """Run a CPU cross-encoder in float32, whatever the checkpoint says.

    `mDeBERTa`'s config declares float16 and the loader honours it. CPU
    float16 is an order of magnitude slower than float32 — 28.8 s against
    2.0 s for one short pair on the 2-core benchmark host — and no more
    accurate, so the weights are raised on CPU. A device that can use
    float16 keeps it.
    """
    if encoder.model.device.type == "cpu":
        encoder.model.float()
    return encoder


def comprehensiveness(mapping: dict, notes: dict[str, str]) -> float:
    """Share of `notes` that a region holds.

    A note has a home when some region lists it as a member. A note left
    standing alone is accounted for but not homed — the map's own
    statement is that nothing refers to it — so it does not count. The
    denominator is the corpus being measured, not the count the map was
    built with, so a map scored against a changed branch is not flattered
    by notes that have since gone.
    """
    if not notes:
        return 0.0
    members = {name for region in mapping["regions"] for name in region["members"]}
    return sum(1 for name in notes if name in members) / len(notes)


def reference_labels(reference: Path | str, names: list[str]) -> np.ndarray:
    """Validate a reference map against a corpus and return its labels.

    A reference is the ground a score is read against; one that
    double-lists a note, names a note the corpus lacks, or omits a corpus
    note would record a decision taken from a broken ground. The same
    check gates the structure sweep, which is why it lives here and both
    callers share it.
    """
    try:
        data = json.loads(Path(reference).read_text())
    except (OSError, json.JSONDecodeError) as err:
        raise ValueError(f"{reference}: not a readable reference map ({err})") from err
    labels: dict[str, str] = {}
    for rid, members in data.get("regions", {}).items():
        for member in members:
            if member in labels:
                raise ValueError(
                    f"{reference}: {member} is listed in two regions "
                    f"({labels[member]} and {rid})"
                )
            labels[member] = rid
    for member in data.get("standalone", []):
        if member in labels:
            raise ValueError(
                f"{reference}: {member} is listed as standalone and in {labels[member]}"
            )
        labels[member] = STANDALONE
    missing = [n for n in names if n not in labels]
    if missing:
        raise ValueError(f"reference has no label for: {', '.join(missing)}")
    extra = [n for n in labels if n not in names]
    if extra:
        raise ValueError(f"reference labels notes the corpus does not hold: {', '.join(extra)}")
    return np.array([labels[n] for n in names])


def map_labels(mapping: dict, names: list[str]) -> np.ndarray:
    """The map's own labels, in corpus order, for the structure score.

    A member takes its region id; a standalone note takes `STANDALONE`;
    a note the map never places takes `UNMAPPED`. Region ids are opaque
    to adjusted Rand index, which is invariant to relabelling, which is
    what lets a rebuilt map with different ids be scored against a fixed
    reference. Every label is a string so the array is one comparable
    type: a mixed array of ids and names cannot be scored at all.
    """
    labels: dict[str, object] = {}
    for region in mapping["regions"]:
        for member in region["members"]:
            labels.setdefault(member, region["id"])
    for member in mapping.get("standalone", []):
        labels.setdefault(member, STANDALONE)
    return np.array([str(labels.get(name, UNMAPPED)) for name in names])


def structure_match(mapping: dict, notes: dict[str, str], reference: Path | str) -> float:
    """Adjusted Rand index of the map's regions against a reference.

    1.0 is a map that partitions the corpus exactly as the reference
    does; 0 is no better than chance; negative is worse than chance. It
    is the only measure here that needs a labelled corpus, which is why
    `product.md` keeps it for the fixture rather than for every run.
    """
    names = list(notes)
    return float(adjusted_rand_score(reference_labels(reference, names), map_labels(mapping, names)))


def characterisation_text(characterisation: dict) -> str:
    """The whole of a characterisation as one string to compare.

    `about`, `topics` and `key_claims` are all the map says about the
    region, so redundancy judges all of it, not just the prose.
    """
    parts = [
        characterisation["about"].strip(),
        "; ".join(characterisation["topics"]),
        "; ".join(characterisation["key_claims"]),
    ]
    return ". ".join(part for part in parts if part)


def cross_encoder(model: str = REDUNDANCY_MODEL):
    """A `compare(a, b)` backed by the cached cross-encoder, symmetric.

    Loaded on first call, not at import, so importing the package still
    pulls no model into the process, and kept for the next call. The two
    orders are both scored and the higher kept because a relevance
    cross-encoder is not symmetric and two characterisations are peers
    (`architecture.md`, Similarity).
    """
    from sentence_transformers import CrossEncoder

    encoder = _CROSS_ENCODERS.get(model)
    if encoder is None:
        encoder = _cpu_float32(CrossEncoder(model))
        _CROSS_ENCODERS[model] = encoder

    def compare(left: str, right: str) -> float:
        forward = float(encoder.predict([(left, right)])[0])
        backward = float(encoder.predict([(right, left)])[0])
        return max(forward, backward)

    return compare


def _groups(same: list[list[bool]]) -> int:
    """Connected components of the 'says the same thing' relation.

    A chain of pairwise judgements is one group: if a says what b says
    and b says what c says, the map says one thing in three regions,
    however the middle phrasing matched.
    """
    n = len(same)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if same[i][j]:
                root_i, root_j = find(i), find(j)
                if root_i != root_j:
                    parent[root_j] = root_i
    return len({find(i) for i in range(n)})


def redundancy(characterisations: dict[int, dict], compare=None,
               threshold: float = REDUNDANCY_THRESHOLD) -> float:
    """Share of characterisations that repeat something another says.

    Two regions say the same thing when `compare` scores their whole
    characterisations at or above `threshold`. Redundancy is then the
    share of regions that are not the first of their group: 0 when every
    region adds something, (n-1)/n when one thing is repeated n ways.
    `compare` defaults to the cached cross-encoder; a test injects a stub
    so the aggregation is what it pins.
    """
    ids = sorted(characterisations)
    n = len(ids)
    if n < 2:
        return 0.0
    if compare is None:
        compare = cross_encoder()
    texts = [characterisation_text(characterisations[i]) for i in ids]
    same = [[False] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            same[i][j] = compare(texts[i], texts[j]) >= threshold
    return (n - _groups(same)) / n


# --- the faithfulness judge -----------------------------------------------

JUDGE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "judge_claim",
        "description": "Say whether the notes support one claim, under the rubric.",
        "parameters": {
            "type": "object",
            "properties": {
                "supported": {
                    "type": "boolean",
                    "description": "true when the notes state or directly entail the claim, "
                                   "false otherwise",
                },
                "reason": {
                    "type": "string",
                    "description": "one short sentence saying why",
                },
            },
            "required": ["supported", "reason"],
        },
    },
}

JUDGE_PROMPT = """Judge one claim against the notes it was drawn from.

A claim is SUPPORTED when the notes state it or directly entail it.
A claim is UNSUPPORTED when it adds a fact, name, number or relation the
notes do not contain, or when it contradicts them. Judge the claim only
against these notes; use no outside knowledge. Answer with the
judge_claim tool.

Claim: """

# Small models answer a boolean oddly however the schema types it; the
# word is read rather than counted a malformed attempt, because it is a
# verdict.
_TRUE = {"true", "yes", "supported"}
_FALSE = {"false", "no", "unsupported"}


class InvalidVerdict(Exception):
    """A judge answer that parsed but is not a verdict."""


class JudgeFailed(Exception):
    """A claim exhausted its judge attempts; the caller records it undecided."""

    def __init__(self, claim: str, attempts: int, reasons: list[str]):
        self.claim = claim
        self.attempts = attempts
        self.reasons = reasons
        super().__init__(f"no verdict for {claim!r} after {attempts} attempts")


def validate_verdict(candidate) -> dict:
    """Return `{supported, reason}`, or raise InvalidVerdict.

    `supported` must be a boolean, or the words a small model uses for
    one. `reason` is free text and may be missing: the verdict is what
    the score reads, and spending a retry on the explanation would move
    the score on a formality.
    """
    if not isinstance(candidate, dict):
        raise InvalidVerdict(f"verdict was {type(candidate).__name__}, not an object")
    supported = candidate.get("supported")
    if isinstance(supported, str):
        word = supported.strip().lower()
        if word in _TRUE:
            supported = True
        elif word in _FALSE:
            supported = False
    if not isinstance(supported, bool):
        raise InvalidVerdict("supported must be a boolean")
    reason = candidate.get("reason")
    return {"supported": supported,
            "reason": reason.strip() if isinstance(reason, str) else ""}


def judge_claim(claim: str, evidence: str, llm=structured, log=None) -> dict:
    """Judge one claim against its region's notes, retrying malformed answers.

    `llm` is the model interface: `(prompt, schema) -> dict`. Only a
    malformed answer counts against the cap, exactly as in
    `characterise.characterise_region`; a bug the model raises is not
    retried.
    """
    prompt = JUDGE_PROMPT + claim + "\n\nNotes:\n\n" + evidence + "\n"
    reasons = []
    for attempt in range(1, MAX_JUDGE_ATTEMPTS + 1):
        try:
            return validate_verdict(llm(prompt, JUDGE_SCHEMA))
        except (ModelError, InvalidVerdict) as err:
            reasons.append(f"attempt {attempt}/{MAX_JUDGE_ATTEMPTS}: {err}")
            if log is not None:
                log(f"  judge attempt {attempt}/{MAX_JUDGE_ATTEMPTS} rejected — {err}")
    raise JudgeFailed(claim, MAX_JUDGE_ATTEMPTS, reasons)


def region_evidence(region: dict, notes: dict[str, str]) -> str:
    """Every note in a region, in the order the map lists them.

    The claim was drawn from the representatives, but it is a claim
    about the region, so it is checked against the region's members —
    all the notes that would have to bear it out (`product.md`, what it
    produces).
    """
    return "\n\n".join(notes[name].strip() for name in region["members"] if name in notes)


# --- the NLI judge --------------------------------------------------------


def entailment_index(config) -> int:
    """Which output the model's entailment label is.

    The label order is the model's, not a convention, so `id2label` is
    read rather than assumed: a head that orders its three labels
    differently is still scored on the one it calls entailment.
    """
    labels = getattr(config, "id2label", None) or {}
    for index, label in labels.items():
        if "entail" in str(label).lower():
            return int(index)
    raise ValueError(f"NLI model has no entailment label among {labels!r}")


def probabilities(row) -> np.ndarray:
    """A model row as three probabilities, whether it came as logits or not.

    Cross-encoders differ in whether they apply a softmax, so the row is
    read as probabilities only when it already reads as one; otherwise the
    softmax is applied here. That leaves the argmax alone and makes the
    threshold mean the same thing either way.
    """
    values = np.asarray(row, dtype=float)
    if bool((values >= 0).all()) and abs(float(values.sum()) - 1.0) < 1e-3:
        return values
    shifted = np.exp(values - values.max())
    return shifted / shifted.sum()


def nli_encoder(model: str = NLI_MODEL):
    """The cached NLI cross-encoder, loaded on first use like the others."""
    from sentence_transformers import CrossEncoder

    encoder = _CROSS_ENCODERS.get(model)
    if encoder is None:
        encoder = _cpu_float32(CrossEncoder(model))
        _CROSS_ENCODERS[model] = encoder
    return encoder


_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _sentences(evidence: str) -> list[str]:
    """The evidence as sentences, with hard-wrapped lines rejoined.

    The notes are prose wrapped at a fixed width, so a newline is not a
    sentence boundary: whitespace is collapsed before the split. The split
    is on terminal punctuation followed by whitespace, which leaves
    decimals (4.6) and temperatures (18-22°C) whole.
    """
    text = re.sub(r"\s+", " ", evidence).strip()
    return [part for part in _SENTENCE_END.split(text) if part]


def _windows(tokenizer, text: str, width: int) -> list[str]:
    """`text` as contiguous token windows no longer than `width`."""
    ids = tokenizer(text, add_special_tokens=False)["input_ids"]
    if len(ids) <= width:
        return [text]
    return [tokenizer.decode(ids[start:start + width], skip_special_tokens=True)
            for start in range(0, len(ids), width)]


def premises(tokenizer, evidence: str, width: int) -> list[str]:
    """The evidence as short premises no longer than `width` tokens.

    An NLI cross-encoder is trained on sentence pairs, and a region's
    notes are a long, multi-topic premise on which entailment drifts to
    neutral: on the in-domain fixture a verbatim claim scores 0.97 against
    the sentence that carries it and 0.06 against the note it sits in
    (`benchmarks/measurement.md`). So the evidence is cut into sentences
    and adjacent pairs — a pair keeps an anaphor and its antecedent
    together — and the judge takes the best. A sentence longer than the
    model's input is still split by tokens, so no note is truncated.
    """
    sentences = _sentences(evidence)
    if not sentences:
        return [evidence]
    spans = []
    for index, sentence in enumerate(sentences):
        spans.append(sentence)
        if index + 1 < len(sentences):
            spans.append(f"{sentence} {sentences[index + 1]}")
    return [window for span in spans for window in _windows(tokenizer, span, width)]


def nli_judge(model: str = NLI_MODEL, threshold: float = NLI_THRESHOLD, encoder=None):
    """A `(claim, evidence) -> verdict` judge backed by an NLI cross-encoder.

    Decoupled from the model under test and effectively deterministic, so
    it is the judge the model decision has been waiting on. The premise is
    the region's evidence, cut into sentences and adjacent pairs so the
    model sees the short premises it was trained on; a span longer than
    the model's input is split by tokens. The claim is supported when the
    highest entailment reaches `threshold`. An entailment model answers
    the rubric's two clauses at once: not-entailment is unsupported, and a
    contradiction is one way to fail it.

    `encoder` is injected so the rule is pinned on a stub; the real model
    is loaded, and cached, only when none is given.
    """
    if encoder is None:
        encoder = nli_encoder(model)
    config = encoder.model.config
    index = entailment_index(config)
    tokenizer = encoder.tokenizer
    limit = int(getattr(config, "max_position_embeddings", 0)
                or tokenizer.model_max_length)

    def judge(claim: str, evidence: str) -> dict:
        room = limit - len(tokenizer(claim, add_special_tokens=False)["input_ids"]) - 3
        rows = encoder.predict([(premise, claim)
                                for premise in premises(tokenizer, evidence, max(room, 1))])
        best = max(float(probabilities(row)[index]) for row in rows)
        return {"supported": best >= threshold,
                "reason": f"entailment {best:.2f} (threshold {threshold:.2f})"}

    return judge


def faithfulness(mapping: dict, characterisations: dict[int, dict], notes: dict[str, str],
                 llm=structured, judge=None, progress=None, log=None) -> dict:
    """Judge every `key_claim` against its region's notes.

    Returns the share supported and the verdicts behind it. `judge`, when
    given, is a decoupled `(claim, evidence) -> verdict` judge that
    replaces the model-backed `llm`, so the number no longer reads a
    model's verdict on its own prose. A claim the judge could not answer
    is recorded undecided and excluded from the share, so a failing judge
    cannot move the number it reports; the undecided count is part of the
    result, because a judge's disagreement is the honest finding
    (`architecture.md`, Measurements). A region named by a
    characterisation but absent from the map is skipped rather than
    guessed at.
    """
    regions = {region["id"]: region for region in mapping["regions"]}
    claims = [
        (region_id, claim, region_evidence(regions[region_id], notes))
        for region_id in sorted(characterisations)
        if region_id in regions
        for claim in characterisations[region_id]["key_claims"]
    ]
    total = len(claims)
    verdicts = []
    for position, (region_id, claim, evidence) in enumerate(claims, start=1):
        if progress is not None:
            progress("claim", position, total)
        try:
            verdict = (judge(claim, evidence) if judge is not None
                       else judge_claim(claim, evidence, llm, log))
        except JudgeFailed as err:
            verdict = {"supported": None, "reason": str(err)}
        if log is not None:
            shown = {True: "supported", False: "unsupported", None: "undecided"}[verdict["supported"]]
            log(f"  r{region_id}: {shown} — {claim[:80]}")
        verdicts.append({"region": region_id, "claim": claim, **verdict})
    supported = sum(1 for v in verdicts if v["supported"] is True)
    unsupported = sum(1 for v in verdicts if v["supported"] is False)
    undecided = sum(1 for v in verdicts if v["supported"] is None)
    judged = supported + unsupported
    return {
        "score": (supported / judged) if judged else None,
        "supported": supported,
        "unsupported": unsupported,
        "undecided": undecided,
        "total": total,
        "verdicts": verdicts,
    }


def measure(mapping: dict, characterisations: dict[int, dict], notes: dict[str, str],
            reference: Path | str | None = None, llm=structured, judge=None, compare=None,
            progress=None, log=None) -> dict:
    """All four numbers for one candidate map, and what they rest on.

    `comprehensiveness`, `redundancy` and `faithfulness` are always
    produced; `structure_match` is `None` without a reference, because
    nothing else reproduces it. Faithfulness is `None` when no claim can
    be judged. `faithfulness_detail` carries the verdicts, so the number
    is read beside the disagreement it is made of. `judge`, when given,
    is the decoupled faithfulness judge that replaces `llm`.
    """
    faith = faithfulness(mapping, characterisations, notes, llm=llm, judge=judge,
                         progress=progress, log=log)
    return {
        "notes": len(notes),
        "regions": len(mapping["regions"]),
        "standalone": len(mapping.get("standalone", [])),
        "comprehensiveness": comprehensiveness(mapping, notes),
        "redundancy": redundancy(characterisations, compare),
        "faithfulness": faith["score"],
        "faithfulness_detail": faith,
        "structure_match": (
            structure_match(mapping, notes, reference) if reference is not None else None
        ),
        "reference": str(reference) if reference is not None else None,
    }
