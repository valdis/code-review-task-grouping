#!/usr/bin/env python3
"""Phase-1 scorer: LLM-judge semantic matching → per-item recall → reinforcement lift.

Consumes the raw runs produced by `scripts/run_matrix.py`
(`<case>/results/runs/<condition>__run<k>.json`) and computes the Phase-1 metric of
`docs/methodology.md` §1/§5/§6:

  * **Semantic matching** (§5) — each reported finding is matched to a planted issue by an
    **LLM-judge** that compares MEANING and ignores exact line numbers. This reuses the
    *pattern* (not the code) of qualops's `crb-pairwise` scorer
    (`docs/references.md`): a pairwise (golden, candidate) judge returns
    `{reasoning, match, confidence}`; per golden we keep the highest-confidence match.
  * **Multi-tag ground truth** (§5) — a planted issue carries one or more valid item IDs
    (`manifest.planted[].items`); a report is credited if the judge says it's the same
    underlying issue as that planted defect (any of its tags counts). The golden text a
    planted issue is matched against is built from ALL its checklist item texts + the
    commit subject, so a report phrased under any valid tag can match.
  * **Decoys → precision** (§5) — reported findings that match no planted issue are false
    positives; we additionally flag those that land on a planted DECOY / near-miss as
    "decoy-triggered" FPs, which is what makes precision meaningful.
  * **Per-condition metrics** — recall = matched planted / total planted; precision =
    valid reports / total reports; per-item detected/not.
  * **Cross-run frequencies + lift** (§1/§6) — over the N runs of each condition we take
    per-item detection frequency `recall(i|condition)`; then
    `lift_G(i) = recall(i | in-group G) − recall(i | solo {i})` and
    `lift(G) = mean_i lift_G(i)`, with run-to-run spread reported.

Like the run driver and `research_tool_capabilities.py`, the judge is `claude -p`
headless (stream-json, `structured_output`); it MUST run from a plain terminal (refuses
when CLAUDECODE=1) unless --dry-run.

Outputs (written under `<case>/results/`):
  * `scored/<condition>__run<k>.json` — per-run match detail (which planted issues hit,
    which reports were FPs, decoy hits).
  * `summary.json` — per-condition recall/precision + per-item detection frequency, and
    the per-item / per-group lift table with spread.
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
DEFAULT_MODEL = "sonnet"

# Pairwise judge output schema.
JUDGE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["reasoning", "match", "confidence"],
    "properties": {
        "reasoning": {"type": "string"},
        "match": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
}


class SessionLimitError(RuntimeError):
    pass


# ── Checklist item text (shared with run_matrix parsing) ──────────────────────────────
_ITEM_RE = re.compile(r"^- ([0-9]+(?:\.[0-9]+)*[a-z]?)\s+(.+)$")


def load_checklist(path: Path) -> dict[str, str]:
    items: dict[str, str] = {}
    for line in path.read_text().splitlines():
        m = _ITEM_RE.match(line.strip())
        if m:
            items[m.group(1)] = m.group(2).strip()
    return items


# ── Golden construction from the manifest ─────────────────────────────────────────────
def build_goldens(manifest: dict, checklist_text: dict[str, str]) -> list[dict]:
    """One golden per planted issue. Golden text = all its checklist item texts + subject
    + file/line context, so a report phrased under ANY valid tag can match it (multi-tag).
    """
    goldens: list[dict] = []
    for idx, p in enumerate(manifest.get("planted", [])):
        items = p.get("items", [])
        item_lines = "; ".join(f"{i}: {checklist_text.get(i, '')}" for i in items)
        files = ", ".join(p.get("files", []))
        lines = p.get("lines", [])
        loc = f"{files} lines {lines}" if lines else files
        text = (
            f"A code smell of type(s) [{', '.join(items)}] planted in {loc}. "
            f"Intent: {p.get('subject', '')}. "
            f"Matching checklist items — {item_lines}"
        )
        goldens.append(
            {
                "golden_index": idx,
                "items": items,
                "files": p.get("files", []),
                "subject": p.get("subject", ""),
                "text": text,
            }
        )
    return goldens


def build_decoys(manifest: dict) -> list[dict]:
    """Decoy near-misses, for flagging decoy-triggered false positives."""
    return [
        {
            "near_miss_of": d.get("near_miss_of"),
            "files": d.get("files", []),
            "lines": d.get("lines", []),
        }
        for d in manifest.get("decoys", [])
    ]


# ── candidate (reported issue) text ───────────────────────────────────────────────────
def candidate_text(issue: dict) -> str:
    return (
        f"[{issue.get('criterion', '?')}] {issue.get('file', '')}:"
        f"{issue.get('lines', '')} — {issue.get('description', '')} "
        f"(fix: {issue.get('suggestion', '')})"
    )


# ── LLM judge (claude -p headless) ────────────────────────────────────────────────────
def build_judge_prompt(golden: str, candidate: str) -> str:
    return f"""You are evaluating an AI code-review tool. Decide whether the CANDIDATE \
