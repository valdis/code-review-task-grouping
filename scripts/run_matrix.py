#!/usr/bin/env python3
"""Phase-1 run matrix: solo-vs-in-group code-review runs over a fixed case.

Implements the run matrix of `docs/phase-1-design.md` §3 and `docs/methodology.md`
§1/§2/§6. For a built case (`corpus/cases/<id>/{manifest.json,diff.patch}`) it runs the
frozen code-review prompt against the case's fixed diff under two kinds of condition:

    Solo      checklist = {i}   for each planted item i in the case
    In-group  checklist = G     for each Phase-1 group G whose items overlap the case

Only the CHECKLIST SUBSET differs between conditions; the diff, preamble, output schema,
model and (nominal) temperature are held constant — the confound control of
`methodology.md` §2. Each condition is run N≥3 times (`methodology.md` §6) because LLM
reviews are nondeterministic; recall/detection are later estimated as frequencies over
those runs by the scorer (`scripts/score_matrix.py`, TODO #9).

This driver only PRODUCES RAW RUNS — it does not score them. Each run's model output is a
list of reported issues (File&line/Criterion/Severity/Confidence/Description/Suggestion,
per the frozen preamble). Runs are written verbatim to
`corpus/cases/<id>/results/runs/<condition>__run<k>.json` for the scorer to consume.

Invocation mirrors `scripts/research_tool_capabilities.py`: headless `claude -p` with a
JSON output schema, streaming stream-json, reading the `structured_output` field of the
final result event. Like that script it MUST run from a plain terminal — a nested
`claude` inside an active Claude Code session gets killed (exit 137), so it refuses when
CLAUDECODE=1 unless --dry-run/--print-prompt.

NOTE on temperature: the `claude` CLI exposes no --temperature flag, so "temp 0"
(`methodology.md` §6) cannot be pinned here; runs use the CLI default. This is exactly why
the methodology mandates N≥3 and reports mean±spread rather than trusting a single run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHECKLIST = REPO_ROOT / "references" / "checklist.md"
DEFAULT_GROUPS = REPO_ROOT / "groups.md"
DEFAULT_MODEL = "sonnet"
DEFAULT_N = 3

# ── Output schema: one review = a list of reported issues ─────────────────────────────
# Matches the frozen preamble's report fields (references/prior-experiment/prompts/preamble.md).
RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["issues"],
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "file",
                    "lines",
                    "criterion",
                    "severity",
                    "confidence",
                    "description",
                    "suggestion",
                ],
                "properties": {
                    "file": {"type": "string"},
                    "lines": {"type": "string"},
                    "criterion": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "info"],
                    },
                    "confidence": {"type": "integer", "minimum": 1, "maximum": 10},
                    "description": {"type": "string"},
                    "suggestion": {"type": "string"},
                },
            },
        }
    },
}


class SessionLimitError(RuntimeError):
    """Raised on a 429 session/rate limit so the whole run stops cleanly."""


# ── Checklist item text ───────────────────────────────────────────────────────────────
# Lines look like:  "- 17.4.4a Fallback value semantics: when using ..."
_ITEM_RE = re.compile(r"^- ([0-9]+(?:\.[0-9]+)*[a-z]?)\s+(.+)$")


def load_checklist(path: Path) -> dict[str, str]:
    """Map every checklist item ID → its full text ('Title: description')."""
    items: dict[str, str] = {}
    for line in path.read_text().splitlines():
        m = _ITEM_RE.match(line.strip())
        if m:
            items[m.group(1)] = m.group(2).strip()
    return items


# ── Group definitions parsed from groups.md tables ────────────────────────────────────
# Every group section is a "### <NAME> — ..." heading followed by a GFM table whose first
# column is the item ID. We collect the IDs under each C*/D* heading.
_GROUP_HEAD_RE = re.compile(r"^###\s+([CD][123])\b")
_TABLE_ID_RE = re.compile(r"^\|\s*([0-9]+(?:\.[0-9]+)*[a-z]?)\s*\|")


def load_groups(path: Path) -> dict[str, list[str]]:
    """Map group name (C1..D3) → ordered list of its item IDs, from groups.md tables.

    Only rows under a `### C*/D* — ...` heading are collected; any other heading (`##` or
    a non-group `###`, e.g. the item-sharing matrix) ends the current group so its table
    isn't mistaken for group membership.
    """
    groups: dict[str, list[str]] = {}
    current: str | None = None
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            h = _GROUP_HEAD_RE.match(stripped)
            current = h.group(1) if h else None
            if current:
                groups.setdefault(current, [])
            continue
        if current:
            m = _TABLE_ID_RE.match(stripped)
            if m:
                iid = m.group(1)
                if iid not in groups[current]:
                    groups[current].append(iid)
    return {g: ids for g, ids in groups.items() if ids}


# ── Prompt assembly ───────────────────────────────────────────────────────────────────
_REPORT_BLOCK = """For each issue found, report:
- file — the file path
- lines — the line number(s)
- criterion — which checklist item applies (use the item ID, e.g. "17.6.2")
- severity — critical / high / medium / low / info
- confidence — 1-10 (how sure are you this is a real problem?)
- description — what's wrong and why it matters
- suggestion — how to fix it

