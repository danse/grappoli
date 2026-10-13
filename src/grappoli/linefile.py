"""The append-only line files both model-driven stages write.

`characterisations` and `relations` are line files: one JSON record per
line, appended and flushed as each item completes, resumed by reading
back what is there. A run interrupted mid-write can leave a torn last
line, so the fragment is dropped before anything is appended — appending
to it would glue the next record onto the fragment and corrupt both
(`architecture.md`, Progress and logging).
"""

import json
from pathlib import Path


def drop_torn_tail(path: Path) -> None:
    """Truncate a last line left incomplete by an interrupt.

    Only the incomplete tail goes: every line that ends in a newline is
    a finished record and is left untouched.
    """
    path = Path(path)
    if not path.exists():
        return
    data = path.read_bytes()
    if data and not data.endswith(b"\n"):
        path.write_bytes(data[: data.rfind(b"\n") + 1])


def read_records(path: Path) -> list[dict]:
    """The well-formed JSON objects in the file, in order.

    A blank line, a torn fragment or any non-object line is skipped
    rather than allowed to abort the run: the item it was meant to hold
    then reads as missing and is regenerated.
    """
    path = Path(path)
    if not path.exists():
        return []
    records = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def append(path: Path, record: dict) -> None:
    """Append one record as a line, flushed, creating the file if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(record) + "\n")
        handle.flush()