finding identifies the SAME underlying issue as the GOLDEN (planted) defect.

Golden defect (what we planted and are looking for):
{golden}

Candidate finding (from the tool's review):
{candidate}

Instructions:
- Say match=true only if the candidate points to the SAME underlying bug/smell in the \
same code — semantic match, different wording is fine.
- Ignore exact line numbers; ignore which checklist item ID the candidate cites (a valid \
finding may cite a different-but-related item).
- A finding about a DIFFERENT concern in nearby code is NOT a match.
Respond with the JSON object {{reasoning, match, confidence(0..1)}}."""


def invoke_judge(prompt: str, model: str) -> dict:
    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--output-format", "stream-json",
        "--verbose",
        "--json-schema", json.dumps(JUDGE_SCHEMA),
        "--disallowed-tools", "Bash", "Read", "Edit", "Write", "Glob", "Grep",
        "WebSearch", "WebFetch",
        "--permission-mode", "bypassPermissions",
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
        if ev.get("type") == "result":
            result_ev = ev
    err = proc.stderr.read()
    rc = proc.wait()
    if result_ev and result_ev.get("api_error_status") == 429:
        raise SessionLimitError((result_ev.get("result") or "429").strip())
    if rc != 0:
        detail = (err.strip() or json.dumps(result_ev or {}))[:500]
        if "429" in detail or "session limit" in detail.lower():
            raise SessionLimitError(detail[:200])
        raise RuntimeError(f"claude exited {rc}: {detail}")
    if result_ev is None:
        raise RuntimeError("no result event in stream")
    payload = result_ev.get("structured_output")
    if payload is None:
        raise RuntimeError("judge result had no structured_output")
    if isinstance(payload, str):
        payload = json.loads(payload)
    return payload


# ── Score one run ─────────────────────────────────────────────────────────────────────
def score_run(
    run: dict,
    goldens: list[dict],
    decoys: list[dict],
    checklist_only: set[str],
    model: str,
    judge,
) -> dict:
    """Match a run's reported issues against the goldens. Only goldens whose item set
    intersects the condition's checklist are 'in scope' — a solo {i} condition can only be
    expected to find planted issues tagged i. Out-of-scope goldens are excluded from that
    condition's recall denominator (you didn't ask the model to look for them).
    """
    issues = run.get("issues", [])
    candidates = [candidate_text(i) for i in issues]

    in_scope = [g for g in goldens if set(g["items"]) & checklist_only]
    matched = {g["golden_index"]: {"matched": False, "cand": None, "conf": 0.0} for g in in_scope}
    matched_cand_idx: set[int] = set()

    for g in in_scope:
        for ci, cand in enumerate(candidates):
            res = judge(build_judge_prompt(g["text"], cand), model)
            if res.get("match") and res.get("confidence", 0) > matched[g["golden_index"]]["conf"]:
                matched[g["golden_index"]] = {
                    "matched": True, "cand": ci, "conf": res.get("confidence", 0),
                }
        if matched[g["golden_index"]]["matched"]:
            matched_cand_idx.add(matched[g["golden_index"]]["cand"])

    tp = sum(1 for v in matched.values() if v["matched"])
    fn = len(in_scope) - tp
    fp_idx = [ci for ci in range(len(candidates)) if ci not in matched_cand_idx]

    # Flag FPs that land on a planted decoy's file (decoy-triggered false positives).
    decoy_files = {f for d in decoys for f in d["files"]}
    decoy_hits = [
        ci for ci in fp_idx if issues[ci].get("file") in decoy_files
    ]

    precision = tp / (tp + len(fp_idx)) if (tp + len(fp_idx)) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    return {
        "case_id": run.get("case_id"),
        "condition": run.get("condition"),
        "kind": run.get("kind"),
        "run": run.get("run"),
        "in_scope_goldens": [g["golden_index"] for g in in_scope],
        "per_item_detected": {
            iid: any(
                matched[g["golden_index"]]["matched"]
                for g in in_scope
                if iid in g["items"]
            )
            for iid in checklist_only
            if any(iid in g["items"] for g in in_scope)
        },
        "tp": tp,
        "fn": fn,
        "fp": len(fp_idx),
        "decoy_triggered_fp": len(decoy_hits),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
    }


# ── Aggregate across runs → lift ──────────────────────────────────────────────────────
def aggregate(scored: list[dict]) -> dict:
    """Per-condition mean recall/precision + per-item detection frequency; then per-item
    and per-group reinforcement lift = in-group recall − solo recall."""
    by_condition: dict[str, list[dict]] = {}
    for s in scored:
        by_condition.setdefault(s["condition"], []).append(s)

    cond_summary: dict[str, dict] = {}
    # per-item solo recall frequency (detection rate over that item's solo runs)
    solo_item_freq: dict[str, float] = {}
    for cond, runs in by_condition.items():
        n = len(runs)
        mean_recall = sum(r["recall"] for r in runs) / n
        mean_prec = sum(r["precision"] for r in runs) / n
        # per-item frequency across the runs of this condition
        item_freq: dict[str, float] = {}
        all_items = {i for r in runs for i in r["per_item_detected"]}
        for iid in all_items:
            hits = sum(1 for r in runs if r["per_item_detected"].get(iid))
            item_freq[iid] = round(hits / n, 3)
        cond_summary[cond] = {
            "kind": runs[0]["kind"],
            "n": n,
            "mean_recall": round(mean_recall, 3),
            "mean_precision": round(mean_prec, 3),
            "decoy_triggered_fp_total": sum(r["decoy_triggered_fp"] for r in runs),
            "item_frequency": item_freq,
        }
        if runs[0]["kind"] == "solo" and cond.startswith("solo__"):
            iid = cond[len("solo__"):]
            solo_item_freq[iid] = item_freq.get(iid, 0.0)

    # per-item lift within each in-group condition
    lift_by_group: dict[str, dict] = {}
    for cond, summ in cond_summary.items():
        if summ["kind"] != "in-group":
            continue
        gname = cond[len("group__"):] if cond.startswith("group__") else cond
        per_item: dict[str, dict] = {}
        for iid, in_freq in summ["item_frequency"].items():
            solo = solo_item_freq.get(iid)
            if solo is None:
                continue  # no solo baseline for this item in this case → skip
            per_item[iid] = {
                "recall_in_group": in_freq,
                "recall_solo": solo,
                "lift": round(in_freq - solo, 3),
            }
        lifts = [v["lift"] for v in per_item.values()]
        lift_by_group[gname] = {
            "condition": cond,
            "per_item": per_item,
            "group_lift": round(sum(lifts) / len(lifts), 3) if lifts else None,
        }

    return {
        "conditions": cond_summary,
        "solo_item_frequency": solo_item_freq,
        "lift_by_group": lift_by_group,
    }


# ── Driver ────────────────────────────────────────────────────────────────────────────
def group_checklist(run: dict) -> set[str]:
    return set(run.get("checklist", []))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case_dir", help="built + run case dir (has manifest.json + results/runs/)")
    ap.add_argument("--checklist", type=Path, default=DEFAULT_CHECKLIST)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be judged; call no model")
    args = ap.parse_args()

    case_dir = Path(args.case_dir).resolve()
    manifest = json.loads((case_dir / "manifest.json").read_text())
    runs_dir = case_dir / "results" / "runs"
    if not runs_dir.exists():
        ap.error(f"no runs at {runs_dir} — run scripts/run_matrix.py first")

    checklist_text = load_checklist(args.checklist)
    goldens = build_goldens(manifest, checklist_text)
    decoys = build_decoys(manifest)

    run_files = sorted(runs_dir.glob("*.json"))
    total_pairs = 0
    for rf in run_files:
        run = json.loads(rf.read_text())
        scope = {g["golden_index"] for g in goldens if set(g["items"]) & group_checklist(run)}
        total_pairs += len(scope) * len(run.get("issues", []))
    print(f"{len(run_files)} runs; ~{total_pairs} judge pairs")

    if args.dry_run:
        return 0

    if os.environ.get("CLAUDECODE") == "1":
        print("refusing: CLAUDECODE=1 — run the judge from a plain terminal.",
              file=sys.stderr)
        return 2

    scored_dir = case_dir / "results" / "scored"
    scored_dir.mkdir(parents=True, exist_ok=True)
    scored: list[dict] = []
    try:
        for rf in run_files:
            run = json.loads(rf.read_text())
            out = scored_dir / rf.name
            if out.exists():
                scored.append(json.loads(out.read_text()))
                continue
            s = score_run(
                run, goldens, decoys, group_checklist(run), args.model, invoke_judge
            )
            out.write_text(json.dumps(s, indent=2) + "\n")
            scored.append(s)
            print(f"  {rf.name}: recall={s['recall']} precision={s['precision']} "
                  f"decoyFP={s['decoy_triggered_fp']}")
    except SessionLimitError as e:
        print(f"stopped on session/rate limit: {e}", file=sys.stderr)
        return 3

    summary = aggregate(scored)
    (case_dir / "results" / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print("\nlift by group:")
    for g, v in summary["lift_by_group"].items():
        print(f"  {g}: group_lift={v['group_lift']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