Be skeptical. Only report issues you're confident about (confidence >= 7). Do not report \
style/formatting nits. Return an empty issues list if you find nothing."""


def diff_file_list(diff_text: str) -> list[str]:
    """New-file paths touched by the diff (for the preamble's file list)."""
    files: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            f = line[len("+++ b/") :].strip()
            if f and f != "/dev/null" and f not in files:
                files.append(f)
    return files


def build_prompt(
    checklist_ids: list[str],
    checklist_text: dict[str, str],
    diff_text: str,
    area: str,
) -> str:
    """Assemble one review prompt. The ONLY part that varies across conditions is the
    checklist subset; preamble scaffolding + diff are constant (confound control)."""
    files = diff_file_list(diff_text)
    file_lines = "\n".join(f"- {f}" for f in files)
    checklist_lines = []
    for iid in checklist_ids:
        text = checklist_text.get(iid, "(item text not found)")
        checklist_lines.append(f"- {iid} {text}")
    checklist_block = "\n".join(checklist_lines)

    return f"""You are reviewing a pull request in the cal.com codebase (area: {area}). \
The PR touches these files:
{file_lines}

Review ONLY the added/changed lines in the diff below against the checklist items listed. \
Do not flag issues that fall outside these specific checklist items.

## Checklist for this review
{checklist_block}

{_REPORT_BLOCK}

## Diff under review
```diff
{diff_text}```
"""


# ── Condition enumeration ─────────────────────────────────────────────────────────────
def planted_items(manifest: dict) -> list[str]:
    """Distinct planted item IDs across the case, in first-seen order."""
    seen: list[str] = []
    for p in manifest.get("planted", []):
        for iid in p.get("items", []):
            if iid not in seen:
                seen.append(iid)
    return seen


def enumerate_conditions(
    manifest: dict, groups: dict[str, list[str]]
) -> list[dict]:
    """Build the (solo + in-group) condition list for this case.

    Solo: one condition per distinct planted item ({i}).
    In-group: one per Phase-1 group whose items overlap the case's planted set — the
    group is run with its FULL membership (per §3), even items not planted here, because
    the grouping-as-context is what we test; the scorer credits only planted items.
    """
    items = planted_items(manifest)
    item_set = set(items)
    conditions: list[dict] = []

    for iid in items:
        conditions.append(
            {"condition": f"solo__{iid}", "kind": "solo", "checklist": [iid], "item": iid}
        )

    for gname, gids in sorted(groups.items()):
        if item_set & set(gids):
            conditions.append(
                {
                    "condition": f"group__{gname}",
                    "kind": "in-group",
                    "checklist": list(gids),
                    "group": gname,
                }
            )
    return conditions


# ── claude -p invocation (mirrors research_tool_capabilities.py) ──────────────────────
def _stream_event(ev: dict) -> None:
    """Echo a stream-json event compactly so the run is visible in the terminal."""
    t = ev.get("type")
    if t == "assistant":
        for block in ev.get("message", {}).get("content", []):
            if block.get("type") == "text" and block.get("text", "").strip():
                sys.stderr.write(block["text"].strip()[:400] + "\n")
    elif t == "result":
        sys.stderr.write(f"[result: {ev.get('subtype', 'ok')}]\n")


