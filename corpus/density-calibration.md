# Density Calibration (stub)

Sets `lines_per_issue` — the sparse, realistic issue density a composed case targets
(`docs/corpus-spec.md` §3–4, `methodology.md` §4). **A knob, not a constant** — record the value used
and its basis.

## Calibrated target

```
lines_per_issue: 80
tolerance: 0.25
```

**Basis:** empirical survey of the cal.com CRB cases (below) gives a per-case **median of ~72** and
**mean of ~81** added-lines-per-golden-issue; the pooled ratio (total added / total issues) is **82**.
The pre-existing `80` default (`corpus-spec.md` §3) sits between the median and mean and inside the
observed spread, so it is **kept as-is** — now evidence-backed rather than arbitrary. Deliberately sparse
to avoid the "everything here is a bug" shortcut that destroys precision measurement.

## Calibration survey (computed 2026-07-21)

Surveyed the 10 cal.com **CRB cases** at
`~/code/eggai/qualops/evals/datasets/crb/crb-cal_dot_com-*` (real reviewer-flagged issues with golden
comments in each case's `slice.json`: `diff` + `expected[]`). Per case:
`added_diff_lines / len(expected)`, where added lines are unified-diff `+` lines excluding `+++` file
headers.

| Case | Added lines | Golden issues | Lines/issue |
| ---- | ----------- | ------------- | ----------- |
| 1    | 82          | 2             | 41.0        |
| 2    | 280         | 4             | 70.0        |
| 3    | 368         | 5             | 73.6        |
| 4    | 114         | 2             | 57.0        |
| 5    | 241         | 2             | 120.5       |
| 6    | 111         | 2             | 55.5        |
| 7    | 375         | 5             | 75.0        |
| 8    | 38          | 2             | 19.0        |
| 9    | 555         | 5             | 111.0       |
| 10   | 379         | 2             | 189.5       |

**Aggregates:** 10 cases, 2543 added lines, 31 golden issues. Per-case median **71.8**, mean **81.2**;
pooled **82.0**. Range 19–190 (real PRs vary widely — case 8 is dense, case 10 sparse).

> Status: **computed.** `lines_per_issue: 80` confirmed against the empirical distribution.

## Per-case padding budget (bank vs target)

The target sizes each **composed case**, not each area. A case tests one `(C,D)` pair, so it plants only
that pair's `C ∪ D` issues, then pads with `Kind: decoy`/`clean` commits **in the same `Area`** until
`total_added ≈ issues × 80` (±25% → 60–100 lines/issue). Computed from
[`bank.jsonl`](bank.jsonl) for the currently-planted **daily-webhook** area:

| Composed case        | Issues | Issue lines | Pad available (decoy+clean) | Max total | Lines/issue | In band? |
| -------------------- | ------ | ----------- | --------------------------- | --------- | ----------- | -------- |
| C1 (F1 only)         | 3      | 27          | 66                          | 93        | 31.0        | no       |
| C1 + co-located F4/D | 6      | 97          | 66                          | 163       | 27.2        | no       |

**Finding — padding shortfall.** The daily-webhook area has 3 decoys (39 lines) + 3 clean (27 lines) =
**66 pad lines**, but hitting 80 lines/issue for the 3-issue C1 case needs a total of ~240 (≈213 pad
lines), and ~480 for the 6-issue case. Even consuming all current padding tops out at ~31 lines/issue.

**Action for case composition (before running cases):** grow daily-webhook `Kind: clean`/`decoy` padding
by ≈**150–400 added lines** (several more realistic filler commits) so a case can reach the 60–100 band;
alternatively, lower `lines_per_issue` for Phase-1 cases and record the basis. The other planted areas
(`packages/lib/server`, `routing-forms`, `emails/src`) currently have **no** padding and will each need a
similar budget before their C2/C3 cases compose at density. This is a **case-builder input**, tracked in
`TODO.md` #3 → #4; it does not change the calibrated `lines_per_issue: 80` knob itself.
