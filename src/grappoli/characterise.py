"""Characterise one region at a time.

The representatives of a region go to the model, which returns `about`,
`topics` and `key_claims`; the answer is validated and appended to a
line file. The step never holds the corpus in view: it is handed the
representatives, and no other note reaches the prompt (`product.md`,
Approach).

A malformed answer is retried, up to `MAX_ATTEMPTS` total. A region that
exhausts them is logged with what it cost, skipped, and left out of the
file, so the run can finish and the next run retries exactly it
(`architecture.md`, Model interface). Completed regions are read back
from the line file first and never regenerated, which is why the file is
appended a line at a time rather than rewritten (`architecture.md`,
Progress and logging).
"""

import time
from pathlib import Path

from . import linefile
from .model import ModelError, structured

MAX_ATTEMPTS = 3

# throughput.md: one characterisation is ≈450 prompt tokens and ≈150
# answer tokens at ≈2.3 tok/s generation — about four minutes. The ETA
# starts here and is replaced by this run's own measurements once a
# region has finished.
SECONDS_PER_REGION = 240.0

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "characterise_region",
        "description": "Give one region of notes its about, topics and key claims.",
        "parameters": {
            "type": "object",
            "properties": {
                "about": {
                    "type": "string",
                    "description": "one sentence saying what the region is about, at most 25 words",
                },
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5,
                    "description": "three to five short phrases the region covers",
                },
                "key_claims": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5,
                    "description": "up to five claims, one clause each in your own words, "
                                   "not quoted from the notes",
                },
            },
            "required": ["about", "topics", "key_claims"],
        },
    },
}

PROMPT_HEADER = """You are mapping a corpus of notes. Characterise the region below.

Base every claim on the notes; do not add anything you cannot point to.
Keep it short: one sentence for "about", three to five short phrases for
"topics", and at most five one-clause "key_claims" in your own words —
do not quote or copy the notes. Use the characterise_region tool.

Notes in this region:

"""


class InvalidCharacterisation(Exception):
    """An answer that parsed but is not a characterisation."""


class CharacterisationFailed(Exception):
    """A region exhausted its attempts; the caller logs and skips it."""

    def __init__(self, region_id: int, attempts: int, reasons: list[str]):
        self.region_id = region_id
        self.attempts = attempts
        self.reasons = reasons
        super().__init__(
            f"region {region_id}: no valid characterisation after {attempts} attempts"
        )


def build_prompt(representatives: list[str], notes: dict[str, str]) -> str:
    """The prompt for one region, from its representatives alone."""
    blocks = [notes[name].strip() for name in representatives]
    return PROMPT_HEADER + "\n\n".join(blocks) + "\n"


def validate(candidate) -> dict:
    """Return the characterisation, or raise InvalidCharacterisation.

    Structural only: the required keys, a non-empty `about`, and
    non-empty lists of non-empty strings for `topics` and `key_claims`.
    There is deliberately no count bound — the prompt asks for three to
    five topics, but a sixth is accepted rather than spending another
    four-minute retry on it.
    """
    if not isinstance(candidate, dict):
        raise InvalidCharacterisation(f"answer was {type(candidate).__name__}, not an object")
    about = candidate.get("about")
    if not isinstance(about, str) or not about.strip():
        raise InvalidCharacterisation("about must be a non-empty string")
    cleaned = {"about": about.strip()}
    for key in ("topics", "key_claims"):
        value = candidate.get(key)
        if not isinstance(value, list) or not value:
            raise InvalidCharacterisation(f"{key} must be a non-empty list")
        items = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise InvalidCharacterisation(f"{key} holds a non-string or empty item")
            items.append(item.strip())
        cleaned[key] = items
    return cleaned


def characterise_region(region_id: int, representatives: list[str], notes: dict[str, str],
                        llm=structured, log=None) -> dict:
    """Characterise one region, retrying up to MAX_ATTEMPTS times.

    `llm` is the model interface: `(prompt, schema) -> dict`. Anything
    it raises that is not ModelError is a bug and is not retried; only a
    malformed answer counts against the cap.
    """
    prompt = build_prompt(representatives, notes)
    reasons = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return validate(llm(prompt, TOOL_SCHEMA))
        except (ModelError, InvalidCharacterisation) as err:
            reasons.append(f"attempt {attempt}/{MAX_ATTEMPTS}: {err}")
            if log is not None:
                log(f"region {region_id}: attempt {attempt}/{MAX_ATTEMPTS} rejected — {err}")
    raise CharacterisationFailed(region_id, MAX_ATTEMPTS, reasons)


def read_characterisations(path: Path) -> dict[int, dict]:
    """The completed regions, keyed by id, from the append-only file.

    A line can be torn by a hard interrupt mid-write, since the file is
    appended to and flushed rather than rewritten atomically. Such a
    line is skipped rather than allowed to abort the run: the region it
    was meant to hold is simply not marked done, so it is regenerated
    (architecture.md, Progress and logging).
    """
    done = {}
    for record in linefile.read_records(path):
        region_id = record.get("region")
        if isinstance(region_id, int):
            done[region_id] = record
    return done


def characterise_regions(mapping: dict, notes: dict[str, str], path: Path,
                         llm=structured, clock=time.monotonic,
                         progress=None, log=None) -> list[int]:
    """Characterise every region not already on disk; return failed ids.

    One line per region is appended as it completes, and flushed, so an
    interrupt leaves the finished regions on disk and the next run
    resumes at the first missing one. A region that exhausts its
    attempts is logged with the wall-clock seconds it burned, skipped,
    and left out of the file, so the run continues past it and the next
    run retries only it.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    linefile.drop_torn_tail(path)
    done = read_characterisations(path)
    regions = mapping["regions"]
    total = len(regions)
    failed: list[int] = []
    durations: list[float] = []

    for position, region in enumerate(regions, start=1):
        region_id = region["id"]
        remaining = sum(1 for r in regions[position - 1:] if r["id"] not in done)
        per_region = (sum(durations) / len(durations)) if durations else SECONDS_PER_REGION
        if progress is not None:
            progress("region", position, total, per_region * remaining)
        if region_id in done:
            continue

        started = clock()
        try:
            record = characterise_region(region_id, region["representatives"], notes, llm, log)
        except CharacterisationFailed as err:
            seconds = clock() - started
            failed.append(region_id)
            if log is not None:
                log(f"region {region_id}: gave up after {err.attempts} attempts "
                    f"({seconds:.0f}s) — skipping; next run retries only this")
            continue
        seconds = clock() - started
        durations.append(seconds)
        linefile.append(path, {"region": region_id, **record})

    return failed