def invoke_claude(prompt: str, model: str) -> dict:
    """Run `claude -p` headless with the review output schema; return structured_output."""
    cmd = [
        "claude",
        "-p",
        prompt,
        "--model",
        model,
        "--output-format",
        "stream-json",
        "--verbose",
        "--json-schema",
        json.dumps(RESULT_SCHEMA),
        # No tools: the review is judged from the prompt's diff alone (no repo access,
        # no web). This keeps every run reviewing the identical fixed diff.
        "--disallowed-tools",
        "Bash",
        "Read",
        "Edit",
        "Write",
        "Glob",
        "Grep",
        "WebSearch",
        "WebFetch",
        "--permission-mode",
        "bypassPermissions",
        "--no-session-persistence",
    ]
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDECODE")}

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env
    )
    result_ev = None
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        _stream_event(ev)
        if ev.get("type") == "result":
            result_ev = ev
    err = proc.stderr.read()
    rc = proc.wait()

    if result_ev and result_ev.get("api_error_status") == 429:
        raise SessionLimitError((result_ev.get("result") or "429").strip())
    if rc != 0:
        detail = (err.strip() or json.dumps(result_ev or {}))[:1000]
        if "429" in detail or "session limit" in detail.lower():
            raise SessionLimitError(detail[:200])
        raise RuntimeError(f"claude exited {rc}: {detail or '(no output)'}")
    if result_ev is None:
        raise RuntimeError("no result event in stream")
    if result_ev.get("is_error"):
        raise RuntimeError(f"claude reported error: {result_ev.get('subtype')}")

    payload = result_ev.get("structured_output")
    if payload is None:
        raise RuntimeError(
            "result event had no `structured_output` — did --json-schema apply? "
            f"result keys: {sorted(result_ev.keys())}"
        )
    if isinstance(payload, str):
        payload = json.loads(payload)
    return payload


# ── Driver ────────────────────────────────────────────────────────────────────────────
def run_matrix(
    case_dir: Path,
    checklist_text: dict[str, str],
    groups: dict[str, list[str]],
    n: int,
    model: str,
    dry_run: bool,
    print_prompt: bool,
    out_dir: Path,
) -> None:
    manifest = json.loads((case_dir / "manifest.json").read_text())
    diff_text = (case_dir / "diff.patch").read_text()
    area = manifest.get("area", "")
    case_id = manifest.get("case_id", case_dir.name)

    conditions = enumerate_conditions(manifest, groups)
    runs_dir = out_dir / "runs"
    if not (dry_run or print_prompt):
        runs_dir.mkdir(parents=True, exist_ok=True)

    print(f"case {case_id}: {len(conditions)} conditions × N={n} = "
          f"{len(conditions) * n} runs")
    for c in conditions:
        print(f"  {c['condition']:20s} checklist={c['checklist']}")

    if dry_run:
        return

    for c in conditions:
        prompt = build_prompt(c["checklist"], checklist_text, diff_text, area)
        if print_prompt:
            print(f"\n===== {c['condition']} =====\n{prompt}")
            continue
        for k in range(1, n + 1):
            out_path = runs_dir / f"{c['condition']}__run{k}.json"
            if out_path.exists():
                print(f"  skip {out_path.name} (exists)")
                continue
            print(f"  run {c['condition']} #{k} …", flush=True)
            payload = invoke_claude(prompt, model)
            record = {
                "case_id": case_id,
                "condition": c["condition"],
                "kind": c["kind"],
                "checklist": c["checklist"],
                "run": k,
                "model": model,
                "issues": payload.get("issues", []),
            }
            if "item" in c:
                record["item"] = c["item"]
            if "group" in c:
                record["group"] = c["group"]
            out_path.write_text(json.dumps(record, indent=2) + "\n")
            print(f"    → {out_path.name} ({len(record['issues'])} issues)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case_dir", help="path to a built case dir (has manifest.json + diff.patch)")
    ap.add_argument("--checklist", type=Path, default=DEFAULT_CHECKLIST)
    ap.add_argument("--groups", type=Path, default=DEFAULT_GROUPS)
    ap.add_argument("-n", "--num-runs", type=int, default=DEFAULT_N)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--out", type=Path, default=None,
                    help="results dir (default: <case_dir>/results)")
    ap.add_argument("--dry-run", action="store_true",
                    help="list the conditions/run count; call no model")
    ap.add_argument("--print-prompt", action="store_true",
                    help="print each condition's assembled prompt; call no model")
    args = ap.parse_args()

    case_dir = Path(args.case_dir).resolve()
    if not (case_dir / "manifest.json").exists():
        ap.error(f"{case_dir} has no manifest.json — build the case first")

    # Nested `claude -p` gets killed inside an active Claude Code session (exit 137).
    if os.environ.get("CLAUDECODE") == "1" and not (args.dry_run or args.print_prompt):
        print(
            "refusing to run: CLAUDECODE=1 (inside a Claude Code session). Nested "
            "`claude -p` calls get killed. Run this from a plain terminal.\n"
            "(--dry-run / --print-prompt are safe here — they spawn no claude.)",
            file=sys.stderr,
        )
        return 2

    checklist_text = load_checklist(args.checklist)
    groups = load_groups(args.groups)
    out_dir = args.out or (case_dir / "results")

    try:
        run_matrix(
            case_dir, checklist_text, groups, args.num_runs, args.model,
            args.dry_run, args.print_prompt, out_dir,
        )
    except SessionLimitError as e:
        print(f"stopped on session/rate limit: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
