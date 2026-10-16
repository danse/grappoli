"""The source and the docs keep their citations to `benchmarks/` true.

Every default in the pipeline was decided by a measurement, and the
reason for it is recorded in `benchmarks/` — cited by path from the
docstring it justifies, from `architecture.md`, and from the tests. There
are about three dozen such citations, and most are a docstring's only
evidence: nothing else in the file would notice if the record they name
were renamed or its section were rewritten. Since the records are edited
in place when a new run lands, that is the way a citation is most likely
to be orphaned, silently.

Two kinds of citation are pinned, both scanned from the repo's own source
and prose so a new one is covered without being listed here:

* a record — `benchmarks/<file>.md` — exists;
* a section — `benchmarks/<file>.md`, "Title" — is a heading in it.

The last test keeps the scan from passing vacuously: a pattern that
matched nothing would make the other two true for the empty set.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# A record is cited as `benchmarks/<file>.md`. The lookbehind keeps a
# reference from matching inside a longer path such as `other/…`.
RECORD = re.compile(r"(?<![\w./-])benchmarks/([A-Za-z0-9._/-]+\.md)")
# A section is cited as `benchmarks/<file>.md`, "Title"; the title may
# wrap across lines, so matching is done against whitespace-collapsed
# text.
SECTION = re.compile(r'`benchmarks/([A-Za-z0-9._/-]+\.md)`\s*,\s*"([^"]+)"')
HEADING = re.compile(r"^#{1,6}\s+(.*\S)\s*$", re.MULTILINE)


def _prose():
    """Every file that may cite a record: the docs, source, and tests."""
    files = sorted(ROOT.glob("*.md")) + sorted((ROOT / "benchmarks").rglob("*.md"))
    for folder in ("src", "scripts", "tests"):
        files += sorted(
            path for path in (ROOT / folder).rglob("*")
            if path.suffix in (".py", ".md") and "__pycache__" not in path.parts
        )
    return files


def _records():
    return [(path, match.group(1))
            for path in _prose()
            for match in RECORD.finditer(path.read_text())]


def _sections():
    found = []
    for path in _prose():
        text = re.sub(r"\s+", " ", path.read_text())
        found += [(path, *match.groups()) for match in SECTION.finditer(text)]
    return found


def test_every_cited_record_exists():
    missing = [f"{path.relative_to(ROOT)} cites benchmarks/{name}"
               for path, name in _records()
               if not (ROOT / "benchmarks" / name).is_file()]
    assert not missing, "a citation points at a record that is not there:\n" + "\n".join(missing)


def test_every_cited_section_is_a_heading():
    problems = []
    for path, name, title in _sections():
        target = ROOT / "benchmarks" / name
        if not target.is_file():
            continue  # the missing record is the other test's failure
        headings = {re.sub(r"\s+", " ", heading).strip()
                    for heading in HEADING.findall(target.read_text())}
        if re.sub(r"\s+", " ", title).strip() not in headings:
            problems.append(f'{path.relative_to(ROOT)} cites benchmarks/{name}, "{title}"')
    assert not problems, "a citation names a section that is not there:\n" + "\n".join(problems)


def test_the_scan_finds_the_citations():
    """A scan that finds nothing must fail, not pass over the empty set."""
    names = {name for _, name in _records()}
    assert {"structure.md", "structure-heterogeneous.md", "characterisation.md",
            "relations.md", "throughput.md", "measurement.md"} <= names
    assert any(title == "Against deciding without a reference"
               for _, _, title in _sections())
