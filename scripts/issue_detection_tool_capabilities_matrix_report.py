#!/usr/bin/env python3
"""Generate the issue-detection-tool-capabilities-matrix report tables + notes.

The Markdown doc (docs/issue-detection-tool-capabilities-matrix.md) is a *build
artifact* for everything between the generated-region markers; the source of
truth is data/issue-detection-tool-capabilities-matrix.json.
Edit the JSON, run this script, and the doc's scale table, the per-language
summary table, the per-tool breakdown table, and the per-item notes are rewritten
from the data. The hand-written prose outside the markers is left untouched.

Detection codes (per tool, in the JSON `coverage` map):
    complete / partial / none / na   → rendered ✓ / ∙ / (blank) / n/a

A tool omitted from an item's `coverage` map defaults to `none` (blank); a tool
that genuinely doesn't apply to a language must be listed explicitly as `na`.

Per-item notes embed source references as `{source-key}` placeholders that
resolve to Markdown links `[label](url)` from the JSON `sources` map.

Markers in the doc (must exist, in this order):
    <!-- BEGIN GENERATED: scale -->            ... <!-- END GENERATED: scale -->
    <!-- BEGIN GENERATED: summary-table -->    ... <!-- END GENERATED: summary-table -->
    <!-- BEGIN GENERATED: tool-table -->       ... <!-- END GENERATED: tool-table -->
    <!-- BEGIN GENERATED: notes -->            ... <!-- END GENERATED: notes -->

Usage:
    scripts/issue_detection_tool_capabilities_matrix_report.py          # rewrite doc in place
    scripts/issue_detection_tool_capabilities_matrix_report.py --check   # exit 1 if doc is stale
    scripts/issue_detection_tool_capabilities_matrix_report.py --doc PATH --data PATH  # override
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DATA = os.path.join(ROOT, "data", "issue-detection-tool-capabilities-matrix.json")
DEFAULT_DOC = os.path.join(ROOT, "docs", "issue-detection-tool-capabilities-matrix.md")

# Try to reuse the repo's display-width-aware table formatter so the generated
# tables are emitted already aligned. Fall back to a plain join if unavailable.
try:
    sys.path.insert(0, HERE)
    from importlib import import_module

    _fmt = import_module("fmt-md-tables")
    _format_document = _fmt.format_document
except Exception:  # pragma: no cover - formatter is optional
    _format_document = None


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def icon_for(data: dict, code: str) -> str:
    for s in data["scale"]:
        if s["code"] == code:
            return s["icon"]
    raise KeyError(f"unknown coverage code: {code!r}")


def resolve_sources(text: str, sources: dict) -> str:
    """Replace `{source-key}` placeholders with Markdown links `[label](url)`."""
    def repl(m: re.Match) -> str:
        key = m.group(1)
        if key not in sources:
            raise KeyError(f"unknown source key in note: {key!r}")
        s = sources[key]
        return f"[`{s['label']}`]({s['url']})"

    return re.sub(r"\{([a-z0-9-]+)\}", repl, text)


def render_table(rows: list[list[str]]) -> str:
    """rows[0] is the header, rest are body. Delimiter is inserted automatically."""
    ncols = len(rows[0])
    delim = ["---"] * ncols
    out = [rows[0], delim] + rows[1:]
    lines = ["| " + " | ".join(r) + " |" for r in out]
    return "\n".join(lines)


def render_scale(data: dict) -> str:
    rows = [["Cell", "Ordinal", "Meaning"]]
    for s in data["scale"]:
        if s["code"] == "none":
            cell = "(blank)"
        elif s["code"] == "na":
            continue  # the n/a meaning is documented in the table note, not the scale
        else:
            cell = s["icon"]
        rows.append([cell, s["ordinal"], s["meaning"]])
    return render_table(rows)


def cell(data: dict, item: dict, tool_id: str) -> str:
    code = item["coverage"].get(tool_id, "none")
    return icon_for(data, code)


def lang_summary_code(data: dict, item: dict, lang: dict) -> str:
    """Collapse a language's tools to the best-case (most-covered) code for the
    per-language summary, matching the original hand-built table semantics."""
    # idk ranks below every determined code: a single researched cell wins, but
    # an all-idk (unresearched) row collapses to idk rather than a false "none".
    rank = {"complete": 4, "partial": 3, "na": 2, "none": 1, "idk": 0}
    best = "idk"
    for tool_id in lang["tools"]:
        c = item["coverage"].get(tool_id, "none")
        if rank[c] > rank[best]:
            best = c
    return best


def render_summary_table(data: dict) -> str:
    langs = data["languages"]
    header = ["Item", "Group"] + [l["abbr"] for l in langs]
    rows = [header]
    fams = {f["id"]: f for f in data["families"]}
    cur_family = None
    for item in data["items"]:
        if item["family"] != cur_family:
            cur_family = item["family"]
            f = fams[cur_family]
            rows.append([f"{f['id']} — {f['title']}"] + [""] * (len(header) - 1))
        # Group cell: D-groups if researched; "ref" for cross-language
        # reference-only items; blank for not-yet-researched (idk) rows.
        if item.get("groups"):
            group = " · ".join(item["groups"])
        elif item.get("reference_only"):
            group = "ref"
        else:
            group = ""
        name = f"{item['id']} {item['short']}"
        cells = [icon_for(data, lang_summary_code(data, item, l)) for l in langs]
        rows.append([name, group] + cells)
    return render_table(rows)


def render_tool_table(data: dict) -> str:
    langs = data["languages"]
    tools = data["tools"]
    # Flat ordered list of (lang, tool_id) pairs across all languages.
    pairs = [(l, t) for l in langs for t in l["tools"]]
    top = ["Item"] + [l["abbr"] for (l, _t) in pairs]
    sub = [""] + [tools[t]["name"] for (_l, t) in pairs]
    rows = [top, sub]
    for item in data["items"]:
        name = f"{item['id']} {item['short']}"
        cells = [cell(data, item, t) for (_l, t) in pairs]
        rows.append([name] + cells)
    # The second header row (tool names) must live in the BODY of the markdown
    # table, since GFM has only one header row. render_table puts the delimiter
    # after rows[0]; we instead want delimiter after the *tool* row so both the
    # language row and the tool row render as headers. Emit manually:
    ncols = len(top)
    delim = ["---"] * ncols
    out = [top, delim, sub] + rows[2:]
    lines = ["| " + " | ".join(r) + " |" for r in out]
    return "\n".join(lines)


def _research_source_key(tool_id: str, item_id: str) -> str:
    """Mirror research_tool_capabilities.source_key so we can find the rule link that
    research recorded for a given (tool, item) cell."""
    return f"{tool_id}-{item_id}".replace(".", "_").lower()


def compose_research_note(data: dict, item: dict) -> str:
    """Build a verdict-aware note from an item's coverage map.

    Groups tools by what they actually do — fully detect (complete), partially detect
    (partial), or can't (na) — and attaches the documented rule link where research
    recorded one. This keeps the note consistent with the table's ✓/∙ cells instead of
    implying every listed tool fully covers the issue.
    """
    tools = data["tools"]
    sources = data["sources"]
    cov = item.get("coverage", {})

    def tool_label(tool_id: str) -> str:
        name = tools.get(tool_id, {}).get("name", tool_id)
        key = _research_source_key(tool_id, item["id"])
        if key in sources:
            return f"{name} ([`{sources[key]['label']}`]({sources[key]['url']}))"
        return name

    complete = [tool_label(t) for t, v in cov.items() if v == "complete"]
    partial = [tool_label(t) for t, v in cov.items() if v == "partial"]

    parts = []
    if complete:
        parts.append(f"fully detected by {', '.join(complete)}")
    if partial:
        parts.append(f"partially detected by {', '.join(partial)}")
    if not parts:
        # Some cells determined, but none complete/partial → no off-the-shelf detector.
        if any(v in ("none", "na") for v in cov.values()):
            parts.append("no off-the-shelf detector in the surveyed tools")
    return "; ".join(parts)


def render_notes(data: dict) -> str:
    out: list[str] = []
    for item in data["items"]:
        if "note" in item:
            # Hand-authored prose note with inline {source-key} placeholders.
            note = resolve_sources(item["note"], data["sources"])
            out.append(f"- **{item['id']} {item['name']}** — {note}")
        elif item.get("note_sources"):
            # Auto-composed from structured research, stating the coverage level.
            note = compose_research_note(data, item)
            if note:
                out.append(f"- **{item['id']} {item['name']}** — {note}")
    return "\n".join(out)


def render_tool_capability_difference_notes(data: dict) -> str:
    sources = data["sources"]
    return "\n".join(
        f"- {resolve_sources(n, sources)}"
        for n in data.get("tool_capability_difference_notes", [])
    )


MARKERS = {
    "scale": render_scale,
    "summary-table": render_summary_table,
    "tool-table": render_tool_table,
    "tool-capability-difference-notes": render_tool_capability_difference_notes,
    "notes": render_notes,
}


def inject(doc: str, data: dict) -> str:
    for key, renderer in MARKERS.items():
        begin = f"<!-- BEGIN GENERATED: {key} -->"
        end = f"<!-- END GENERATED: {key} -->"
        if begin not in doc or end not in doc:
            raise SystemExit(f"missing markers for region {key!r}: expected {begin} ... {end}")
        body = renderer(data)
        pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
        doc = pattern.sub(begin + "\n" + body + "\n" + end, doc, count=1)
    if _format_document is not None:
        doc = _format_document(doc)
    return doc


def main(argv: list[str]) -> int:
    args = argv[1:]
    check = "--check" in args
    doc_path = DEFAULT_DOC
    data_path = DEFAULT_DATA
    if "--doc" in args:
        doc_path = args[args.index("--doc") + 1]
    if "--data" in args:
        data_path = args[args.index("--data") + 1]

    data = load(data_path)
    with open(doc_path, "r", encoding="utf-8") as f:
        src = f.read()
    generated = inject(src, data)

    if generated == src:
        if not check:
            print(f"unchanged: {doc_path}")
        return 0
    if check:
        print(f"stale: {doc_path} is out of date with {data_path} — run scripts/issue_detection_tool_capabilities_matrix_report.py")
        return 1
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(generated)
    print(f"generated: {doc_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
