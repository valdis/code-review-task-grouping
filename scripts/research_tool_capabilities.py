#!/usr/bin/env python3
"""Research, per tool, which checklist items that tool can detect — via Claude Code.

For each of the 24 tools we invoke `claude -p` once (batched-by-tool). The model is
given the tool's official rule-list/doc URL plus the list of items still marked `idk`
for that tool, told to web-search the docs, and asked to return a structured verdict
per item: complete / partial / none / na — each backed by a source URL. The child's
research dialogue (thinking / web searches / results) is streamed live to the terminal
for visibility, but the value consumed by the script is still the final JSON blob.

Results are APPENDED to a durable intermediary log (data/tool-capability-research.jsonl),
one JSON row per item×tool verdict (with rationale + raw source). The matrix JSON is NOT
touched by the research run — that keeps the raw evidence reviewable before anything is
curated in. A separate `--merge` step folds the (reviewed) log into the matrix's
`coverage` cells + `sources`. The run is resumable: cells already present in the log are
skipped on rerun.

Workflow:
  1. research:  research_tool_capabilities.py [--tool ID]... [--limit-items N] ...
                → appends verdicts to the JSONL log (matrix untouched)
  2. review:    eyeball data/tool-capability-research.jsonl
  3. merge:     research_tool_capabilities.py --merge
                → applies logged verdicts to the matrix JSON
  4. regenerate: scripts/issue_detection_tool_capabilities_matrix_report.py

Per tool the driver loops over SMALL BATCHES (default 8 items/call) until that tool has
no pending items left, appending to the log after every batch — so a mid-tool crash
keeps prior batches and reruns resume cheaply.

Defaults: all tools, all idk items, batch size 8, no budget cap, model "sonnet".
Requires the `claude` CLI on PATH (headless -p). Needs web access for the search.

IMPORTANT: run this from a PLAIN terminal, NOT from inside a Claude Code session.
Nested `claude` sessions share runtime resources and get killed by the guard, so the
research (`claude -p`) sub-invocations only work standalone. `--merge`, `--dry-run` and
`--print-prompt` are safe to run anywhere (they don't spawn `claude`).
"""
import argparse
import json
import os
import subprocess
import sys


class SessionLimitError(RuntimeError):
    """Raised on a 429 session/rate limit — every further call fails until reset, so
    the whole run should stop rather than churn through the remaining tools."""


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data", "issue-detection-tool-capabilities-matrix.json")
LOG = os.path.join(ROOT, "data", "tool-capability-research.jsonl")

VALID_VERDICTS = {"complete", "partial", "none", "na", "idk"}

# JSON schema the model must satisfy (structured-output validation).
RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "verdict": {
                        "type": "string",
                        "enum": ["complete", "partial", "none", "na", "idk"],
                    },
                    "source_url": {"type": "string"},
                    "source_label": {"type": "string"},
                    "rationale": {"type": "string"},
                },
                "required": ["id", "verdict", "rationale"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


def load_data() -> dict:
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def save_data(data: dict) -> None:
    """Atomic write so an interrupted run never corrupts the matrix."""
    tmp = DATA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA)


