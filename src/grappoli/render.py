"""Render the map as the page a reader sees.

This is the pipeline's last arrow: the map, the characterisations and the
relations go in, one page comes out. It makes no model call, reads and
writes nothing, and depends on nothing else — so the same three working
files always give the same page, and the page is the corpus's rather than
the model's. The words are the model's and are carried verbatim; deciding
which words appear, and where, is this module's whole job
(`architecture.md`, The document).

The content contract is fixed: every region; its characterisation where
one exists; every relation, once, between characterised regions; and the
notes that stand alone. A region with no characterisation, or a touching
pair with no relation, is a gap on the page — `no characterisation`, `(no
relation recorded)` — rather than something omitted or invented, so a
partial build reads as partial.

`render` is given the three inputs already read: the mapping `build_map`
returns, the `characterisations` keyed by region id, and the `relations`
keyed by their unordered pair, both exactly as `read_characterisations`
and `read_relations` return them.
"""


def render(mapping: dict, characterisations: dict, relations: dict) -> str:
    """The page for one map, as a string without a trailing newline.

    Pure and deterministic: it reads no file, calls no model and asks no
    clock, so `grappoli show` is a formatting of what a `grappoli read`
    already left on disk.
    """
    known = {(min(a, b), max(a, b)): record for (a, b), record in relations.items()}
    blocks = [_header(mapping)]
    for region in mapping.get("regions", []):
        blocks.append(_region(region, characterisations.get(region.get("id"))))
    pairs = _relation_pairs(mapping, characterisations, known)
    if pairs:
        blocks.append(_relations_section(pairs, known))
    standalone = mapping.get("standalone", [])
    if standalone:
        blocks.append(_standalone_section(standalone))
    return "\n\n".join(blocks)


def _header(mapping: dict) -> str:
    """What the page is: how much corpus, and the rule that mapped it.

    The counts come from the map's own structure rather than its `notes`
    field, so the header is right for a map assembled by hand as well as
    one `build_map` wrote.
    """
    regions = mapping.get("regions", [])
    standalone = mapping.get("standalone", [])
    notes = sum(len(region.get("members", [])) for region in regions) + len(standalone)
    title = (f"grappoli — {notes} notes, {len(regions)} regions, "
             f"{len(standalone)} standalone")
    rule = _rule(mapping)
    return f"{title}\n{rule}" if rule else title


def _rule(mapping: dict) -> str:
    """The map's rule parameters, so the page says which rule produced it.

    Only the parameters the map actually carries are named, so a map
    without them still renders.
    """
    parts = []
    if mapping.get("similarity"):
        parts.append(str(mapping["similarity"]))
    if "k" in mapping:
        parts.append(f"k={mapping['k']}")
    for flag in ("mutual", "weighted"):
        if flag in mapping:
            parts.append(f"{flag}={str(bool(mapping[flag])).lower()}")
    if "resolution" in mapping:
        parts.append(f"resolution={mapping['resolution']}")
    return "rule: " + ", ".join(parts) if parts else ""


def _region(region: dict, characterisation: dict | None) -> str:
    """One region: its characterisation where there is one, then its notes.

    The representatives are named only when they are a proper subset of
    the members — for a region small enough that every note was sent to
    the model, the two lines would say the same thing twice.
    """
    lines = [f"Region {region.get('id')}"]
    if characterisation:
        lines.append(f"  about: {characterisation['about']}")
        lines.append(f"  topics: {', '.join(characterisation['topics'])}")
        lines.append("  claims:")
        lines.extend(f"    - {claim}" for claim in characterisation["key_claims"])
    else:
        lines.append("  no characterisation")
    members = region.get("members", [])
    if members:
        lines.append(f"  notes: {', '.join(members)}")
    representatives = region.get("representatives", [])
    if representatives and set(representatives) != set(members):
        lines.append(f"  representatives: {', '.join(representatives)}")
    return "\n".join(lines)


def _relation_pairs(mapping: dict, characterisations: dict, known: dict) -> list:
    """The pairs the relation section lists, once each, low id first.

    A pair is here if the map says the regions touch and both are
    characterised (a relation can only be written between
    characterisations), or if a relation for it is already on disk. The
    two together mean every stored relation is shown and every touching
    pair that should have one is, whether or not it does.
    """
    pairs = set(known)
    for edge in mapping.get("edges", []):
        source, target = edge.get("source"), edge.get("target")
        if source in characterisations and target in characterisations:
            pairs.add((min(source, target), max(source, target)))
    return sorted(pairs)


def _relations_section(pairs: list, known: dict) -> str:
    """How the regions touch: one line per pair, the statement or a gap."""
    lines = ["Relations"]
    for source, target in pairs:
        record = known.get((source, target))
        statement = record["statement"] if record else "(no relation recorded)"
        lines.append(f"  {source} ↔ {target} — {statement}")
    return "\n".join(lines)


def _standalone_section(notes: list) -> str:
    """The notes nothing refers to: the second figure a reader acts on."""
    return "Standalone\n" + "\n".join(f"  - {note}" for note in notes)