def load_log() -> list[dict]:
    """Read the intermediary research log (JSONL); empty if it doesn't exist."""
    if not os.path.exists(LOG):
        return []
    rows = []
    with open(LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def logged_cells() -> set[tuple[str, str]]:
    """(tool_id, item_id) pairs already captured in the log — for resumability."""
    return {(r["tool"], r["id"]) for r in load_log()}


def append_log(rows: list[dict]) -> None:
    """Append verdict rows to the JSONL log (create on first write)."""
    with open(LOG, "a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_prompt(tool_id: str, tool: dict, scale: dict, items: list[dict]) -> str:
    """Construct the individualized prompt for one tool over its pending items."""
    lines = []
    for it in items:
        inj = it.get("injectable", "?")
        fam = it.get("section") or it.get("family", "")
        lines.append(f'- {it["id"]} | {it["name"]} | injectable={inj} | area={fam}')
    item_block = "\n".join(lines)

    scale_block = "\n".join(
        f'  - "{c}" = {scale[c]}' for c in ("complete", "partial", "none", "na")
    )

    return f"""You are auditing the static-analysis tool **{tool['name']}** (id `{tool_id}`,
language: {tool['lang']}). Its official rule-list / capabilities entry point is:

  {tool.get('doc_url', '(no doc url on record — search for the official rule list)')}

GOAL: For EACH checklist item below, determine whether {tool['name']} — out of the box,
with its standard/recommended rule set or a widely-used bundled rule — can detect that
CLASS of issue. Use WebSearch / WebFetch to read the tool's actual documented rules. Do
not guess from the tool's reputation; ground every verdict in a documented rule or an
explicit absence.

VERDICT SCALE (pick exactly one per item):
{scale_block}

Guidance:
- "complete": a documented rule directly and reliably flags this class of issue.
- "partial": a rule covers some but not all cases, or only with non-default config, or
  catches a closely-related subset.
- "na": the issue's underlying construct does not exist in {tool['lang']} (e.g. a
  pointer-nil issue in a language without pointers), so the tool *cannot* apply.
- "none": the construct exists in this language but the tool has no rule for it.
- Use "idk" ONLY if you genuinely cannot find evidence either way after searching.

EVIDENCE: For every "complete"/"partial" verdict you MUST provide a `source_url`
pointing to the specific rule's documentation page (and a short `source_label`, e.g. the
rule id/name). For "na"/"none" a source is optional. Always give a one-line `rationale`.

Return ONLY structured JSON matching the provided schema: an object with a `results`
array, one entry per item id below. Do not omit any item.

ITEMS TO JUDGE ({len(items)}):
{item_block}
"""


def _stream_event(ev: dict) -> None:
    """Pretty-print one stream-json event so the research 'inner dialogue' is visible."""
    et = ev.get("type")
    if et in ("assistant", "user"):
        for block in ev.get("message", {}).get("content", []):
            bt = block.get("type")
            if bt == "text" and block.get("text", "").strip():
                print(f"    💭 {block['text'].strip()}", flush=True)
            elif bt == "thinking" and block.get("thinking", "").strip():
                print(f"    🧠 {block['thinking'].strip()}", flush=True)
            elif bt == "tool_use":
                q = block.get("input", {})
                arg = q.get("query") or q.get("url") or ""
                print(f"    🔎 {block.get('name')}: {arg}", flush=True)
            elif bt == "tool_result":
                content = block.get("content", "")
                if isinstance(content, list):
                    content = " ".join(
                        c.get("text", "") for c in content if isinstance(c, dict)
                    )
                snippet = str(content).strip().replace("\n", " ")[:160]
                if snippet:
                    print(f"    📄 {snippet}…", flush=True)
    elif et == "result":
        cost = ev.get("total_cost_usd")
        turns = ev.get("num_turns")
        extra = f" ({turns} turns, ~${cost:.2f} list-price)" if cost is not None else ""
        print(f"    ✅ done{extra}", flush=True)


def invoke_claude(prompt: str, model: str, budget: float | None) -> dict:
    """Run `claude -p` headless, STREAMING its research dialogue to the terminal.

    Uses --output-format stream-json (one JSON object per line): assistant/user
    messages carry text + tool_use/tool_result blocks that we echo live; the final
    `result` event's `structured_output` field holds the schema-validated payload.
    """
    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--output-format", "stream-json",
        "--verbose",  # required for stream-json to emit per-message events
        "--json-schema", json.dumps(RESULT_SCHEMA),
        # WebSearch + WebFetch only. WebFetch converts HTML→markdown, so the model reads
        # clean text instead of raw HTML. Bash is explicitly disallowed so the model
        # can't `curl` pages and dump raw markup into context.
        "--allowed-tools", "WebSearch", "WebFetch",
        "--disallowed-tools", "Bash", "Read", "Edit", "Write", "Glob", "Grep",
        # Headless `-p` cannot answer an interactive permission prompt, so a tool
        # approval under "default" mode silently fails the run. Bypass is safe here:
        # the disallow-list blocks everything except the two read-only web tools.
        "--permission-mode", "bypassPermissions",
        "--no-session-persistence",
    ]
    # --max-budget-usd caps on the API *list-price estimate*, which is irrelevant on a
    # subscription plan (no per-call billing) and there just kills long research runs.
    # Off by default; opt in only for the pay-per-token API.
    if budget is not None:
        cmd += ["--max-budget-usd", str(budget)]
    # Strip the nested-session guard so a `claude` child can launch when this driver
    # is itself run from within a Claude Code session.
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
            continue  # non-JSON noise; ignore
        _stream_event(ev)
        if ev.get("type") == "result":
            result_ev = ev
    err = proc.stderr.read()
    rc = proc.wait()
    # A 429 (session/rate limit) surfaces as an error result event with a nonzero rc.
    # Detect it first and raise the dedicated type so the caller stops the whole run.
    if result_ev and result_ev.get("api_error_status") == 429:
        msg = (result_ev.get("result") or "session/rate limit (429)").strip()
        raise SessionLimitError(msg)
    if rc != 0:
        detail = (err.strip() or json.dumps(result_ev or {}))[:1000]
        # Some limit messages arrive without api_error_status but with a 429 marker.
        if "429" in detail or "session limit" in detail.lower():
            raise SessionLimitError(detail[:200])
        raise RuntimeError(f"claude exited {rc}: {detail or '(no output)'}")
    if result_ev is None:
        raise RuntimeError("no result event in stream")
    if result_ev.get("is_error"):
        raise RuntimeError(f"claude reported error: {result_ev.get('subtype')}")

    # Per the headless docs, when --json-schema is set the schema-validated payload is
    # in the result event's `structured_output` field (an object). The `result` field
    # holds the natural-language text, NOT the JSON — reading it fails to parse.
    payload = result_ev.get("structured_output")
    if payload is None:
        raise RuntimeError(
            "result event had no `structured_output` — did --json-schema apply? "
            f"result keys: {sorted(result_ev.keys())}"
        )
    if isinstance(payload, str):
        payload = json.loads(payload)
    return payload


def source_key(tool_id: str, item_id: str) -> str:
    return f"{tool_id}-{item_id}".replace(".", "_").lower()


def results_to_rows(tool_id: str, valid_ids: set[str], results: list[dict]) -> list[dict]:
    """Normalize one tool's model output into log rows (one per valid item)."""
    rows = []
    for r in results:
        iid = r.get("id")
        verdict = r.get("verdict")
        if iid not in valid_ids or verdict not in VALID_VERDICTS:
            continue
        rows.append({
            "tool": tool_id,
            "id": iid,
            "verdict": verdict,
            "source_url": (r.get("source_url") or "").strip(),
            "source_label": (r.get("source_label") or "").strip(),
            "rationale": (r.get("rationale") or "").strip(),
        })
    return rows


def merge_log_into_matrix(data: dict) -> int:
    """Fold the reviewed JSONL log into the matrix coverage + sources.

    Last-writer-wins per (tool, item); only overwrites `idk`/unset cells. Returns
    number of cells updated. Caller persists via save_data().
    """
    by_id = {it["id"]: it for it in data["items"]}
    sources = data.setdefault("sources", {})
    updated = 0
    for r in load_log():
        tool_id, iid, verdict = r["tool"], r["id"], r["verdict"]
        if iid not in by_id or verdict == "idk":
            continue
        item = by_id[iid]
        cov = item.setdefault("coverage", {})
        if cov.get(tool_id) not in (None, "idk"):
            continue  # already determined in the matrix — don't clobber
        cov[tool_id] = verdict
        updated += 1
        url = (r.get("source_url") or "").strip()
        if verdict in ("complete", "partial") and url:
            key = source_key(tool_id, iid)
            sources[key] = {"label": r.get("source_label") or key, "url": url}
            item.setdefault("note_sources", [])
            if key not in item["note_sources"]:
                item["note_sources"].append(key)
        if item.get("research_status") == "unresearched" and all(
            v != "idk" for v in cov.values()
        ):
            item["research_status"] = "researched"
    return updated


def pending_items(data: dict, tool_id: str, done: set, limit: int | None) -> list[dict]:
    """Items still `idk` for this tool AND not already in the research log."""
    out = []
    for it in data["items"]:
        if it.get("coverage", {}).get(tool_id) != "idk":
            continue
        if (tool_id, it["id"]) in done:
            continue
        out.append(it)
    return out[:limit] if limit else out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", action="append", dest="tools",
                    help="restrict to these tool id(s); repeatable")
    ap.add_argument("--limit-items", type=int, default=None,
                    help="cap items per tool (for a cheap trial run)")
    ap.add_argument("--budget-usd", type=float, default=None,
                    help="optional per-tool spend cap on the API list-price ESTIMATE. "
                         "Off by default — irrelevant on a subscription plan and it "
                         "only kills long research runs. Set only for the paid API.")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--dry-run", action="store_true",
                    help="don't call claude; just report what would run")
    ap.add_argument("--print-prompt", action="store_true",
                    help="print the built prompt for the first selected tool and exit")
    ap.add_argument("--batch-size", type=int, default=8,
                    help="items per claude call; the driver loops over batches until "
                         "each tool is exhausted (default 8, smaller = more robust)")
    ap.add_argument("--max-batches", type=int, default=None,
                    help="cap the number of batches per tool (for a bounded trial)")
    ap.add_argument("--merge", action="store_true",
                    help="fold the reviewed JSONL log into the matrix and exit "
                         "(no research; no claude calls)")
    args = ap.parse_args()

    data = load_data()
    scale = {s["code"]: s["meaning"] for s in data["scale"]}
    tool_ids = args.tools or list(data["tools"].keys())

    if args.merge:
        n = merge_log_into_matrix(data)
        save_data(data)
        print(f"merged {n} cell(s) from {LOG} into the matrix")
        return 0

    # Nested `claude -p` calls get killed inside an active Claude Code session.
    if os.environ.get("CLAUDECODE") == "1" and not (args.dry_run or args.print_prompt):
        print("!! Refusing to run: you're inside a Claude Code session — nested "
              "`claude -p` calls get killed.\n"
              "   Run this from a plain terminal. (--merge/--dry-run/--print-prompt "
              "are fine here.)", file=sys.stderr)
        return 2

    if args.print_prompt:
        tid = tool_ids[0]
        items = pending_items(data, tid, logged_cells(), args.batch_size)
        print(build_prompt(tid, data["tools"][tid], scale, items))
        return 0

    grand = 0
    limit_hit = None
    for tid in tool_ids:
        if limit_hit:
            break
        if tid not in data["tools"]:
            print(f"!! unknown tool: {tid}", file=sys.stderr)
            continue
        # Total still-pending for this tool (for a progress readout).
        remaining = len(pending_items(data, tid, logged_cells(), None))
        if remaining == 0:
            print(f"[{tid}] nothing pending — skip")
            continue
        print(f"[{tid}] {remaining} item(s) pending; "
              f"batching {args.batch_size} at a time…")
        if args.dry_run:
            continue

        batch_no = 0
        prev_pending = None
        while True:
            if args.max_batches is not None and batch_no >= args.max_batches:
                print(f"[{tid}] hit --max-batches={args.max_batches}; stopping tool")
                break
            # Re-read the log each batch so already-logged items are skipped — this is
            # what makes the loop resumable and non-repeating across runs.
            done_now = logged_cells()
            batch = pending_items(data, tid, done_now, args.batch_size)
            if not batch:
                print(f"[{tid}] exhausted — no items left")
                break
            cur_pending = len(pending_items(data, tid, done_now, None))
            # Progress guard: if a batch didn't reduce the pending count, the model is
            # persistently skipping items — bail rather than loop forever on them.
            if prev_pending is not None and cur_pending >= prev_pending:
                print(f"[{tid}] no progress (still {cur_pending} pending); "
                      "aborting tool", file=sys.stderr)
                break
            prev_pending = cur_pending
            batch_no += 1
            ids = ", ".join(it["id"] for it in batch)
            print(f"[{tid}] batch {batch_no} ({len(batch)} items: {ids})")
            prompt = build_prompt(tid, data["tools"][tid], scale, batch)
            valid_ids = {it["id"] for it in batch}
            try:
                payload = invoke_claude(prompt, args.model, args.budget_usd)
            except SessionLimitError as e:
                # 429: every further call fails until reset — stop the entire run.
                limit_hit = str(e)
                print(f"\n!! SESSION LIMIT: {limit_hit}\n"
                      f"   Stopping. Already-logged verdicts are saved; rerun after "
                      f"the reset to resume where this left off.", file=sys.stderr)
                break
            except Exception as e:  # noqa: BLE001 — log and move on to next batch/tool
                print(f"[{tid}] batch {batch_no} FAILED: {e}", file=sys.stderr)
                # Don't spin forever on a persistently failing batch.
                print(f"[{tid}] aborting this tool after batch failure", file=sys.stderr)
                break
            rows = results_to_rows(tid, valid_ids, payload.get("results", []))
            if not rows:
                print(f"[{tid}] batch {batch_no} returned no usable verdicts; "
                      "aborting tool to avoid a loop", file=sys.stderr)
                break
            append_log(rows)  # persist immediately — crash-safe, resumable
            grand += len(rows)
            print(f"[{tid}] batch {batch_no}: logged {len(rows)} verdict(s)")

    print(f"done — {grand} verdict(s) appended to:\n  {LOG}")
    print("review that log, then run with --merge to apply verdicts to the matrix")
    return 0


if __name__ == "__main__":
    sys.exit(main())
